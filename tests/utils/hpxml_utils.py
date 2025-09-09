"""
HPXML comparison and validation utilities.

This module provides functions for:
- Extracting key elements from HPXML files
- Comparing HPXML files for differences
- Normalizing HPXML content for consistent comparison
- Validating HPXML file structure and content
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from difflib import unified_diff
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


def normalize_paths_for_comparison(xml_content: str) -> str:
    """
    Normalize file paths in XML content for cross-platform comparison.

    This function standardizes OpenStudio-HPXML paths to remove platform-specific
    differences like drive letters (C:/) and mixed path separators, and normalizes
    workspace directory naming differences.

    Args:
        xml_content: Raw XML content as string

    Returns:
        XML content with normalized paths
    """
    # First, normalize all backslashes to forward slashes for consistency
    normalized_content = xml_content.replace("\\", "/")

    # Replace Windows-style OpenStudio-HPXML paths with standard format
    # Pattern matches: C:/OpenStudio-HPXML/... or D:/OpenStudio-HPXML/...
    normalized_content = re.sub(
        r"[A-Z]:/OpenStudio-HPXML/", "/OpenStudio-HPXML/", normalized_content
    )

    # Normalize workspace directory paths that may vary between environments
    # Pattern matches: /workspaces/h2k-hpxml/ or /workspaces/h2k_hpxml/
    normalized_content = re.sub(
        r"/workspaces/h2k[-_]hpxml/", "/workspaces/h2k_hpxml/", normalized_content
    )

    # Normalize weather file paths to just basename - this is the key fix for cross-environment testing
    # Pattern matches any path ending with OpenStudio-HPXML/weather/filename
    # Examples:
    #   /app/deps/OpenStudio-HPXML/weather/CAN_ON_Ottawa.Intl.AP.716280_CWEC2020.epw
    #   /workspaces/h2k-hpxml/src/h2k_hpxml/_deps/OpenStudio-HPXML/weather/file.epw
    #   C:/OpenStudio-HPXML/weather/file.epw
    # All become: WEATHER_FILE/filename
    normalized_content = re.sub(
        r"[^<>]*OpenStudio-HPXML/weather/([^<>/]+)", r"WEATHER_FILE/\1", normalized_content
    )

    return normalized_content


def extract_hpxml_key_elements(hpxml_path: str) -> Dict[str, Any]:
    """
    Extract key elements from HPXML file for comparison.

    Returns structured data about building characteristics,
    systems, and key parameters that should remain consistent.

    Args:
        hpxml_path: Path to HPXML file

    Returns:
        Dictionary containing extracted key elements
    """
    try:
        tree = ET.parse(hpxml_path)
        root = tree.getroot()

        # Get namespace if present
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"

        # Extract key building characteristics
        extracted_data = {
            "building_info": {},
            "enclosure": {},
            "systems": {},
            "climate": {},
            "validation": {},
        }

        # Building info
        building = root.find(f".//{namespace}Building")
        if building is not None:
            building_details = building.find(f".//{namespace}BuildingDetails")
            site = building.find(f".//{namespace}Site")

            extracted_data["building_info"] = {
                "site_type": (
                    site.find(f".//{namespace}SiteType").text
                    if site is not None and site.find(f".//{namespace}SiteType") is not None
                    else None
                ),
                "building_type": (
                    building_details.find(f".//{namespace}BuildingType").text
                    if building_details is not None
                    and building_details.find(f".//{namespace}BuildingType") is not None
                    else None
                ),
                "conditioned_floor_area": (
                    building_details.find(f".//{namespace}ConditionedFloorArea").text
                    if building_details is not None
                    and building_details.find(f".//{namespace}ConditionedFloorArea") is not None
                    else None
                ),
                "conditioned_building_volume": (
                    building_details.find(f".//{namespace}ConditionedBuildingVolume").text
                    if building_details is not None
                    and building_details.find(f".//{namespace}ConditionedBuildingVolume")
                    is not None
                    else None
                ),
                "number_of_bedrooms": (
                    building_details.find(f".//{namespace}NumberofBedrooms").text
                    if building_details is not None
                    and building_details.find(f".//{namespace}NumberofBedrooms") is not None
                    else None
                ),
                "number_of_bathrooms": (
                    building_details.find(f".//{namespace}NumberofBathrooms").text
                    if building_details is not None
                    and building_details.find(f".//{namespace}NumberofBathrooms") is not None
                    else None
                ),
            }

        # Enclosure components (walls, windows, doors, etc.)
        enclosure_elements = ["Wall", "Window", "Door", "Floor", "Slab", "Ceiling", "Roof"]
        for element in enclosure_elements:
            elements = root.findall(f".//{namespace}{element}")
            if elements:
                extracted_data["enclosure"][element.lower() + "s"] = len(elements)

        # HVAC Systems
        hvac_systems = ["HeatingSystem", "CoolingSystem", "HeatPump", "HVACDistribution"]
        for system in hvac_systems:
            systems = root.findall(f".//{namespace}{system}")
            if systems:
                extracted_data["systems"][system.lower() + "s"] = len(systems)

        # Hot Water Systems
        hw_systems = root.findall(f".//{namespace}WaterHeatingSystem")
        if hw_systems:
            extracted_data["systems"]["water_heating_systems"] = len(hw_systems)

        # Ventilation Systems
        vent_systems = root.findall(f".//{namespace}VentilationFan")
        if vent_systems:
            extracted_data["systems"]["ventilation_fans"] = len(vent_systems)

        # Climate/Weather
        climate_elem = root.find(f".//{namespace}Climate")
        if climate_elem is not None:
            weather_station = climate_elem.find(f".//{namespace}WeatherStation")
            extracted_data["climate"] = {
                "weather_station_name": (
                    weather_station.find(f".//{namespace}Name").text
                    if weather_station is not None
                    and weather_station.find(f".//{namespace}Name") is not None
                    else None
                ),
                "weather_station_wmo": (
                    weather_station.find(f".//{namespace}WMO").text
                    if weather_station is not None
                    and weather_station.find(f".//{namespace}WMO") is not None
                    else None
                ),
            }

        # Simulation Control Settings
        sim_control = root.find(f".//{namespace}SimulationControl")
        if sim_control is not None:
            timestep_elem = sim_control.find(f".//{namespace}Timestep")
            extracted_data["simulation_control"] = {
                "timestep": timestep_elem.text if timestep_elem is not None else None,
            }

        # Add file validation info
        extracted_data["validation"] = {
            "file_size": os.path.getsize(hpxml_path),
            "root_element": root.tag,
            "namespace": root.attrib.get("xmlns") if "xmlns" in root.attrib else None,
            "total_elements": len(root.findall(".//*")),
        }

        return extracted_data

    except Exception as e:
        return {"error": f"Failed to parse HPXML: {str(e)}"}


def normalize_hpxml_for_comparison(hpxml_path: str) -> str:
    """
    Normalize HPXML file for comparison by removing timestamps and
    other volatile elements that may change between runs.

    Args:
        hpxml_path: Path to HPXML file

    Returns:
        Normalized HPXML content as string
    """
    try:
        tree = ET.parse(hpxml_path)
        root = tree.getroot()

        # Get namespace if present
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"

        # Remove or normalize timestamp elements
        for timestamp_elem in root.findall(f".//{namespace}Timestamp"):
            timestamp_elem.text = "NORMALIZED_TIMESTAMP"

        # Remove software version info that might change
        for software_elem in root.findall(f".//{namespace}SoftwareInfo"):
            version_elem = software_elem.find(f"{namespace}Version")
            if version_elem is not None:
                version_elem.text = "NORMALIZED_VERSION"

        # Remove transaction elements that contain timestamps
        for transaction_elem in root.findall(f".//{namespace}Transaction"):
            created_elem = transaction_elem.find(f"{namespace}CreatedDateAndTime")
            if created_elem is not None:
                created_elem.text = "NORMALIZED_DATETIME"

        # Sort elements for consistent comparison (if needed)
        # This depends on HPXML structure and what elements can be reordered

        # Convert to string and normalize paths for cross-platform compatibility
        xml_content = ET.tostring(root, encoding="unicode")
        normalized_content = normalize_paths_for_comparison(xml_content)

        return normalized_content

    except Exception as e:
        return f"Error normalizing HPXML: {str(e)}"


def compare_hpxml_files(baseline_path: str, comparison_path: str) -> Dict[str, Any]:
    """
    Compare two HPXML files comprehensively and return differences.

    This function performs a complete comparison of HPXML files, detecting ANY changes
    in the XML structure, content, or formatting. It normalizes both files to remove
    volatile elements (like timestamps) but otherwise expects exact matches.

    Args:
        baseline_path: Path to baseline HPXML file
        comparison_path: Path to comparison HPXML file

    Returns:
        Dictionary containing comparison results
    """
    result = {
        "files_match": False,
        "differences": [],
        "baseline_data": {},
        "comparison_data": {},
        "summary": {},
    }

    try:
        # Check if files exist
        if not os.path.exists(baseline_path):
            result["error"] = f"Baseline file not found: {baseline_path}"
            return result

        if not os.path.exists(comparison_path):
            result["error"] = f"Comparison file not found: {comparison_path}"
            return result

        # Get normalized content for both files
        baseline_normalized = normalize_hpxml_for_comparison(baseline_path)
        comparison_normalized = normalize_hpxml_for_comparison(comparison_path)

        # Check for normalization errors
        if baseline_normalized.startswith("Error normalizing"):
            result["error"] = baseline_normalized
            return result

        if comparison_normalized.startswith("Error normalizing"):
            result["error"] = comparison_normalized
            return result

        # Check if files are identical after normalization
        files_match = baseline_normalized == comparison_normalized

        differences = []

        if not files_match:
            # Generate detailed differences using unified diff
            diff_lines = list(
                unified_diff(
                    baseline_normalized.splitlines(keepends=True),
                    comparison_normalized.splitlines(keepends=True),
                    fromfile="baseline",
                    tofile="comparison",
                    lineterm="",
                )
            )

            # Extract meaningful differences (skip diff headers)
            meaningful_diffs = []
            for line in diff_lines:
                if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                    continue
                if line.startswith("-") or line.startswith("+"):
                    meaningful_diffs.append(line.strip())

            # Limit number of differences shown to avoid overwhelming output
            if len(meaningful_diffs) > 20:
                differences = meaningful_diffs[:20] + [
                    f"... and {len(meaningful_diffs) - 20} more differences"
                ]
            else:
                differences = meaningful_diffs

            # If no meaningful differences found, indicate files differ but in subtle ways
            if not differences:
                differences = [
                    "Files differ but differences are subtle (whitespace, formatting, etc.)"
                ]

        # Extract key elements for summary information
        baseline_data = extract_hpxml_key_elements(baseline_path)
        comparison_data = extract_hpxml_key_elements(comparison_path)

        result["files_match"] = files_match
        result["differences"] = differences
        result["baseline_data"] = baseline_data
        result["comparison_data"] = comparison_data
        result["summary"] = {
            "total_differences": len(differences),
            "baseline_elements": baseline_data.get("validation", {}).get("total_elements", 0),
            "comparison_elements": comparison_data.get("validation", {}).get("total_elements", 0),
            "baseline_file_size": baseline_data.get("validation", {}).get("file_size", 0),
            "comparison_file_size": comparison_data.get("validation", {}).get("file_size", 0),
        }

    except Exception as e:
        result["error"] = str(e)

    return result


def validate_hpxml_structure(hpxml_path: str) -> Dict[str, Any]:
    """
    Validate HPXML file structure and content.

    Args:
        hpxml_path: Path to HPXML file

    Returns:
        Dictionary containing validation results
    """
    validation_result = {"is_valid": False, "errors": [], "warnings": [], "structure_info": {}}

    try:
        tree = ET.parse(hpxml_path)
        root = tree.getroot()

        # Get namespace if present
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"

        # Check for HPXML namespace
        if "http://hpxmlonline.com" not in str(root.tag):
            validation_result["warnings"].append("HPXML namespace not found in root element")

        # Check for required top-level elements
        required_elements = ["XMLTransactionHeaderInformation", "Building"]
        for element in required_elements:
            if root.find(f".//{namespace}{element}") is None:
                validation_result["errors"].append(f"Required element missing: {element}")

        # Check for Building elements
        building = root.find(f".//{namespace}Building")
        if building is not None:
            # Check for required Building sub-elements
            required_building_elements = ["BuildingDetails", "Site"]
            for element in required_building_elements:
                if building.find(f".//{namespace}{element}") is None:
                    validation_result["warnings"].append(
                        f"Recommended Building element missing: {element}"
                    )

        # Structure information
        validation_result["structure_info"] = {
            "root_element": root.tag,
            "total_elements": len(root.findall(".//*")),
            "file_size_bytes": os.path.getsize(hpxml_path),
            "has_building": root.find(f".//{namespace}Building") is not None,
            "has_climate": root.find(f".//{namespace}Climate") is not None,
            "has_enclosure": any(
                root.findall(f".//{namespace}{elem}") for elem in ["Wall", "Window", "Door"]
            ),
            "has_systems": any(
                root.findall(f".//{namespace}{elem}")
                for elem in ["HeatingSystem", "CoolingSystem", "WaterHeatingSystem"]
            ),
        }

        # Set validity based on errors
        validation_result["is_valid"] = len(validation_result["errors"]) == 0

    except ET.ParseError as e:
        validation_result["errors"].append(f"XML parsing error: {str(e)}")
    except Exception as e:
        validation_result["errors"].append(f"Validation error: {str(e)}")

    return validation_result


def create_hpxml_summary(hpxml_files: List[str]) -> Dict[str, Any]:
    """
    Create a summary of multiple HPXML files.

    Args:
        hpxml_files: List of HPXML file paths

    Returns:
        Dictionary containing summary information
    """
    summary = {"total_files": len(hpxml_files), "valid_files": 0, "invalid_files": 0, "files": {}}

    for hpxml_file in hpxml_files:
        base_name = os.path.splitext(os.path.basename(hpxml_file))[0]

        # Extract key elements
        extracted_data = extract_hpxml_key_elements(hpxml_file)

        # Validate structure
        validation_result = validate_hpxml_structure(hpxml_file)

        summary["files"][base_name] = {
            "file_path": hpxml_file,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "structure_info": validation_result.get("structure_info", {}),
            "key_elements": extracted_data,
        }

        if validation_result["is_valid"]:
            summary["valid_files"] += 1
        else:
            summary["invalid_files"] += 1

    return summary
