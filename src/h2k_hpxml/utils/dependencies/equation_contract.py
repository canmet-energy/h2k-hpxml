"""Verify mirrored OS-HPXML equations against installed workflow sources.

Used by pytest contract tests when upgrading OpenStudio-HPXML. Compares numeric
literals in OS Ruby sources to a pinned manifest and runs Python oracle vectors.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from dataclasses import field
from importlib import resources
from pathlib import Path
from typing import Any

from osdep.validators import detect_hpxml_version

from ...core.model import ModelData
from . import load_dependency_config


@dataclass
class ContractIssue:
    contract_id: str
    kind: str
    message: str


@dataclass
class ContractReport:
    pinned_version: str
    installed_version: str | None
    hpxml_path: Path | None
    issues: list[ContractIssue] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def summary_lines(self) -> list[str]:
        lines = [
            "OS-HPXML equation contract",
            f"  Pinned:    {self.pinned_version}",
            f"  Installed: {self.installed_version or 'unknown'}",
        ]
        if self.hpxml_path:
            lines.append(f"  Path:      {self.hpxml_path}")
        for item in self.passed:
            lines.append(f"  OK  {item}")
        for issue in self.issues:
            lines.append(f"  FAIL [{issue.contract_id}] {issue.message}")
        return lines


def normalize_hpxml_version(version: str | None) -> str | None:
    if not version:
        return None
    cleaned = version.strip()
    if cleaned.lower().startswith("v"):
        cleaned = cleaned[1:]
    match = re.search(r"(\d+\.\d+\.\d+)", cleaned)
    return match.group(1) if match else cleaned


def detect_hpxml_version_from_path(hpxml_path: Path) -> str | None:
    folder_match = re.search(r"v(\d+\.\d+\.\d+)", hpxml_path.name, re.IGNORECASE)
    if folder_match:
        return folder_match.group(1)

    return normalize_hpxml_version(detect_hpxml_version(hpxml_path))


def load_equation_contract() -> dict[str, Any]:
    with resources.files("h2k_hpxml.resources").joinpath(
        "os_hpxml_equation_contract.json"
    ).open(encoding="utf-8") as contract_file:
        return json.load(contract_file)


def _constant_pattern(constant: str) -> re.Pattern[str]:
    escaped = re.escape(constant)
    if constant.startswith("-"):
        return re.compile(rf"{escaped}\b")
    return re.compile(rf"(?<![\d.]){escaped}\b")


def source_contains_constant(source_text: str, constant: str) -> bool:
    return _constant_pattern(constant).search(source_text) is not None


def verify_source_constants(
    contract_id: str, os_source_path: Path, tracked_constants: list[str]
) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    if not os_source_path.is_file():
        issues.append(
            ContractIssue(
                contract_id,
                "missing_file",
                f"OS source not found: {os_source_path}",
            )
        )
        return issues

    source_text = os_source_path.read_text(encoding="utf-8", errors="replace")
    for constant in tracked_constants:
        if not source_contains_constant(source_text, constant):
            issues.append(
                ContractIssue(
                    contract_id,
                    "constant",
                    f"Constant {constant!r} not found in {os_source_path.name}",
                )
            )
    return issues


def _resolve_callable(function_path: str):
    module_name, function_name = function_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def run_oracle_test(oracle: dict[str, Any]) -> tuple[Any, list[ContractIssue]]:
    contract_id = oracle.get("contract_id", oracle["id"])
    function = _resolve_callable(oracle["function"])
    args = oracle.get("args", [])
    kwargs = dict(oracle.get("kwargs", {}))

    if "model_data_details" in oracle:
        model_data = ModelData()
        model_data.set_building_details(oracle["model_data_details"])
        result = function(model_data)
    else:
        result = function(*args, **kwargs)

    issues: list[ContractIssue] = []
    expected = oracle["expected"]
    rel_tol = oracle.get("rel_tol", 1e-9)
    abs_tol = oracle.get("abs_tol", 1e-9)
    if not _values_close(result, expected, rel_tol, abs_tol):
        issues.append(
            ContractIssue(
                contract_id,
                "oracle",
                (
                    f"Oracle {oracle['id']}: expected {expected}, got {result} "
                    f"(function {oracle['function']})"
                ),
            )
        )
    return result, issues


def _values_close(actual: Any, expected: Any, rel_tol: float, abs_tol: float) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= max(
            abs_tol, rel_tol * abs(float(expected))
        )
    except (TypeError, ValueError):
        return actual == expected


def verify_equation_contract(hpxml_path: Path | str | None = None) -> ContractReport:
    """Compare pinned equation manifest against an OS-HPXML install and Python oracles."""
    contract = load_equation_contract()
    dep_config = load_dependency_config()
    pinned_version = normalize_hpxml_version(contract["openstudio_hpxml_version"])
    pinned_dep_version = normalize_hpxml_version(dep_config["openstudio_hpxml_version"])

    report = ContractReport(
        pinned_version=contract["openstudio_hpxml_version"],
        installed_version=None,
        hpxml_path=None,
    )

    if pinned_version != pinned_dep_version:
        report.issues.append(
            ContractIssue(
                "_manifest",
                "version",
                (
                    f"Contract manifest targets {contract['openstudio_hpxml_version']} but "
                    f"dependency_versions.json pins {dep_config['openstudio_hpxml_version']}"
                ),
            )
        )

    resolved_path = _resolve_hpxml_path(hpxml_path)
    if resolved_path is None:
        report.issues.append(
            ContractIssue(
                "_install",
                "missing_install",
                "OpenStudio-HPXML installation not found; cannot scan OS sources",
            )
        )
    else:
        report.hpxml_path = resolved_path
        report.installed_version = detect_hpxml_version_from_path(resolved_path)
        if (
            pinned_version
            and report.installed_version
            and pinned_version != report.installed_version
        ):
            report.issues.append(
                ContractIssue(
                    "_version",
                    "version",
                    (
                        f"Installed OS-HPXML v{report.installed_version} differs from "
                        f"pinned {contract['openstudio_hpxml_version']}"
                    ),
                )
            )

        for entry in contract["contracts"]:
            os_source = resolved_path / entry["os_source"]
            constant_issues = verify_source_constants(
                entry["id"], os_source, entry["tracked_constants"]
            )
            report.issues.extend(constant_issues)
            if not constant_issues:
                report.passed.append(f"{entry['id']} constants")

    for oracle in contract["oracle_tests"]:
        _, oracle_issues = run_oracle_test(oracle)
        report.issues.extend(oracle_issues)
        if not oracle_issues:
            report.passed.append(f"oracle:{oracle['id']}")

    return report


def _resolve_hpxml_path(hpxml_path: Path | str | None) -> Path | None:
    if hpxml_path is not None:
        path = Path(hpxml_path)
        return path if path.exists() else None

    from . import get_hpxml_os_path

    detected = get_hpxml_os_path()
    return Path(detected) if detected else None
