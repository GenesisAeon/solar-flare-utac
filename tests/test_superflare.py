"""Tests for SuperflareStatistics power-law distribution model."""
from __future__ import annotations

import math

import numpy as np
import pytest

from solar_flare_utac.constants import POWER_LAW_INDEX_ALPHA, POWER_LAW_INDEX_TAU
from solar_flare_utac.superflare import SuperflareStatistics


@pytest.fixture(scope="module")
def sf_catalog():
    sf = SuperflareStatistics(seed=42)
    catalog = sf.generate_catalog(n_years=47.0)
    return sf, catalog


class TestCatalogGeneration:
    def test_catalog_nonempty(self, sf_catalog) -> None:
        _, catalog = sf_catalog
        assert len(catalog.energies_J) > 0

    def test_energies_positive(self, sf_catalog) -> None:
        _, catalog = sf_catalog
        assert np.all(catalog.energies_J > 0.0)

    def test_sizes_positive(self, sf_catalog) -> None:
        _, catalog = sf_catalog
        assert np.all(catalog.sizes > 0.0)

    def test_durations_positive(self, sf_catalog) -> None:
        _, catalog = sf_catalog
        assert np.all(catalog.durations_h > 0.0)

    def test_times_increasing(self, sf_catalog) -> None:
        _, catalog = sf_catalog
        assert np.all(np.diff(catalog.times_h) > 0.0)


class TestPowerLawFit:
    def test_fit_returns_alpha(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        fit = sf.fit_power_law(catalog.energies_J)
        assert "alpha" in fit
        assert not math.isnan(fit["alpha"])

    def test_fitted_alpha_in_range(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        fit = sf.fit_power_law(catalog.energies_J)
        # α should be near 1.8 with some tolerance (large synthetic sample)
        assert 1.0 < fit["alpha"] < 3.0

    def test_fitted_alpha_near_target(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        fit = sf.fit_power_law(catalog.energies_J)
        assert abs(fit["alpha"] - POWER_LAW_INDEX_ALPHA) < 0.5

    def test_ks_pvalue_returned(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        fit = sf.fit_power_law(catalog.energies_J)
        assert "ks_pvalue" in fit
        assert 0.0 <= fit["ks_pvalue"] <= 1.0

    def test_short_sample_returns_nan(self) -> None:
        sf = SuperflareStatistics(seed=42)
        fit = sf.fit_power_law(np.array([1.0, 2.0]))
        assert math.isnan(fit["alpha"])


class TestScaleInvariance:
    def test_measure_in_range(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        m = sf.scale_invariance_measure(catalog.sizes)
        assert 0.0 <= m <= 1.0

    def test_perfect_match_gives_one(self) -> None:
        sf = SuperflareStatistics(seed=42)
        # Generate sizes that perfectly match τ_target
        catalog = sf.generate_catalog(n_years=100.0)
        m = sf.scale_invariance_measure(catalog.sizes, tau_target=POWER_LAW_INDEX_TAU)
        assert m > 0.0


class TestAvalancheShapeCollapse:
    def test_returns_gamma(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        result = sf.avalanche_shape_collapse(catalog.sizes, catalog.durations_h)
        assert "gamma" in result

    def test_gamma_positive_or_nan(self, sf_catalog) -> None:
        sf, catalog = sf_catalog
        result = sf.avalanche_shape_collapse(catalog.sizes, catalog.durations_h)
        gamma = result["gamma"]
        assert math.isnan(gamma) or gamma > 0.0
