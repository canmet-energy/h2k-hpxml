"""Unit tests for SOC operating parity helpers (no OpenStudio required)."""

from tests.utils.operating_parity_utils import (
    assert_operating_parity,
    list_soc_operating_cases,
    load_expectations,
    max_rel_error,
)


def test_load_expectations_has_all_fixture_files():
    expectations = load_expectations()
    cases = list_soc_operating_cases()
    assert len(cases) == len(expectations["cases"])
    assert len(cases) >= 5


def test_max_rel_error():
    assert max_rel_error(100.0, 99.5) == 0.005
    assert max_rel_error(0.0, 0.0) == 0.0


def test_assert_operating_parity_passes_within_tolerance():
    failures = assert_operating_parity(
        {
            "hot_water_usage_Lperday_h2k": 187.0,
            "hot_water_usage_Lperday_hpxml": 186.5,
            "baseloads_elec_GJ_h2k": 25.0,
            "baseloads_elec_GJ_hpxml": 24.8,
        },
        {"hot_water_usage_Lperday_h2k": 187.0, "baseloads_elec_GJ_h2k": 25.0},
        {"hot_water_usage_Lperday": 0.005, "baseloads_elec_GJ": 0.02},
        "example.h2k",
    )
    assert failures == []


def test_assert_operating_parity_fails_when_out_of_tolerance():
    failures = assert_operating_parity(
        {
            "hot_water_usage_Lperday_h2k": 187.0,
            "hot_water_usage_Lperday_hpxml": 180.0,
            "baseloads_elec_GJ_h2k": 25.0,
            "baseloads_elec_GJ_hpxml": 25.0,
        },
        {"hot_water_usage_Lperday_h2k": 187.0, "baseloads_elec_GJ_h2k": 25.0},
        {"hot_water_usage_Lperday": 0.005, "baseloads_elec_GJ": 0.02},
        "example.h2k",
    )
    assert len(failures) == 1
    assert "hot_water_usage_Lperday" in failures[0]
