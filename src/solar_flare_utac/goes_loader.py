"""GOES X-ray flux data loader and synthetic generator.

Reproduces the statistical properties of the 47-year GOES 1–8 Å record
(1975–2026) described in Velasco Herrera et al. (2026, JGR Space Physics).
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from .constants import (
    GOES_END_YEAR,
    GOES_START_YEAR,
    POWER_LAW_INDEX_ALPHA,
    SEED,
    SOLAR_CYCLE_YEARS,
    XCLASS_PER_CYCLE,
)

if TYPE_CHECKING:
    pass


class GOESLoader:
    """Loads or synthetically generates GOES 1–8 Å X-ray flux time series.

    When observational data is unavailable the generator reproduces the key
    statistical fingerprints of the real GOES record (power-law flare energy
    distribution, solar-cycle modulation, lognormal background variance).
    """

    def __init__(self, seed: int = SEED) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self._times: NDArray[np.float64] | None = None
        self._flux: NDArray[np.float64] | None = None

    # ── synthetic generation ───────────────────────────────────────────────────

    def generate_synthetic(
        self,
        n_years: int = GOES_END_YEAR - GOES_START_YEAR,
        cadence_hours: float = 1.0,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Generate a synthetic GOES 1–8 Å flux time series.

        Returns
        -------
        times : array of shape (N,)
            Time axis in hours from t=0.
        flux : array of shape (N,)
            Estimated irradiance in W m⁻².
        """
        n_steps = int(n_years * 365.25 * 24 / cadence_hours)
        times = np.arange(n_steps, dtype=np.float64) * cadence_hours

        # Background: B-class ~10⁻⁷ W/m², modulated by 11-year solar cycle
        cycle_phase = 2.0 * math.pi * times / (SOLAR_CYCLE_YEARS * 8760.0)
        solar_modulation = 1.0 + 0.8 * np.sin(cycle_phase) ** 2
        background = 1e-7 * solar_modulation
        noise = self.rng.lognormal(mean=0.0, sigma=0.4, size=n_steps)
        flux = background * noise

        # Inject flare events drawn from a power-law size distribution
        n_flares = int(XCLASS_PER_CYCLE / SOLAR_CYCLE_YEARS * n_years * 120)
        t_idx = self.rng.integers(0, n_steps, size=n_flares)
        flare_peaks = self._sample_powerlaw(
            n=n_flares, e_min=1e-8, e_max=1e-3, alpha=POWER_LAW_INDEX_ALPHA
        )

        decay_steps = max(1, int(1.5 / cadence_hours))
        for ti, peak in zip(t_idx, flare_peaks):
            t_end = min(n_steps, ti + decay_steps * 6)
            dt = np.arange(t_end - ti, dtype=np.float64)
            # Fast rise (1 step), exponential decay
            rise = np.exp(-((dt - 0.5) ** 2) / 0.5)
            rise[1:] = np.exp(-dt[1:] / decay_steps)
            flux[ti:t_end] += peak * rise[: t_end - ti]

        self._times = times
        self._flux = flux
        return times, flux

    # ── statistical tools ──────────────────────────────────────────────────────

    def permutation_entropy(
        self, flux: NDArray[np.float64], m: int = 4, normalised: bool = True
    ) -> float:
        """Permutation entropy of order m (Bandt & Pompe 2002).

        Returns a value in [0, 1] when normalised=True.
        """
        n = len(flux)
        if n < m:
            return 0.0

        patterns: dict[tuple[int, ...], int] = {}
        for i in range(n - m + 1):
            key = tuple(int(x) for x in np.argsort(flux[i : i + m]))
            patterns[key] = patterns.get(key, 0) + 1

        total = sum(patterns.values())
        probs = np.fromiter((v / total for v in patterns.values()), dtype=float)
        h = float(-np.dot(probs, np.log2(probs + 1e-14)))
        if normalised:
            h_max = math.log2(math.factorial(m))
            return float(np.clip(h / h_max if h_max > 0 else 0.0, 0.0, 1.0))
        return float(h)

    def ar1_coefficient(self, flux: NDArray[np.float64]) -> float:
        """Estimate the AR(1) coefficient (critical slowing down indicator)."""
        if len(flux) < 3:
            return 0.0
        x = flux - float(np.mean(flux))
        std = float(np.std(x))
        if std < 1e-30:
            return 0.0
        return float(np.clip(np.corrcoef(x[:-1], x[1:])[0, 1], -1.0, 1.0))

    def identify_flares(
        self,
        flux: NDArray[np.float64],
        times: NDArray[np.float64],
        threshold_multiplier: float = 10.0,
    ) -> list[dict]:
        """Identify flare events using a simple background-threshold method."""
        background = float(np.percentile(flux, 25))
        threshold = background * threshold_multiplier

        flares: list[dict] = []
        in_flare = False
        start_i = 0

        for i in range(len(flux)):
            if not in_flare and flux[i] > threshold:
                in_flare = True
                start_i = i
            elif in_flare and (flux[i] < threshold or i == len(flux) - 1):
                end_i = i
                seg = flux[start_i:end_i]
                peak_off = int(np.argmax(seg))
                flares.append(
                    {
                        "start_time_h": float(times[start_i]),
                        "peak_time_h": float(times[start_i + peak_off]),
                        "end_time_h": float(times[end_i - 1]),
                        "peak_flux_W_m2": float(seg[peak_off]),
                        "fluence": float(np.trapz(seg, times[start_i:end_i])),
                        "duration_h": float(times[end_i - 1] - times[start_i]),
                    }
                )
                in_flare = False

        return flares

    # ── helpers ────────────────────────────────────────────────────────────────

    def _sample_powerlaw(
        self,
        n: int,
        e_min: float,
        e_max: float,
        alpha: float,
    ) -> NDArray[np.float64]:
        """Sample n values from P(E) ∝ E^(−α) via inverse-CDF."""
        beta = 1.0 - alpha  # negative for α > 1
        u = self.rng.uniform(size=n)
        # CDF^{-1}: E = (u*(E_max^β - E_min^β) + E_min^β)^(1/β)
        lo, hi = e_min**beta, e_max**beta
        samples = (u * (hi - lo) + lo) ** (1.0 / beta)
        return np.clip(samples.astype(np.float64), e_min, e_max)

    @property
    def times(self) -> NDArray[np.float64] | None:
        return self._times

    @property
    def flux(self) -> NDArray[np.float64] | None:
        return self._flux
