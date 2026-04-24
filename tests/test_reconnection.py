"""Tests for ReconnectionThreshold instability model."""
from __future__ import annotations

import pytest

from solar_flare_utac.constants import (
    GAMMA_SOLAR,
    H_THRESHOLD,
    LAMBDA_ERUPTIVE,
    LAMBDA_QUIET,
)
from solar_flare_utac.reconnection import ReconnectionThreshold


@pytest.fixture
def rc() -> ReconnectionThreshold:
    return ReconnectionThreshold()


class TestReconnectionThreshold:
    def test_quiescent_below_threshold(self, rc: ReconnectionThreshold) -> None:
        lam = rc.reconnection_rate(H=0.1, Gamma=GAMMA_SOLAR * 10.0)
        assert lam == LAMBDA_QUIET

    def test_quiescent_low_gamma(self, rc: ReconnectionThreshold) -> None:
        lam = rc.reconnection_rate(H=H_THRESHOLD + 0.1, Gamma=0.0)
        assert lam == LAMBDA_QUIET

    def test_eruptive_rate_above_quiet(self, rc: ReconnectionThreshold) -> None:
        lam_erupt = rc.reconnection_rate(H=H_THRESHOLD + 0.1, Gamma=GAMMA_SOLAR * 3.0)
        assert lam_erupt > LAMBDA_QUIET

    def test_eruptive_rate_bounded(self, rc: ReconnectionThreshold) -> None:
        lam = rc.reconnection_rate(H=0.99, Gamma=100.0)
        assert lam <= LAMBDA_QUIET + LAMBDA_ERUPTIVE + 1e-9

    def test_is_unstable_true(self, rc: ReconnectionThreshold) -> None:
        assert rc.is_unstable(H=H_THRESHOLD + 0.05, Gamma=GAMMA_SOLAR * 2.0)

    def test_is_unstable_false_low_H(self, rc: ReconnectionThreshold) -> None:
        assert not rc.is_unstable(H=0.1, Gamma=GAMMA_SOLAR * 10.0)

    def test_is_unstable_false_low_gamma(self, rc: ReconnectionThreshold) -> None:
        assert not rc.is_unstable(H=H_THRESHOLD + 0.1, Gamma=0.0)

    def test_current_sheet_thickness_decreases_with_H(self, rc: ReconnectionThreshold) -> None:
        t1 = rc.current_sheet_thickness_km(H=0.1)
        t2 = rc.current_sheet_thickness_km(H=0.9)
        assert t1 > t2

    def test_current_sheet_thickness_positive(self, rc: ReconnectionThreshold) -> None:
        for H in (0.0, 0.3, 0.6, 0.9):
            assert rc.current_sheet_thickness_km(H) > 0.0

    def test_reconnection_time_positive(self, rc: ReconnectionThreshold) -> None:
        t = rc.reconnection_time_min(H=H_THRESHOLD + 0.1, Gamma=GAMMA_SOLAR * 2.0)
        assert t > 0.0

    def test_reconnection_time_decreases_with_gamma(self, rc: ReconnectionThreshold) -> None:
        H = H_THRESHOLD + 0.1
        t_low = rc.reconnection_time_min(H=H, Gamma=GAMMA_SOLAR * 2.0)
        t_high = rc.reconnection_time_min(H=H, Gamma=GAMMA_SOLAR * 10.0)
        assert t_high < t_low

    def test_critical_current_proxy_zero_below_threshold(self, rc: ReconnectionThreshold) -> None:
        proxy = rc.critical_current_density_proxy(H=0.0)
        assert proxy == 0.0

    def test_critical_current_proxy_positive_above(self, rc: ReconnectionThreshold) -> None:
        proxy = rc.critical_current_density_proxy(H=H_THRESHOLD + 0.1)
        assert proxy > 0.0

    def test_critical_current_proxy_bounded(self, rc: ReconnectionThreshold) -> None:
        proxy = rc.critical_current_density_proxy(H=1.0)
        assert 0.0 <= proxy <= 1.0
