"""SolarFlareUTAC — Diamond interface (GenesisAeon Package 21).

Implements the full Diamond-template contract:
  run_cycle()       simulate a UTAC cycle and return state dict
  get_crep_state()  {C, R, E, P, Gamma}
  get_utac_state()  {H, dH_dt, H_star, K_eff}
  get_phase_events() list of flare phase-transition events
  to_zenodo_record() Zenodo-compatible metadata dict

Physics
-------
H(t)  — normalised magnetic free energy of the active region ∈ [0, 1]
K     — normalisation ceiling E_max (active region maximum energy)
H*    — two fixed points: H*_quiet ≈ 0.1 and eruption threshold ≈ 0.6
r     — flux-emergence buildup rate ≈ 0.06 hr⁻¹
σ     — CREP coupling = 2.2
Γ(t)  — CREP tensor (C, R, E, P) → Γ_solar ≈ 0.014 (Package 21 result)

Ethics Gate Light (Phase H) is applied inside run_cycle().
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np

from .active_region import MagneticActiveRegion
from .constants import (
    E_MAX_J,
    ETHICS_H_MAX,
    ETHICS_TENSION_MAX,
    GAMMA_SOLAR,
    H_STAR_QUIET,
    H_THRESHOLD,
    PACKAGE_REGISTRY_ENTRY,
    R_BUILDUP,
    SEED,
    SIGMA_CREP,
    SOLAR_CYCLE_YEARS,
    SOLAR_TARGETS,
)
from .crep_solar import CREPState, SolarCREP
from .geomagnetic import GeomagneticStorm
from .goes_loader import GOESLoader
from .reconnection import ReconnectionThreshold
from .superflare import SuperflareStatistics

# ── genesis-os stubs ───────────────────────────────────────────────────────────
try:
    from genesis.core.utac import UTAC_ODE, UTACParams  # type: ignore[import-not-found]
    from genesis.core.crep import CREPTensor  # type: ignore[import-not-found]
    from genesis.mirror.phase_loop import PhaseTransitionLoop  # type: ignore[import-not-found]
    from genesis.core.lagrangian import UnifiedLagrangian  # type: ignore[import-not-found]
    _GENESIS_AVAILABLE = True
except ImportError:
    _GENESIS_AVAILABLE = False


# ── Ethics Gate ────────────────────────────────────────────────────────────────

class _EthicsGate:
    """Lightweight gate that blocks UTAC transitions above safety thresholds."""

    def check(self, state: dict, tension: float) -> dict:
        if tension > ETHICS_TENSION_MAX:
            return {
                "allowed": False,
                "reason": f"tension={tension:.4f} exceeds max={ETHICS_TENSION_MAX}",
            }
        H = float(state.get("H", 0.0))
        if H > ETHICS_H_MAX:
            return {
                "allowed": False,
                "reason": f"H={H:.4f} exceeds safe threshold={ETHICS_H_MAX}",
            }
        return {"allowed": True, "reason": "ok"}


# ── SolarFlareUTAC ─────────────────────────────────────────────────────────────

class SolarFlareUTAC:
    """GenesisAeon Package 21 — Solar flare magnetic avalanche threshold.

    Central result: Γ_solar = arctanh(0.03) / 2.2 ≈ 0.014.
    Solar active regions occupy the ultra-sensitive end of the CREP spectrum.

    Parameters
    ----------
    seed : int
        Master random seed (default 42).
    active_region_id : str
        Identifier for the simulated active region (e.g. 'AR3000').
    """

    def __init__(
        self,
        seed: int = SEED,
        active_region_id: str = "AR_synthetic",
    ) -> None:
        self.seed = seed
        self.active_region_id = active_region_id

        self._ar = MagneticActiveRegion(r_buildup=R_BUILDUP, seed=seed)
        self._crep = SolarCREP(sigma=SIGMA_CREP, seed=seed)
        self._reconnect = ReconnectionThreshold(
            h_threshold=H_THRESHOLD, theta_pt=GAMMA_SOLAR
        )
        self._goes = GOESLoader(seed=seed)
        self._superflare = SuperflareStatistics(seed=seed)
        self._geomagnetic = GeomagneticStorm(seed=seed)
        self._ethics_gate = _EthicsGate()

        # Optional tension metric — set externally to enable Ethics Gate
        self._tension_metric = None

        self._phase_events: list[dict] = []
        self._last_crep: CREPState = self._crep.nominal()
        self._last_utac: dict = self._build_utac_dict()
        self._cycle_count: int = 0
        self._goes_flux: np.ndarray | None = None

    # ── Diamond interface ──────────────────────────────────────────────────────

    def run_cycle(self, duration_hours: float = 72.0) -> dict:
        """Simulate one UTAC cycle of duration_hours.

        Each flare event during the cycle is recorded as a PhaseTransitionEvent.

        Returns
        -------
        dict with keys:
          utac_state, crep_state, phase_events, flare_count,
          gamma_solar, benchmark_targets, genesis_available.
        """
        dt_hours = 0.1
        n_steps = int(duration_hours / dt_hours)

        # Pre-generate synthetic GOES flux for P component
        times_flux, flux = self._goes.generate_synthetic(
            n_years=1, cadence_hours=dt_hours
        )
        self._goes_flux = flux
        window_size = 200

        cycle_phase_0 = (self._cycle_count % int(SOLAR_CYCLE_YEARS * 8760 / dt_hours)) * dt_hours
        new_events: list[dict] = []

        for i in range(n_steps):
            t = i * dt_hours
            H = self._ar.H

            # Solar cycle phase
            cycle_phase = 2.0 * math.pi * (cycle_phase_0 + t) / (SOLAR_CYCLE_YEARS * 8760)

            # CREP tensor update
            flux_window = flux[max(0, i - window_size) : i + 1] if i > 0 else flux[:1]
            dH_approx = self._ar.r_buildup * (1.0 - H) - self._reconnect.reconnection_rate(H, self._last_crep.Gamma) * H
            self._last_crep = self._crep.compute(
                H=H,
                dH_dt=dH_approx,
                flux_series=flux_window,
                solar_cycle_phase=cycle_phase,
            )

            # Reconnection rate
            lam = self._reconnect.reconnection_rate(H, self._last_crep.Gamma)

            # Advance active region
            result = self._ar.step(dt_hours=dt_hours, lambda_reconnect=lam)

            # Record flare phase event
            if result["flare_triggered"]:
                evt = {
                    "type": "solar_flare",
                    "time_h": t,
                    "H_pre": H,
                    "energy_J": result["energy_released_J"],
                    "crep_Gamma": self._last_crep.Gamma,
                    "reconnection_rate": lam,
                }
                new_events.append(evt)
                self._phase_events.append(evt)

                # Geomagnetic impact estimate
                geo = self._geomagnetic.predict_dst(
                    flare_energy_J=result["energy_released_J"]
                )
                evt["dst_peak_nT"] = geo["dst_peak_nT"]
                evt["storm_class"] = geo["storm_class"]

        self._last_utac = self._build_utac_dict()
        self._cycle_count += 1

        state = {
            "utac_state": self._last_utac,
            "crep_state": self._last_crep.to_dict(),
            "phase_events": new_events,
            "flare_count": len(new_events),
            "gamma_solar": self._last_crep.Gamma,
            "gamma_nominal": GAMMA_SOLAR,
            "benchmark_targets": SOLAR_TARGETS,
            "genesis_available": _GENESIS_AVAILABLE,
        }

        # ── Ethics Gate Light (Phase H) ────────────────────────────────────────
        tension = getattr(self, "_tension_metric", None)
        if tension is not None:
            tension_value = float(tension.get_current_tension())
            ethics_result = self._ethics_gate.check(state=state, tension=tension_value)
            if not ethics_result["allowed"]:
                raise RuntimeError(f"EthicsGate blocked: {ethics_result['reason']}")

        return state

    def get_crep_state(self) -> dict:
        """Return current CREP tensor state {C, R, E, P, Gamma}."""
        return self._last_crep.to_dict()

    def get_utac_state(self) -> dict:
        """Return current UTAC state {H, dH_dt, H_star, K_eff}."""
        return dict(self._last_utac)

    def get_phase_events(self) -> list:
        """Return list of all recorded PhaseTransitionEvents (flares)."""
        return list(self._phase_events)

    def to_zenodo_record(self) -> dict:
        """Return a Zenodo-compatible metadata record.

        Ethics Gate check is also performed here before export.
        """
        state = self._last_utac
        # ── Ethics Gate Light (Phase H) ────────────────────────────────────────
        tension = getattr(self, "_tension_metric", None)
        if tension is not None:
            tension_value = float(tension.get_current_tension())
            ethics_result = self._ethics_gate.check(state=state, tension=tension_value)
            if not ethics_result["allowed"]:
                raise RuntimeError(f"EthicsGate blocked: {ethics_result['reason']}")

        return {
            "title": "Solar Flare UTAC — GenesisAeon Package 21",
            "description": (
                "UTAC dynamical model of solar flare magnetic avalanche threshold. "
                f"Central result: Gamma_solar = {GAMMA_SOLAR:.4f} "
                f"(eta=0.03, sigma={SIGMA_CREP}). "
                "Package 21 of the GenesisAeon cross-domain CREP atlas."
            ),
            "creators": [{"name": "Römer, Johann", "affiliation": "MOR Research Collective"}],
            "keywords": [
                "solar flare", "UTAC", "CREP", "magnetic reconnection",
                "space weather", "self-organized criticality", "GenesisAeon",
            ],
            "license": "MIT",
            "doi": PACKAGE_REGISTRY_ENTRY["zenodo"],
            "upload_type": "software",
            "related_identifiers": [
                {"identifier": PACKAGE_REGISTRY_ENTRY["reference"], "relation": "isCitedBy"},
            ],
            "metadata": {
                "package": 21,
                "gamma_solar": GAMMA_SOLAR,
                "eta_xclass": 0.03,
                "sigma_crep": SIGMA_CREP,
                "utac_state": state,
                "crep_state": self._last_crep.to_dict(),
                "flare_count_total": len(self._phase_events),
                "cycle_count": self._cycle_count,
                "genesis_available": _GENESIS_AVAILABLE,
            },
            "created": datetime.now(timezone.utc).isoformat(),
        }

    # ── extended interface ─────────────────────────────────────────────────────

    def predict_flare_window(self, horizon_days: float = 3.0) -> dict:
        """Estimate flare probability window over the next horizon_days.

        Compares the UTAC-derived CREP state against the phase-transition
        threshold θ_PT ≈ Γ_solar.

        Returns
        -------
        dict with keys: horizon_days, Gamma_current, theta_PT, H_current,
            flare_probability, warning_level.
        """
        Gamma = self._last_crep.Gamma
        H = self._ar.H

        # Probability model: logistic in Gamma and H
        x = SIGMA_CREP * (Gamma - GAMMA_SOLAR) + 3.0 * (H - H_THRESHOLD)
        prob = float(1.0 / (1.0 + math.exp(-x)))

        if Gamma > 2.0 * GAMMA_SOLAR and H > 0.5:
            warning = "HIGH"
        elif Gamma > GAMMA_SOLAR or H > 0.4:
            warning = "MODERATE"
        else:
            warning = "LOW"

        return {
            "horizon_days": horizon_days,
            "Gamma_current": Gamma,
            "theta_PT": GAMMA_SOLAR,
            "H_current": H,
            "flare_probability": prob,
            "warning_level": warning,
        }

    # ── helpers ────────────────────────────────────────────────────────────────

    def _build_utac_dict(self) -> dict:
        H = self._ar.H
        K = 1.0  # normalised ceiling
        dH_dt = self._ar.dH_dt(
            H,
            self._reconnect.reconnection_rate(H, self._last_crep.Gamma),
        )
        return {
            "H": H,
            "dH_dt": dH_dt,
            "H_star": H_STAR_QUIET,
            "K_eff": K,
        }

    def __repr__(self) -> str:
        return (
            f"SolarFlareUTAC(id={self.active_region_id!r}, "
            f"H={self._ar.H:.3f}, Gamma={self._last_crep.Gamma:.4f}, "
            f"flares={len(self._phase_events)})"
        )
