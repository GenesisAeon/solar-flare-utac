"""Solar-specific CREP tensor computation.

Maps four observational quantities (C, R, E, P) onto a scalar CREP coupling
Γ(t).  The nominal solar calibration gives Γ_solar ≈ 0.014 (Package 21
central result), placing solar active regions in the ultra-sensitive regime.

CREP components
---------------
C — magnetic helicity coherence     (twist uniformity across active region)
R — resonance                        (photospheric driver vs. coronal response)
E — non-potential energy fraction    (emergence from potential-field state)
P — permutation entropy (inverted)   (GOES 1–8 Å flux regularity)

η_CREP = (C + R + E + P) / 4 → Γ = arctanh(η_CREP) / σ
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .constants import GAMMA_SOLAR, SEED, SIGMA_CREP


# ── genesis-os stubs ───────────────────────────────────────────────────────────
try:
    from genesis.core.crep import CREPTensor  # type: ignore[import-not-found]
    _GENESIS_AVAILABLE = True
except ImportError:
    _GENESIS_AVAILABLE = False


@dataclass
class CREPState:
    """Snapshot of the four CREP components and derived Γ."""

    C: float   # helicity coherence     ∈ [0, 1]
    R: float   # resonance              ∈ [0, 1]
    E: float   # non-potential fraction ∈ [0, 1]
    P: float   # 1 – perm. entropy      ∈ [0, 1]
    Gamma: float

    def to_dict(self) -> dict:
        return {"C": self.C, "R": self.R, "E": self.E, "P": self.P, "Gamma": self.Gamma}


class SolarCREP:
    """Compute the solar CREP tensor from active-region state variables.

    Parameters
    ----------
    sigma : float
        CREP coupling constant σ (default 2.2).
    seed : int
        RNG seed for stochastic components.
    """

    def __init__(self, sigma: float = SIGMA_CREP, seed: int = SEED) -> None:
        self.sigma = sigma
        self.rng = np.random.default_rng(seed)
        self._last_state: CREPState | None = None

    # ── primary interface ──────────────────────────────────────────────────────

    def compute(
        self,
        H: float,
        dH_dt: float,
        flux_series: NDArray[np.float64] | None = None,
        solar_cycle_phase: float = 0.0,
    ) -> CREPState:
        """Compute Γ(t) from current active-region state.

        Parameters
        ----------
        H : float
            Normalised free energy ∈ [0, 1].
        dH_dt : float
            Current rate of change of H [hr⁻¹].
        flux_series : array, optional
            Recent GOES 1–8 Å flux window (used for P component).
        solar_cycle_phase : float
            Solar cycle phase ∈ [0, 2π] (used for R component).
        """
        C = self._helicity_coherence(H)
        R = self._resonance(H, solar_cycle_phase)
        E = self._nonpotential_fraction(H, dH_dt)
        P = self._permutation_component(flux_series)

        eta = (C + R + E + P) / 4.0
        eta = float(np.clip(eta, 1e-6, 1.0 - 1e-6))
        Gamma = math.atanh(eta) / self.sigma

        state = CREPState(C=C, R=R, E=E, P=P, Gamma=Gamma)
        self._last_state = state
        return state

    def nominal(self) -> CREPState:
        """Return the nominal solar CREP state (η ≈ 0.03, Γ ≈ 0.014)."""
        # Each component = 0.03 → η_avg = 0.03
        return CREPState(C=0.03, R=0.03, E=0.03, P=0.03, Gamma=GAMMA_SOLAR)

    # ── component estimators ───────────────────────────────────────────────────

    def _helicity_coherence(self, H: float) -> float:
        """C: magnetic helicity coherence.

        Increases as H approaches H_THRESHOLD — more organised twist.
        Nominally very small (solar field geometry is complex).
        """
        from .constants import H_THRESHOLD
        base = 0.01
        ramp = 0.05 * math.tanh(10.0 * (H - 0.3))
        jitter = float(self.rng.normal(0.0, 0.003))
        return float(np.clip(base + ramp + jitter, 0.001, 0.15))

    def _resonance(self, H: float, cycle_phase: float) -> float:
        """R: resonance between photospheric driver and coronal response.

        Modulated by solar cycle and H.  Solar coronal resonance is weak
        compared with oceanic/neural systems → R stays near 0.03.
        """
        base = 0.02
        cycle_mod = 0.01 * (1.0 + math.sin(cycle_phase))
        h_mod = 0.01 * H
        jitter = float(self.rng.normal(0.0, 0.002))
        return float(np.clip(base + cycle_mod + h_mod + jitter, 0.001, 0.12))

    def _nonpotential_fraction(self, H: float, dH_dt: float) -> float:
        """E: non-potential energy fraction.

        The fraction of total magnetic energy stored above the current-free
        (potential) field state.  Scales with both H and flux emergence rate.
        """
        base = 0.02 * H
        emergence = float(np.clip(0.01 * dH_dt / max(abs(dH_dt), 1e-9), 0.0, 0.05))
        jitter = float(self.rng.normal(0.0, 0.002))
        return float(np.clip(base + emergence + jitter, 0.001, 0.20))

    def _permutation_component(
        self, flux: NDArray[np.float64] | None, m: int = 4
    ) -> float:
        """P: 1 − permutation entropy of GOES flux window.

        High permutation entropy (chaotic flare timing) → small P.
        During pre-flare organisation → entropy drops → P rises slightly.
        Nominally: pe ≈ 0.97 → P ≈ 0.03.
        """
        if flux is None or len(flux) < m:
            return 0.03   # nominal solar value

        from .goes_loader import GOESLoader
        loader = GOESLoader.__new__(GOESLoader)
        pe = loader.permutation_entropy(flux, m=m, normalised=True)
        P = float(np.clip(1.0 - pe, 0.001, 0.15))
        return P

    @property
    def last_state(self) -> CREPState | None:
        return self._last_state
