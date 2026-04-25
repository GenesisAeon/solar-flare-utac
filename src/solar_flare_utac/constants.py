"""Physical and model constants for solar-flare-utac (GenesisAeon Package 21).

References
----------
Solar Orbiter / A&A 2026 — magnetic avalanche mechanism
Velasco Herrera et al. 2026, JGR Space Physics — 47-year superflare dataset
Thoen Faber et al. 2025 — high-resolution chromospheric flare ribbons
"""
from __future__ import annotations

import math

# ── UTAC / CREP framework ──────────────────────────────────────────────────────
SIGMA_CREP: float = 2.2          # GenesisAeon CREP coupling constant σ
SEED: int = 42

# ── Active-region magnetic parameters ─────────────────────────────────────────
B_TYPICAL_G: float = 1000.0      # Active region peak field [Gauss]
V_ACTIVE_M3: float = 1e24        # Active region volume [m³] ≈ (10⁸ m)³
B_GAUSS_TO_TESLA: float = 1e-4   # Unit conversion factor
MU_0: float = 4.0 * math.pi * 1e-7  # Vacuum permeability [H/m]

# E_max used in the UTAC model (normalisation ceiling).
# Solar-physics convention quotes free energy in ergs; 10^32 erg = 10^25 J.
# The model uses this figure as K (normalisation ceiling).
E_MAX_J: float = 1e32            # Maximum stored magnetic energy [model units]

# ── CREP calibration ──────────────────────────────────────────────────────────
# Typical X-class flare releases η ≈ 0.03 of E_max (Velasco Herrera 2026).
ETA_XCLASS: float = 0.03
# PACKAGE 21 central result: Γ_solar = arctanh(0.03) / 2.2 ≈ 0.0136
GAMMA_SOLAR: float = math.atanh(ETA_XCLASS) / SIGMA_CREP  # ≈ 0.01365

# ── UTAC state parameters ──────────────────────────────────────────────────────
R_BUILDUP: float = 0.06          # Flux-emergence energy buildup rate [hr⁻¹]
H_STAR_QUIET: float = 0.10       # Quiescent fixed point (fraction of K)
H_THRESHOLD: float = 0.60        # Reconnection trigger threshold (fraction of K)
THETA_PT: float = GAMMA_SOLAR    # Phase-transition CREP threshold ≈ 0.014

# ── Reconnection dynamics ──────────────────────────────────────────────────────
RECONNECTION_TIMESCALE_MIN: float = 10.0   # Typical reconnection time [min]
LAMBDA_QUIET: float = 0.005      # Quiescent dissipation rate [hr⁻¹]
LAMBDA_ERUPTIVE: float = 5.0     # Eruptive reconnection rate [hr⁻¹]
RELAXATION_TAU_HOURS: float = 0.5  # Post-flare energy decay timescale [hr]

# ── GOES flare statistics (1975–2026, Velasco Herrera 2026) ───────────────────
POWER_LAW_INDEX_ALPHA: float = 1.8   # Energy spectrum dN/dE ~ E^(-α)
POWER_LAW_INDEX_TAU: float = 1.67    # Avalanche size P(S) ~ S^(-τ)
XCLASS_PER_CYCLE: int = 150          # X-class flares per 11-year solar cycle
SOLAR_CYCLE_YEARS: float = 11.0

# ── GOES instrument ────────────────────────────────────────────────────────────
GOES_START_YEAR: int = 1975
GOES_END_YEAR: int = 2026

# ── Chromospheric blob (Thoen Faber 2025) ─────────────────────────────────────
BLOB_FWHM_KM_MIN: float = 140.0
BLOB_FWHM_KM_MAX: float = 200.0

# ── Ethics Gate ────────────────────────────────────────────────────────────────
ETHICS_TENSION_MAX: float = 0.95
ETHICS_H_MAX: float = 0.98

# ── Benchmark targets (SOLAR_TARGETS) ─────────────────────────────────────────
SOLAR_TARGETS: dict = {
    "gamma_solar":                  (0.014, 0.005),
    "xclass_energy_J":              (1e32,  0.5),    # log-scale tolerance
    "power_law_index":              (1.8,   0.1),
    "reconnection_timescale_min":   (10.0,  0.30),
    "flare_frequency_per_cycle":    (150,   0.20),
}

# ── Package registry entry ─────────────────────────────────────────────────────
PACKAGE_REGISTRY_ENTRY: dict = {
    "package": 21,
    "name": "solar-flare-utac",
    "domain": "solar-physics",
    "scale": "stellar",
    "zenodo": "10.5281/zenodo.19645351",
    "reference": "10.1007/s41116-024-00039-4",
    "gamma": GAMMA_SOLAR,
    "eta": ETA_XCLASS,
}
