"""Tests for the Diamond-template interface of SolarFlareUTAC.

Verifies:
  - run_cycle() returns required keys
  - get_crep_state() returns {C, R, E, P, Gamma} with correct structure
  - get_utac_state() returns {H, dH_dt, H_star, K_eff} in valid ranges
  - get_phase_events() returns a list
  - to_zenodo_record() returns a dict with required metadata keys
  - predict_flare_window() returns probability and warning level
  - Gamma_solar ≈ 0.014 (Package 21 central result)
"""
from __future__ import annotations

import math

import pytest

from solar_flare_utac import GAMMA_SOLAR, SolarFlareUTAC


@pytest.fixture(scope="module")
def model() -> SolarFlareUTAC:
    m = SolarFlareUTAC(seed=42, active_region_id="AR_test")
    m.run_cycle(duration_hours=6.0)
    return m


# ── run_cycle ──────────────────────────────────────────────────────────────────

class TestRunCycle:
    def test_returns_dict(self, model: SolarFlareUTAC) -> None:
        state = model.run_cycle(duration_hours=1.0)
        assert isinstance(state, dict)

    def test_required_keys(self, model: SolarFlareUTAC) -> None:
        state = model.run_cycle(duration_hours=1.0)
        for key in ("utac_state", "crep_state", "phase_events", "flare_count", "gamma_solar"):
            assert key in state, f"Missing key: {key}"

    def test_flare_count_nonnegative(self, model: SolarFlareUTAC) -> None:
        state = model.run_cycle(duration_hours=1.0)
        assert state["flare_count"] >= 0

    def test_gamma_nominal(self, model: SolarFlareUTAC) -> None:
        state = model.run_cycle(duration_hours=1.0)
        # Gamma should be positive and in a physically sensible range
        gamma = state["crep_state"]["Gamma"]
        assert 0.0 < gamma < 1.0


# ── get_crep_state ─────────────────────────────────────────────────────────────

class TestCREPState:
    def test_keys(self, model: SolarFlareUTAC) -> None:
        state = model.get_crep_state()
        assert set(state.keys()) == {"C", "R", "E", "P", "Gamma"}

    def test_components_in_range(self, model: SolarFlareUTAC) -> None:
        state = model.get_crep_state()
        for key in ("C", "R", "E", "P"):
            assert 0.0 <= state[key] <= 1.0, f"{key} = {state[key]} out of [0, 1]"

    def test_gamma_positive(self, model: SolarFlareUTAC) -> None:
        state = model.get_crep_state()
        assert state["Gamma"] > 0.0

    def test_gamma_solar_nominal(self) -> None:
        """Package 21 central result: Γ_solar = arctanh(0.03) / 2.2 ≈ 0.014."""
        expected = math.atanh(0.03) / 2.2
        assert abs(GAMMA_SOLAR - expected) < 1e-6

    def test_gamma_solar_value(self) -> None:
        """Γ_solar must be within benchmark tolerance ±0.005 of 0.014."""
        assert abs(GAMMA_SOLAR - 0.014) < 0.005


# ── get_utac_state ─────────────────────────────────────────────────────────────

class TestUTACState:
    def test_keys(self, model: SolarFlareUTAC) -> None:
        state = model.get_utac_state()
        assert set(state.keys()) == {"H", "dH_dt", "H_star", "K_eff"}

    def test_H_in_range(self, model: SolarFlareUTAC) -> None:
        state = model.get_utac_state()
        assert 0.0 <= state["H"] <= 1.0

    def test_H_star_positive(self, model: SolarFlareUTAC) -> None:
        state = model.get_utac_state()
        assert state["H_star"] > 0.0

    def test_K_eff_positive(self, model: SolarFlareUTAC) -> None:
        state = model.get_utac_state()
        assert state["K_eff"] > 0.0

    def test_H_le_K_eff(self, model: SolarFlareUTAC) -> None:
        state = model.get_utac_state()
        assert state["H"] <= state["K_eff"]


# ── get_phase_events ───────────────────────────────────────────────────────────

class TestPhaseEvents:
    def test_returns_list(self, model: SolarFlareUTAC) -> None:
        events = model.get_phase_events()
        assert isinstance(events, list)

    def test_event_structure(self, model: SolarFlareUTAC) -> None:
        events = model.get_phase_events()
        for evt in events:
            assert "type" in evt
            assert "time_h" in evt
            assert "energy_J" in evt
            assert evt["energy_J"] >= 0.0

    def test_event_type(self, model: SolarFlareUTAC) -> None:
        events = model.get_phase_events()
        for evt in events:
            assert evt["type"] == "solar_flare"


# ── to_zenodo_record ───────────────────────────────────────────────────────────

class TestZenodoRecord:
    def test_returns_dict(self, model: SolarFlareUTAC) -> None:
        record = model.to_zenodo_record()
        assert isinstance(record, dict)

    def test_required_metadata(self, model: SolarFlareUTAC) -> None:
        record = model.to_zenodo_record()
        for key in ("title", "creators", "license", "doi", "metadata"):
            assert key in record, f"Zenodo record missing key: {key}"

    def test_metadata_gamma(self, model: SolarFlareUTAC) -> None:
        record = model.to_zenodo_record()
        meta = record["metadata"]
        assert "gamma_solar" in meta
        assert abs(meta["gamma_solar"] - GAMMA_SOLAR) < 1e-9

    def test_package_number(self, model: SolarFlareUTAC) -> None:
        record = model.to_zenodo_record()
        assert record["metadata"]["package"] == 21


# ── predict_flare_window ───────────────────────────────────────────────────────

class TestFlareWindow:
    def test_returns_dict(self, model: SolarFlareUTAC) -> None:
        w = model.predict_flare_window(horizon_days=3.0)
        assert isinstance(w, dict)

    def test_required_keys(self, model: SolarFlareUTAC) -> None:
        w = model.predict_flare_window()
        for key in ("horizon_days", "Gamma_current", "theta_PT", "H_current",
                    "flare_probability", "warning_level"):
            assert key in w

    def test_probability_in_range(self, model: SolarFlareUTAC) -> None:
        w = model.predict_flare_window()
        assert 0.0 <= w["flare_probability"] <= 1.0

    def test_warning_level_valid(self, model: SolarFlareUTAC) -> None:
        w = model.predict_flare_window()
        assert w["warning_level"] in ("LOW", "MODERATE", "HIGH")
