"""Tests for MagneticActiveRegion energy dynamics."""
from __future__ import annotations

import numpy as np
import pytest

from solar_flare_utac.active_region import MagneticActiveRegion
from solar_flare_utac.constants import H_STAR_QUIET, H_THRESHOLD, R_BUILDUP


@pytest.fixture
def ar() -> MagneticActiveRegion:
    return MagneticActiveRegion(r_buildup=R_BUILDUP, h_init=H_STAR_QUIET, seed=42)


class TestMagneticActiveRegion:
    def test_initial_H_in_range(self, ar: MagneticActiveRegion) -> None:
        assert 0.0 <= ar.H <= 1.0

    def test_dH_dt_positive_when_below_equilibrium(self, ar: MagneticActiveRegion) -> None:
        # At H=0, buildup dominates → dH/dt > 0
        rate = ar.dH_dt(H=0.0, lambda_reconnect=0.0)
        assert rate > 0.0

    def test_dH_dt_at_unity(self, ar: MagneticActiveRegion) -> None:
        # At H=1 with zero reconnection: dH/dt = r*(1-1) = 0
        rate = ar.dH_dt(H=1.0, lambda_reconnect=0.0)
        assert abs(rate) < 1e-9

    def test_step_advances_time(self, ar: MagneticActiveRegion) -> None:
        h_before = ar.H
        ar.step(dt_hours=0.1, lambda_reconnect=0.0)
        # H should change (buildup dominant)
        assert ar._time_hours > 0.0

    def test_step_H_stays_in_range(self, ar: MagneticActiveRegion) -> None:
        for _ in range(200):
            ar.step(dt_hours=0.1, lambda_reconnect=0.001)
        assert 0.0 <= ar.H <= 1.0

    def test_flare_triggered_above_threshold(self) -> None:
        # Start just below threshold; a large dt with no dissipation crosses it
        ar = MagneticActiveRegion(r_buildup=2.0, h_init=H_THRESHOLD - 0.001, seed=0)
        result = ar.step(dt_hours=1.0, lambda_reconnect=0.0, noise_sigma=0.0)
        assert result["flare_triggered"]

    def test_energy_released_nonnegative(self, ar: MagneticActiveRegion) -> None:
        for _ in range(100):
            result = ar.step(dt_hours=0.1, lambda_reconnect=0.0)
            assert result["energy_released_J"] >= 0.0

    def test_simulate_returns_expected_keys(self, ar: MagneticActiveRegion) -> None:
        out = ar.simulate(duration_hours=10.0, dt_hours=0.5)
        for key in ("times", "H", "flare_events"):
            assert key in out

    def test_simulate_H_array_shape(self, ar: MagneticActiveRegion) -> None:
        out = ar.simulate(duration_hours=5.0, dt_hours=0.5)
        assert len(out["H"]) == len(out["times"])

    def test_non_potential_fraction_nonneg(self, ar: MagneticActiveRegion) -> None:
        assert ar.non_potential_fraction >= 0.0

    def test_helicity_coherence_in_range(self, ar: MagneticActiveRegion) -> None:
        for _ in range(30):
            ar.step(dt_hours=0.1, lambda_reconnect=0.001)
        assert 0.0 <= ar.helicity_coherence <= 1.0

    def test_reset_restores_state(self, ar: MagneticActiveRegion) -> None:
        ar.step(dt_hours=1.0, lambda_reconnect=0.01)
        ar.reset(h_init=0.05)
        assert abs(ar.H - 0.05) < 1e-9
        assert ar.flare_count == 0


class TestSimulationPhysics:
    def test_energy_buildup_without_reconnection(self) -> None:
        ar = MagneticActiveRegion(r_buildup=0.1, h_init=0.0, seed=42)
        out = ar.simulate(duration_hours=20.0, dt_hours=0.1,
                          lambda_func=lambda H, t: 0.0)
        # H should increase significantly from 0
        assert float(out["H"][-1]) > 0.3

    def test_eruptive_reconnection_drops_H(self) -> None:
        ar = MagneticActiveRegion(h_init=H_THRESHOLD + 0.05, seed=0)
        # High reconnection rate should keep H low
        out = ar.simulate(
            duration_hours=5.0, dt_hours=0.1,
            lambda_func=lambda H, t: 10.0
        )
        assert float(np.mean(out["H"])) < H_THRESHOLD
