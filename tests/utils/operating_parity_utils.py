"""Helpers for SOC operating-condition parity tests (H2K vs OpenStudio-HPXML)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from h2k_hpxml.analysis import annual
from h2k_hpxml.config.translation_config import build_translation_config
from h2k_hpxml.core.translator import h2ktohpxml

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "soc_operating"
H2K_DIR = FIXTURES_DIR / "h2k"
EXPECTATIONS_PATH = FIXTURES_DIR / "expectations.json"

PARITY_METRICS = (
    "hot_water_usage_Lperday",
    "baseloads_elec_GJ",
)


def load_expectations() -> dict[str, Any]:
    return json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))


def list_soc_operating_cases() -> list[tuple[str, dict[str, Any]]]:
    """Return (h2k_filename, case_expectations) pairs that have fixture files on disk."""
    expectations = load_expectations()
    cases = []
    for filename, case_data in expectations["cases"].items():
        h2k_path = H2K_DIR / filename
        if h2k_path.is_file():
            cases.append((filename, case_data))
    return cases


def _hpxml_filename(h2k_filename: str) -> str:
    return h2k_filename.replace(".h2k", ".xml").replace(".H2K", ".xml").replace(" ", "-")


def run_operating_parity_compare(
    h2k_path: Path,
    hpxml_os_path: Path,
    work_subdir: str,
    translation_mode: str = "STANDARD",
) -> dict[str, Any]:
    """
    Translate one H2K file, simulate with OpenStudio-HPXML, and return flattened compare dict.

    work_subdir is relative to the OS-HPXML install root (e.g. workflow/soc_operating_tests/run1).
    """
    h2k_path = Path(h2k_path)
    h2k_string = h2k_path.read_text(encoding="utf-8")
    hpxml_string = h2ktohpxml(
        h2k_string,
        build_translation_config(
            overrides={
                "translation_mode": translation_mode,
                "operating_condition": "SOC",
            }
        ),
    )

    output_dir = hpxml_os_path / work_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    hpxml_filename = _hpxml_filename(h2k_path.name)
    hpxml_output_path = output_dir / hpxml_filename
    hpxml_output_path.write_text(hpxml_string, encoding="utf-8")

    sim_cmd = f"openstudio workflow/run_simulation.rb -x {work_subdir}/{hpxml_filename}"
    subprocess.run(
        sim_cmd,
        cwd=hpxml_os_path,
        check=True,
        shell=True,
    )

    os_results = annual.read_os_results(str(output_dir), return_type="dict")
    if not os_results or os_results.get("Energy Use: Total (MBtu)", 0) == 0:
        raise RuntimeError(f"OpenStudio simulation produced no results for {h2k_path.name}")

    h2k_results, weather_location, hot_water_load_lperday = annual.read_h2k_results(
        str(h2k_path), operating_conditions="SOC"
    )
    compare_dict = annual.compare_os_h2k_annual(h2k_results, os_results)
    compare_dict["location"] = weather_location
    compare_dict["hot_water_usage_Lperday_h2k"] = hot_water_load_lperday
    return compare_dict


def max_rel_error(reference: float, actual: float) -> float:
    if reference == 0:
        return 0.0 if actual == 0 else float("inf")
    return abs(actual - reference) / abs(reference)


def assert_operating_parity(
    compare_dict: dict[str, Any],
    case_expectations: dict[str, Any],
    defaults: dict[str, float],
    h2k_filename: str,
) -> list[str]:
    """Return list of failure messages (empty if all metrics pass)."""
    failures = []
    for metric in PARITY_METRICS:
        h2k_key = f"{metric}_h2k"
        hpxml_key = f"{metric}_hpxml"
        reference = case_expectations.get(h2k_key)
        if reference is None:
            reference = compare_dict.get(h2k_key)
        actual = compare_dict.get(hpxml_key)
        limit = case_expectations.get(f"{metric}_max_rel_error", defaults.get(metric))

        if actual is None:
            failures.append(f"{h2k_filename}: missing HPXML metric {hpxml_key}")
            continue
        if reference is None or limit is None:
            failures.append(f"{h2k_filename}: missing reference or tolerance for {metric}")
            continue

        error = max_rel_error(float(reference), float(actual))
        if error > limit:
            failures.append(
                f"{h2k_filename}: {metric} rel error {error:.4f} "
                f"(h2k={reference}, hpxml={actual}, max={limit})"
            )
    return failures
