"""Refactored exposed floor components using common utilities."""

from typing import Any, Dict

from ..types import ComponentDict
from ..types import H2KDict
from ..utils import h2k
from ..utils.common import FacilityTypeHelper
from ..utils.common import ValidationHelper
from ..utils.common import extract_and_process_components


def _process_single_floor(floor: Dict[str, Any], floor_id: str, model_data: Any) -> ComponentDict:
    """
    Process a single H2K floor component to HPXML format.

    Args:
        floor: H2K floor component dictionary
        floor_id: Generated floor ID
        model_data: Model data object for storing information

    Returns:
        HPXML floor component dictionary
    """
    # Get component label and basic properties
    floor_label = ValidationHelper.get_component_label(floor)

    # Extract numeric values safely
    floor_rval = h2k.get_number_field(floor, "exp_floor_r_value")
    floor_area = h2k.get_number_field(floor, "exp_floor_area")

    # Determine facility type and adjacency
    res_facility_type = model_data.get_building_detail("res_facility_type")

    # Use utility helper for adjacency determination
    floor_exterior = FacilityTypeHelper.determine_exterior_adjacent(floor, res_facility_type)
    buffered_type = FacilityTypeHelper.get_buffered_attached_type(res_facility_type)

    # Store foundation details for later calculations
    model_data.add_foundation_detail(
        {
            "type": "expFloor",
            "total_perimeter": 0,
            "total_area": floor_area,
            "exposed_perimeter": 0,
            "exposed_fraction": 0,
        }
    )

    # Build HPXML floor component
    hpxml_floor = {
        "SystemIdentifier": {"@id": floor_id},
        "ExteriorAdjacentTo": floor_exterior,
        "InteriorAdjacentTo": "conditioned space",  # always conditioned space
        "FloorType": {"WoodFrame": None},  # default to wood frame
        "Area": floor_area,  # [ft2]
        "InteriorFinish": {"Type": "none"},  # default for non-ceiling floors
        "Insulation": {
            "SystemIdentifier": {"@id": f"{floor_id}Insulation"},
            "AssemblyEffectiveRValue": round(floor_rval, 2),
        },
        "extension": {"H2kLabel": floor_label},
    }

    # Add FloorOrCeiling attribute for non-freezing adjacent spaces
    if buffered_type == "other non-freezing space":
        hpxml_floor["FloorOrCeiling"] = "floor"

    return hpxml_floor


def get_floors(h2k_dict: H2KDict, model_data: Any) -> Dict[str, Any]:
    """
    Extract and process all exposed floor components from H2K data.

    Args:
        h2k_dict: H2K dictionary containing house data
        model_data: Model data object for counters and warnings

    Returns:
        Dictionary containing processed HPXML floor components
    """
    hpxml_floors = extract_and_process_components(
        h2k_dict=h2k_dict,
        component_type="Floor",
        model_data=model_data,
        counter_name="floor",
        id_prefix="Floor",
        processor_func=_process_single_floor,
    )

    return {"floors": hpxml_floors}


# Keep original function for backward compatibility
def get_floors_legacy(h2k_dict, model_data=None):
    """Legacy version of get_floors for backward compatibility."""
    if model_data is None:
        model_data = {}

    return get_floors(h2k_dict, model_data)
