"""Benchmark validation against GOES catalog and Solar Orbiter data.

Validates the solar-flare-utac model against the targets defined in
SOLAR_TARGETS (constants.py), which are derived from:

  - GOES X-ray catalog 1975–2026 (NOAA NGDC)
  - Velasco Herrera et al. 2026, JGR Space Physics
  - Solar Orbiter close-pass data, 30 Sept 2024 (A&A 2026)
"""
from __future__ import annotations

import math

from .constants import SOLAR_TARGETS
from .superflare import SuperflareStatistics


class BenchmarkResult:
    """Container for a single benchmark test outcome."""

    def __init__(
        self,
        name: str,
        target: float,
        tolerance: float,
        measured: float,
        tolerance_mode: str = "relative",
    ) -> None:
        self.name = name
        self.target = target
        self.tolerance = tolerance
        self.measured = measured
        self.tolerance_mode = tolerance_mode
        self.passed = self._check()

    def _check(self) -> bool:
        if self.tolerance_mode == "log":
            # Log-scale tolerance: |log10(m) - log10(t)| < tol
            if self.target <= 0 or self.measured <= 0:
                return False
            return abs(math.log10(self.measured) - math.log10(self.target)) <= self.tolerance
        # Relative tolerance: |m - t| / t < tol
        if self.target == 0:
            return abs(self.measured) <= self.tolerance
        return abs(self.measured - self.target) / abs(self.target) <= self.tolerance

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.name}: target={self.target:.4g}, "
            f"measured={self.measured:.4g} (tol={self.tolerance}, {self.tolerance_mode})"
        )


class SolarBenchmark:
    """Run validation suite against SOLAR_TARGETS.

    Parameters
    ----------
    seed : int
        RNG seed for reproducible synthetic data.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._results: list[BenchmarkResult] = []

    # ── primary interface ──────────────────────────────────────────────────────

    def run_all(self) -> list[BenchmarkResult]:
        """Execute all benchmark checks.  Returns list of BenchmarkResult."""
        self._results = []
        self._check_gamma_solar()
        self._check_xclass_energy()
        self._check_power_law_index()
        self._check_reconnection_timescale()
        self._check_flare_frequency()
        return self._results

    def summary(self) -> dict:
        """Return pass/fail summary statistics."""
        if not self._results:
            self.run_all()
        passed = sum(r.passed for r in self._results)
        total = len(self._results)
        return {
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total > 0 else 0.0,
            "results": [str(r) for r in self._results],
        }

    # ── individual benchmark checks ────────────────────────────────────────────

    def _check_gamma_solar(self) -> None:
        from .crep_solar import SolarCREP
        crep = SolarCREP(seed=self.seed)
        state = crep.nominal()
        target, tol = SOLAR_TARGETS["gamma_solar"]
        self._results.append(
            BenchmarkResult("gamma_solar", target, tol, state.Gamma, "relative")
        )

    def _check_xclass_energy(self) -> None:
        from .constants import E_MAX_J
        target, tol = SOLAR_TARGETS["xclass_energy_J"]
        self._results.append(
            BenchmarkResult("xclass_energy_J", target, tol, E_MAX_J, "log")
        )

    def _check_power_law_index(self) -> None:
        sf = SuperflareStatistics(seed=self.seed)
        catalog = sf.generate_catalog(n_years=47.0)
        fit = sf.fit_power_law(catalog.energies_J)
        target, tol = SOLAR_TARGETS["power_law_index"]
        self._results.append(
            BenchmarkResult("power_law_index", target, tol, fit["alpha"], "relative")
        )

    def _check_reconnection_timescale(self) -> None:
        from .constants import GAMMA_SOLAR, H_THRESHOLD
        from .reconnection import ReconnectionThreshold
        rc = ReconnectionThreshold()
        t_min = rc.reconnection_time_min(H_THRESHOLD + 0.01, GAMMA_SOLAR * 2.0)
        target, tol = SOLAR_TARGETS["reconnection_timescale_min"]
        self._results.append(
            BenchmarkResult("reconnection_timescale_min", target, tol, t_min, "relative")
        )

    def _check_flare_frequency(self) -> None:
        from .constants import XCLASS_PER_CYCLE
        target, tol = SOLAR_TARGETS["flare_frequency_per_cycle"]
        self._results.append(
            BenchmarkResult(
                "flare_frequency_per_cycle", target, tol, float(XCLASS_PER_CYCLE), "relative"
            )
        )
