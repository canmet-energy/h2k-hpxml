"""
Comparison utilities for energy data validation and regression testing.

This module provides common functions for:
- Comparing energy data between baseline and current runs
- Calculating percentage differences with tolerance
- Generating comparison reports
- Handling missing or zero-value components
"""

import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


def calculate_percentage_difference(baseline_value: float, current_value: float) -> float:
    """
    Calculate percentage difference between baseline and current values.

    Args:
        baseline_value: The baseline reference value
        current_value: The current test value

    Returns:
        Percentage difference (positive means current > baseline)
    """
    if baseline_value == 0:
        if current_value == 0:
            return 0.0
        else:
            # If baseline is 0 but current isn't, that's a significant change
            return float("inf")

    return ((current_value - baseline_value) / abs(baseline_value)) * 100


def compare_energy_values(
    baseline_data: Dict[str, Any],
    current_data: Dict[str, Any],
    tolerance_percent: float = 5.0,
    path: str = "",
) -> List[Dict[str, Any]]:
    """
    Compare energy data structures recursively.

    Args:
        baseline_data: Baseline energy data
        current_data: Current energy data to compare
        tolerance_percent: Tolerance for percentage differences
        path: Current path in the data structure (for error reporting)

    Returns:
        List of comparison results
    """
    comparisons = []

    def compare_recursive(baseline: Any, current: Any, current_path: str) -> None:
        if isinstance(baseline, dict) and isinstance(current, dict):
            # Handle dictionaries
            if "value" in baseline and "value" in current:
                # This is a leaf node with actual values
                baseline_val = float(baseline["value"])
                current_val = float(current["value"])

                # Calculate percentage difference
                pct_diff = calculate_percentage_difference(baseline_val, current_val)

                # Determine if within tolerance
                passed = abs(pct_diff) <= tolerance_percent or (
                    baseline_val == 0 and current_val == 0
                )

                comparison = {
                    "path": current_path,
                    "baseline_value": baseline_val,
                    "current_value": current_val,
                    "percentage_difference": pct_diff,
                    "tolerance_percent": tolerance_percent,
                    "passed": passed,
                    "units": baseline.get("units", current.get("units", "unknown")),
                }
                comparisons.append(comparison)

            else:
                # Recurse into nested dictionaries
                all_keys = set(baseline.keys()) | set(current.keys())
                for key in all_keys:
                    new_path = f"{current_path}.{key}" if current_path else key

                    if key in baseline and key in current:
                        compare_recursive(baseline[key], current[key], new_path)
                    elif key in baseline and key not in current:
                        # Missing in current data
                        if isinstance(baseline[key], dict) and "value" in baseline[key]:
                            baseline_val = float(baseline[key]["value"])
                            # Only flag as missing if baseline value is significant
                            if baseline_val > 0:
                                comparison = {
                                    "path": new_path,
                                    "baseline_value": baseline_val,
                                    "current_value": 0.0,
                                    "percentage_difference": -100.0,
                                    "tolerance_percent": tolerance_percent,
                                    "passed": False,
                                    "units": baseline[key].get("units", "unknown"),
                                    "note": "Missing in current data",
                                }
                                comparisons.append(comparison)
                    elif key not in baseline and key in current:
                        # New in current data
                        if isinstance(current[key], dict) and "value" in current[key]:
                            current_val = float(current[key]["value"])
                            comparison = {
                                "path": new_path,
                                "baseline_value": 0.0,
                                "current_value": current_val,
                                "percentage_difference": float("inf") if current_val > 0 else 0.0,
                                "tolerance_percent": tolerance_percent,
                                "passed": current_val == 0,  # New zero values are OK
                                "units": current[key].get("units", "unknown"),
                                "note": "New in current data",
                            }
                            comparisons.append(comparison)

    compare_recursive(baseline_data, current_data, path)
    return comparisons


