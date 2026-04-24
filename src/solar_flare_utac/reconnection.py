"""Magnetic reconnection threshold model.

Implements the current-sheet instability criterion for magnetic reconnection.
Based on Syrovatsky's theory: reconnection triggers when the current density
J > J_crit, which in the UTAC framework maps to H > H_THRESHOLD.

The CREP tensor Γ gates whether a current sheet at threshold will actually
reconnect — this requires coherent field geometry (C) and resonance (R).
This is the 'magnetic avalanche' mechanism reported by Solar Orbiter (2026).
"""
from __future__ import annotations

import math

import numpy as np

from .constants import (
    H_THRESHOLD,
    LAMBDA_ERUPTIVE,
    LAMBDA_QUIET,
    RECONNECTION_TIMESCALE_MIN,
    SIGMA_CREP,
    THETA_PT,
)


class ReconnectionThreshold:
    """CREP-gated magnetic reconnection instability model.

    The reconnection rate λ is determined by both the energy state H and the
    CREP coupling Γ.  Eruption requires *both* H > H_threshold AND Γ > θ_PT.

    Parameters
    ----------
    h_threshold : float
        Normalised free energy above which reconnection can trigger.
    theta_pt : float
        CREP phase-transition threshold Γ_PT (default ≈ Γ_solar).
    """

    def __init__(
        self,
        h_threshold: float = H_THRESHOLD,
        theta_pt: float = THETA_PT,
    ) -> None:
        self.h_threshold = h_threshold
        self.theta_pt = theta_pt

    # ── primary interface ──────────────────────────────────────────────────────

    def reconnection_rate(self, H: float, Gamma: float) -> float:
        """Return the reconnection dissipation rate λ [hr⁻¹].

        In the quiescent regime λ equals the slow background dissipation.
        When both the energy threshold and CREP threshold are exceeded the
        rate jumps to the eruptive value, gated by tanh(σΓ).

        Parameters
        ----------
        H : float
            Normalised free energy ∈ [0, 1].
        Gamma : float
            CREP coupling parameter Γ ≥ 0.
        """
        if H < self.h_threshold or Gamma <= self.theta_pt:
            return LAMBDA_QUIET

        crep_gate = math.tanh(SIGMA_CREP * Gamma)
        return LAMBDA_QUIET + (LAMBDA_ERUPTIVE - LAMBDA_QUIET) * crep_gate

    def is_unstable(self, H: float, Gamma: float) -> bool:
        """True when the current-sheet instability criterion is met."""
        return H >= self.h_threshold and Gamma > self.theta_pt

    # ── physics diagnostics ────────────────────────────────────────────────────

    def current_sheet_thickness_km(self, H: float) -> float:
        """Estimate Sweet–Parker current sheet half-thickness δ [km].

        Scales as δ ∝ (1 - H/H_max)^0.5 — thinner as free energy rises,
        making the sheet more prone to resistive tearing instability.
        """
        L_AR = 1e5  # Active region scale length [km]
        S_lundquist = 1e8  # Lundquist number for corona
        delta = L_AR / math.sqrt(S_lundquist) * math.sqrt(max(1.0 - H, 1e-6))
        return float(delta)

    def reconnection_time_min(self, H: float, Gamma: float) -> float:
        """Estimate inflow-driven reconnection timescale [min].

        Approaches RECONNECTION_TIMESCALE_MIN as H → 1 and Γ → Γ_solar.
        """
        if H < 1e-6:
            return 1e6
        rate_hr = self.reconnection_rate(H, Gamma)
        if rate_hr < 1e-9:
            return 1e6
        return float(60.0 / rate_hr)

    def critical_current_density_proxy(self, H: float) -> float:
        """J_crit proxy: fraction of H above which reconnection is possible."""
        return float(np.clip((H - self.h_threshold) / (1.0 - self.h_threshold), 0.0, 1.0))
