"""
SOC operating-condition parity tests (H2K vs OpenStudio-HPXML simulation).

Validates that translated HPXML models produce baseload electricity and hot water
use close to H2K SOC results for the curated ``tests/fixtures/soc_operating/`` corpus.

These tests are **opt-in** — they require OpenStudio-HPXML, run a full simulation per
file, and are intended for major operating-condition changes (not every CI run).

Run explicitly:

    pytest tests/integration/test_operating_parity.py --run-operating-parity -v
"""

from __future__ import annotations

import shutil
import uuid

import pytest

from tests.utils.operating_parity_utils import (
    H2K_DIR,
    assert_operating_parity,
    list_soc_operating_cases,
    load_expectations,
    run_operating_parity_compare,
)


def _case_ids(case_pair):
    return case_pair[0]


@pytest.fixture(scope="module")
def hpxml_os_path():
    from h2k_hpxml.utils.dependencies import get_hpxml_os_path

    path = get_hpxml_os_path()
    if not path:
        pytest.skip("OpenStudio-HPXML not installed")
    return path


@pytest.mark.operating_parity
@pytest.mark.integration
@pytest.mark.parametrize("case_info", list_soc_operating_cases(), ids=_case_ids)
def test_soc_operating_parity(case_info, check_openstudio_bindings, hpxml_os_path):
    """Compare baseload electricity and hot water vs H2K SOC reference values."""
    h2k_filename, case_expectations = case_info
    expectations = load_expectations()
    defaults = expectations["default_max_rel_error"]

    h2k_path = H2K_DIR / h2k_filename
    work_subdir = f"workflow/soc_operating_tests/{uuid.uuid4().hex[:12]}"
    work_path = hpxml_os_path / work_subdir

    try:
        compare_dict = run_operating_parity_compare(h2k_path, hpxml_os_path, work_subdir)
        failures = assert_operating_parity(
            compare_dict, case_expectations, defaults, h2k_filename
        )
        assert not failures, "\n".join(failures)
    finally:
        if work_path.exists():
            shutil.rmtree(work_path, ignore_errors=True)