def generate_comparison_summary(comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of comparison results.

    Args:
        comparisons: List of individual comparison results

    Returns:
        Summary dictionary with statistics
    """
    total_comparisons = len(comparisons)
    passed_comparisons = sum(1 for c in comparisons if c["passed"])
    failed_comparisons = total_comparisons - passed_comparisons

    # Group failures by type
    missing_components = [c for c in comparisons if c.get("note") == "Missing in current data"]
    new_components = [c for c in comparisons if c.get("note") == "New in current data"]
    tolerance_failures = [c for c in comparisons if not c["passed"] and "note" not in c]

    # Calculate statistics
    if total_comparisons > 0:
        pass_rate = (passed_comparisons / total_comparisons) * 100
    else:
        pass_rate = 0.0

    # Find worst differences
    significant_failures = [
        c for c in tolerance_failures if abs(c.get("percentage_difference", 0)) > 10
    ]

    summary = {
        "total_comparisons": total_comparisons,
        "passed_comparisons": passed_comparisons,
        "failed_comparisons": failed_comparisons,
        "pass_rate_percent": round(pass_rate, 2),
        "failure_breakdown": {
            "tolerance_failures": len(tolerance_failures),
            "missing_components": len(missing_components),
            "new_components": len(new_components),
        },
        "significant_failures": len(significant_failures),
        "worst_differences": sorted(
            [
                c
                for c in comparisons
                if not c["passed"] and abs(c.get("percentage_difference", 0)) != float("inf")
            ],
            key=lambda x: abs(x.get("percentage_difference", 0)),
            reverse=True,
        )[
            :5
        ],  # Top 5 worst differences
    }

    return summary


def format_comparison_report(
    file_name: str, comparisons: List[Dict[str, Any]], summary: Dict[str, Any]
) -> str:
    """
    Format a human-readable comparison report.

    Args:
        file_name: Name of the file being compared
        comparisons: List of comparison results
        summary: Summary statistics

    Returns:
        Formatted report string
    """
    report_lines = [
        f"# Energy Comparison Report: {file_name}",
        f"Generated: {json.dumps({'timestamp': 'now'})}",
        "",
        "## Summary",
        f"- Total Comparisons: {summary['total_comparisons']}",
        f"- Passed: {summary['passed_comparisons']} ({summary['pass_rate_percent']}%)",
        f"- Failed: {summary['failed_comparisons']}",
        "",
        "## Failure Breakdown",
        f"- Tolerance Failures: {summary['failure_breakdown']['tolerance_failures']}",
        f"- Missing Components: {summary['failure_breakdown']['missing_components']}",
        f"- New Components: {summary['failure_breakdown']['new_components']}",
        "",
    ]

    # Add details for significant failures
    if summary["worst_differences"]:
        report_lines.extend(["## Worst Differences", ""])

        for diff in summary["worst_differences"]:
            report_lines.append(
                f"- {diff['path']}: {diff['percentage_difference']:.1f}% "
                f"(baseline: {diff['baseline_value']}, current: {diff['current_value']})"
            )

        report_lines.append("")

    # Add details for missing components
    missing_components = [c for c in comparisons if c.get("note") == "Missing in current data"]
    if missing_components:
        report_lines.extend(["## Missing Components", ""])

        for comp in missing_components[:10]:  # Limit to first 10
            report_lines.append(f"- {comp['path']}: {comp['baseline_value']} {comp['units']}")

        if len(missing_components) > 10:
            report_lines.append(f"... and {len(missing_components) - 10} more")

        report_lines.append("")

    return "\n".join(report_lines)


def validate_comparison_data(
    baseline_data: Dict[str, Any], current_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate that comparison data is suitable for comparison.

    Args:
        baseline_data: Baseline energy data
        current_data: Current energy data

    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not baseline_data:
        return False, "Baseline data is empty"

    if not current_data:
        return False, "Current data is empty"

    # Count energy values in each dataset
    def count_values(data):
        count = 0

        def count_recursive(d):
            nonlocal count
            if isinstance(d, dict):
                if "value" in d:
                    count += 1
                else:
                    for v in d.values():
                        count_recursive(v)

        count_recursive(data)
        return count

    baseline_count = count_values(baseline_data)
    current_count = count_values(current_data)

    if baseline_count == 0:
        return False, "No baseline values found for comparison"

    if current_count == 0:
        return False, "No current values found for comparison"

    # Check if the counts are reasonably similar (within 50% difference)
    count_diff_pct = abs(baseline_count - current_count) / baseline_count * 100
    if count_diff_pct > 50:
        return (
            False,
            f"Data structure mismatch: baseline has {baseline_count} values, current has {current_count} ({count_diff_pct:.1f}% difference)",
        )

    return (
        True,
        f"Validation passed: {baseline_count} baseline values, {current_count} current values",
    )


def filter_comparisons_by_tolerance(
    comparisons: List[Dict[str, Any]], tolerance_percent: float
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter comparisons into passed and failed based on tolerance.

    Args:
        comparisons: List of comparison results
        tolerance_percent: Tolerance threshold

    Returns:
        Tuple of (passed_comparisons, failed_comparisons)
    """
    passed = []
    failed = []

    for comparison in comparisons:
        if comparison["passed"]:
            passed.append(comparison)
        else:
            failed.append(comparison)

    return passed, failed
