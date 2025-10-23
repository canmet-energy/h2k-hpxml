# Utility functions related to H2k mapping
import json
import os

from ..utils import units
from . import data_utils as obj


def _load_resource_json(resource_name):
    """
    Load a JSON resource file using multiple strategies for compatibility.

    Args:
        resource_name: Name of the JSON file in the resources folder

    Returns:
        dict: Parsed JSON content

    Raises:
        RuntimeError: If the resource cannot be loaded
    """
    json_content = None

    # Strategy 1: Try importlib.resources (Python 3.7+, works with installed packages)
    try:
        from importlib import resources

        try:
            with resources.open_text("h2k_hpxml.resources", resource_name) as f:
                json_content = json.load(f)
        except (FileNotFoundError, ImportError, AttributeError):
            pass
    except ImportError:
        pass

    # Strategy 2: Try pkg_resources for pip installations
    if json_content is None:
        try:
            import pkg_resources

            resource_path = pkg_resources.resource_filename(
                "h2k_hpxml", f"resources/{resource_name}"
            )
            if os.path.exists(resource_path):
                with open(resource_path, encoding="utf-8") as f:
                    json_content = json.load(f)
        except (ImportError, FileNotFoundError):
            pass

    # Strategy 3: Fallback to relative path (for development)
    if json_content is None:
        resources_folder = os.path.join(os.path.dirname(__file__), "..", "resources")
        resource_path = os.path.join(resources_folder, resource_name)
        if os.path.exists(resource_path):
            try:
                with open(resource_path, encoding="utf-8") as f:
                    json_content = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                raise RuntimeError(f"Failed to load resource {resource_name}: {e}")

    if json_content is None:
        raise RuntimeError(
            f"Resource file '{resource_name}' not found. Tried:\n"
            "1. importlib.resources (package installation)\n"
            "2. pkg_resources (pip installation)\n"
            "3. Relative path (development mode)"
        )

    return json_content


# Load configuration files at module level
selection_config = _load_resource_json("config_selection.json")
numeric_config = _load_resource_json("config_numeric.json")
foundation_config = _load_resource_json("config_foundations.json")


def get_selection_field(h2k_dict=None, field_key=""):
    if h2k_dict is None:
        h2k_dict = {}

    if field_key not in selection_config.keys():
        print("field key not found " + field_key)
        return None

    h2k_address = selection_config[field_key]["address"]["h2k"]
    default_val = selection_config[field_key]["default"]
    selection_map = selection_config[field_key]["map"]

    h2k_val = obj.get_val(h2k_dict, h2k_address)

    if not isinstance(h2k_val, str):
        # kick out early if we didn't reach the bottom level of the object for some reason
        # This would indicate either a problem with the address or the field isn't always present
        return default_val

    return selection_map.get(h2k_val, default_val)


def get_number_field(h2k_dict=None, field_key=""):
    if h2k_dict is None:
        h2k_dict = {}

    if field_key not in numeric_config.keys():
        print("field key not found " + field_key)
        return None

    h2k_address = numeric_config[field_key]["address"]["h2k"]

    decimals = numeric_config[field_key]["decimals"]

    unit_type = numeric_config[field_key].get("units", {}).get("unit_type", None)
    h2k_units = numeric_config[field_key].get("units", {}).get("h2k_units", None)
    hpxml_units = numeric_config[field_key].get("units", {}).get("hpxml_units", None)

    value = obj.get_val(h2k_dict, h2k_address)

    if isinstance(value, dict):
        return 0

    h2k_val = float(value) if decimals > 0 else int(value)

    if None in [unit_type, h2k_units, hpxml_units]:
        return h2k_val

    return round(units.convert_unit(h2k_val, unit_type, h2k_units, hpxml_units), decimals)


def get_composite_rval(composite_dict, wall_core="C"):
    # wall_core = 0.116 RSI for concrete, 0.417 RSI for wood, which is subtracted before the effective R-value is returned
    # this calculation aligns with h2k's calculation method
    wall_core_rval = 0.116 * 5.678 if wall_core == "C" else 0.417 * 5.678
    rval = 0.0

    section_list = composite_dict.get("Composite", {}).get("Section", [])

    if section_list == []:
        rval = get_number_field(composite_dict, "composite_nom_r_value")
    else:
        section_list = section_list if isinstance(section_list, list) else [section_list]
        percentage = 0.0
        totPercentage = 0.0
        sumQuotient = 0.0

        for section in section_list:
            if "@percentage" in section.keys():
                percentage = float(section["@percentage"])

            else:
                percentage = 100 - totPercentage

            totPercentage += percentage

            sumQuotient += percentage / ((float(section.get("@rsi", 0)) * 5.678) + wall_core_rval)

        rval = round((100 / sumQuotient) - wall_core_rval, 4)

    # We have to return like this because of how the math works out with an R-value of 0 and floating point numbers
    return abs(rval) if rval == -0.0 else rval


def get_foundation_config(key=""):
    return foundation_config.get(key, foundation_config)
