"""Tests for OS-HPXML equation contract verification."""

from __future__ import annotations

import pytest

from h2k_hpxml.core.model import ModelData
from h2k_hpxml.utils.dependencies.equation_contract import (
    detect_hpxml_version_from_path,
    load_equation_contract,
    normalize_hpxml_version,
    run_oracle_test,
    source_contains_constant,
    verify_equation_contract,
    verify_source_constants,
)


def test_normalize_hpxml_version():
    assert normalize_hpxml_version("v1.9.1") == "1.9.1"
    assert normalize_hpxml_version("1.9.1") == "1.9.1"


def test_detect_hpxml_version_from_folder_name(tmp_path):
    install = tmp_path / "OpenStudio-HPXML-v1.9.1"
    install.mkdir()
    assert detect_hpxml_version_from_path(install) == "1.9.1"


def test_oracle_tests_in_manifest_match_python():
    contract = load_equation_contract()
    for oracle in contract["oracle_tests"]:
        _, issues = run_oracle_test(oracle)
        assert not issues, issues[0].message


def test_source_constant_scan_passes_with_matching_ruby(tmp_path):
    ruby_dir = tmp_path / "HPXMLtoOpenStudio" / "resources"
    ruby_dir.mkdir(parents=True)
    ruby_file = ruby_dir / "hotwater_appliances.rb"
    ruby_file.write_text(
        "ref_f_gpd = [-4.84 + 18.6 * n_occ, 0.0].max\n"
        "ref_w_gpd = 7.16 * (n_occ**0.7)\n"
        "o_frac = 0.25\n",
        encoding="utf-8",
    )

    issues = verify_source_constants(
        "fixtures_gpd_operational",
        ruby_file,
        ["-4.84", "18.6", "7.16", "0.25"],
    )
    assert issues == []


def test_source_constant_scan_fails_when_literal_drifts(tmp_path):
    ruby_dir = tmp_path / "HPXMLtoOpenStudio" / "resources"
    ruby_dir.mkdir(parents=True)
    ruby_file = ruby_dir / "hotwater_appliances.rb"
    ruby_file.write_text("ref_f_gpd = [-5.0 + 19.0 * n_occ, 0.0].max\n", encoding="utf-8")

    issues = verify_source_constants(
        "fixtures_gpd_operational",
        ruby_file,
        ["-4.84", "18.6"],
    )
    assert len(issues) == 2
    assert all(issue.kind == "constant" for issue in issues)


def test_verify_equation_contract_against_mock_install(tmp_path):
    install = tmp_path / "OpenStudio-HPXML-v1.12.0"
    resources = install / "HPXMLtoOpenStudio" / "resources"
    resources.mkdir(parents=True)

    hotwater = resources / "hotwater_appliances.rb"
    hotwater.write_text(
        "\n".join(
            [
                "ref_f_gpd = [-4.84 + 18.6 * n_occ, 0.0].max",
                "ref_w_gpd = 7.16 * (n_occ**0.7)",
                "o_frac = 0.25",
                "o_cd_eff = 0.0",
                "gas_h20 = 0.3914",
                "elec_h20 = 0.0178",
                "scy = 123.0 + 61.0 * n_occ",
                "acy = scy * ((3.0 * 2.08 + 1.59) / (capacity * 2.08 + 1.59))",
                "0.5497",
                "0.02504",
                "91.0 + 30.0",
                "105",
                "0.05",
            ]
        ),
        encoding="utf-8",
    )

    weather = resources / "weather.rb"
    weather.write_text(
        "tmains_ratio = 0.4 + 0.01 * (data.AnnualAvgDrybulb - 44)\n"
        "tmains_lag = 35 - (data.AnnualAvgDrybulb - 44)\n"
        "+ 6 + tmains_ratio * maxDiffMonthlyAvgOAT / 2 * Math.sin(deg_rad * (0.986 * (d - 15 - tmains_lag) + sign * 90))\n"
        "max(32.0, temp_f)\n",
        encoding="utf-8",
    )

    defaults = resources / "defaults.rb"
    defaults.write_text(
        "return -1.36 + 1.49 * n_occs\n"
        "return -1.98 + 1.89 * n_occs\n"
        "return -2.19 + 2.08 * n_occs\n"
        "return -1.26 + 1.61 * n_occs\n",
        encoding="utf-8",
    )

    (install / "workflow").mkdir()
    (install / "workflow" / "run_simulation.rb").write_text("# stub", encoding="utf-8")

    report = verify_equation_contract(install)
    assert report.installed_version == "1.12.0"
    assert report.ok, "\n".join(report.summary_lines())


@pytest.mark.integration
@pytest.mark.equation_contract
def test_equation_contract_matches_installed_openstudio_hpxml():
    """Run full contract against the local OS-HPXML install (skip if absent)."""
    import os
    from pathlib import Path

    from h2k_hpxml.utils.dependencies import get_hpxml_os_path

    if os.environ.get("H2K_SKIP_AUTO_INSTALL") == "1":
        pytest.skip("Skipped in CI (H2K_SKIP_AUTO_INSTALL=1)")

    hpxml_path = get_hpxml_os_path()
    if not hpxml_path or not Path(hpxml_path).is_dir():
        pytest.skip("OpenStudio-HPXML not installed")

    report = verify_equation_contract(hpxml_path)
    if not report.ok:
        pytest.fail("\n".join(report.summary_lines()))


def test_hot_to_mixed_ratio_oracle():
    contract = load_equation_contract()
    oracle = next(o for o in contract["oracle_tests"] if o["id"] == "hot_to_mixed_ratio_standard")
    _, issues = run_oracle_test(oracle)
    assert not issues

    model_data = ModelData()
    model_data.set_building_details(oracle["model_data_details"])
    from h2k_hpxml.utils.hot_water_usage import calc_hot_to_mixed_ratio

    assert calc_hot_to_mixed_ratio(model_data) == pytest.approx(oracle["expected"])


def test_source_contains_constant_handles_negative_literals():
    assert source_contains_constant("x = -4.84 + 18.6 * n", "-4.84")
    assert source_contains_constant("x = -4.84 + 18.6 * n", "18.6")
    assert not source_contains_constant("x = -5.0 + 18.6 * n", "-4.84")
