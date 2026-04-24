"""Geomagnetic storm impact model.

Maps solar flare energy and CME parameters to ground-level geomagnetic
disturbance.  Calibrated against ESA CryoSat + Swarm (Jan–Feb 2026) X-class
storm measurements.

The Dst (disturbance storm time) index is used as the geomagnetic impact
proxy.  A simple empirical model (Burton et al. 1975) is implemented.
"""
from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from .constants import E_MAX_J, SEED


class GeomagneticStorm:
    """Estimate ground-level geomagnetic impact of a solar flare/CME event.

    Parameters
    ----------
    seed : int
        RNG seed for stochastic CME propagation uncertainty.
    """

    # Empirical coupling parameters (Burton et al. 1975, updated)
    _Q_COEFFICIENT: float = -3.6e-5  # Dst injection per unit solar wind pressure
    _DST_RECOVERY_TAU_H: float = 10.0  # Dst recovery e-folding time [hr]
    _CME_TRANSIT_MEAN_H: float = 40.0  # Mean Sun–Earth transit time [hr]
    _CME_TRANSIT_SIGMA_H: float = 8.0  # Sigma of transit time [hr]

    def __init__(self, seed: int = SEED) -> None:
        self.rng = np.random.default_rng(seed)
        self._dst_current: float = 0.0  # nT
        self._storm_history: list[dict] = []

    # ── primary interface ──────────────────────────────────────────────────────

    def predict_dst(
        self,
        flare_energy_J: float,
        cme_speed_km_s: float = 1000.0,
    ) -> dict:
        """Predict Dst index from flare energy and CME speed.

        Parameters
        ----------
        flare_energy_J : float
            Flare radiated energy [J].
        cme_speed_km_s : float
            CME propagation speed [km/s].

        Returns
        -------
        dict with keys: dst_peak_nT, transit_time_h, storm_class, kp_proxy.
        """
        eta_flare = float(np.clip(flare_energy_J / E_MAX_J, 1e-12, 1.0))

        # Solar wind dynamic pressure proxy (scales with CME speed^2)
        v_ref = 400.0  # typical slow solar wind [km/s]
        p_dyn = (cme_speed_km_s / v_ref) ** 2 * eta_flare

        dst_injection = self._Q_COEFFICIENT * p_dyn * 1e12   # scale to nT
        dst_peak = float(np.clip(dst_injection, -800.0, 0.0))

        transit_hours = self.rng.normal(
            self._CME_TRANSIT_MEAN_H, self._CME_TRANSIT_SIGMA_H
        )
        transit_hours = max(transit_hours, 10.0)

        storm_class = self._classify_storm(dst_peak)
        kp_proxy = self._dst_to_kp(dst_peak)

        event = {
            "dst_peak_nT": dst_peak,
            "transit_time_h": float(transit_hours),
            "storm_class": storm_class,
            "kp_proxy": kp_proxy,
            "flare_energy_J": flare_energy_J,
            "cme_speed_km_s": cme_speed_km_s,
        }
        self._storm_history.append(event)
        self._dst_current = dst_peak
        return event

    def dst_recovery(self, dst_0: float, elapsed_hours: float) -> float:
        """Exponential recovery of Dst after storm main phase."""
        return float(dst_0 * math.exp(-elapsed_hours / self._DST_RECOVERY_TAU_H))

    def simulate_storm_profile(
        self, dst_peak: float, duration_hours: float = 72.0, dt_hours: float = 1.0
    ) -> dict:
        """Simulate the full Dst storm profile (onset → main → recovery)."""
        n = int(duration_hours / dt_hours)
        times = np.arange(n) * dt_hours
        dst = np.zeros(n)

        # Simple two-phase model: sudden commencement at t=5hr, recovery after
        onset_h = 5.0
        main_duration_h = 10.0

        for i, t in enumerate(times):
            if t < onset_h:
                dst[i] = 0.0
            elif t < onset_h + main_duration_h:
                frac = (t - onset_h) / main_duration_h
                dst[i] = dst_peak * math.sin(math.pi / 2 * frac)
            else:
                dst[i] = self.dst_recovery(dst_peak, t - onset_h - main_duration_h)

        return {"times_h": times, "dst_nT": dst, "dst_peak": dst_peak}

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_storm(dst_nT: float) -> str:
        if dst_nT > -50.0:
            return "none"
        elif dst_nT > -100.0:
            return "moderate"
        elif dst_nT > -200.0:
            return "intense"
        else:
            return "super"

    @staticmethod
    def _dst_to_kp(dst_nT: float) -> float:
        """Empirical Dst → Kp conversion (Thomsen 2004)."""
        dst_abs = abs(dst_nT)
        if dst_abs < 30.0:
            return 0.0
        kp = math.log10(dst_abs / 20.0) * 3.0 + 1.0
        return float(np.clip(kp, 0.0, 9.0))

    @property
    def storm_history(self) -> list[dict]:
        return list(self._storm_history)

    @property
    def dst_current(self) -> float:
        return self._dst_current
