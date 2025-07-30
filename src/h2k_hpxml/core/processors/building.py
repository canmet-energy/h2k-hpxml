"""
Building details processing for H2K to HPXML translation.

This module handles processing of building construction details, occupancy,
and structural information from H2K data to populate HPXML building sections.
"""

from ...core.model import ModelData
from ...exceptions import HPXMLGenerationError
from ...types import H2KDict
from ...types import HPXMLDict
from ...utils import h2k
from ...utils import obj
from ...utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def process_building_details(
    h2k_dict: H2KDict, hpxml_dict: HPXMLDict, model_data: ModelData
) -> None:
    """
    Process building details and populate model data and HPXML structure.

    Extracts building construction details, occupancy information, and structural
    data from H2K input and translates it to HPXML format. This includes:
    - Building type and construction details
    - Occupancy patterns and schedules
    - Foundation and structural information
    - Building orientation and geometry

    Args:
        h2k_dict: Parsed H2K dictionary containing building data
        hpxml_dict: Parsed HPXML dictionary to be populated
        model_data: ModelData instance for tracking building information

    Raises:
        HPXMLGenerationError: If building details cannot be processed

    Returns:
        None: Modifies hpxml_dict and model_data in place

    Raises:
        HPXMLGenerationError: If building details processing fails
    """
    logger.info("Processing building details")

    try:
        # Initialize model data with H2K results
        model_data.set_results(h2k_dict)

        # ================ 3. HPXML Section: Building ================
        # Set up model details for use in calculations
        model_data.set_building_details(
            {
                "building_type": h2k.get_selection_field(h2k_dict, "building_type"),
                "ag_heated_floor_area": h2k.get_number_field(h2k_dict, "ag_heated_floor_area"),
                "bg_heated_floor_area": h2k.get_number_field(h2k_dict, "bg_heated_floor_area"),
            }
        )

        # Handle multi-unit residential building (MURB) details
        if model_data.get_building_detail("building_type") != "house":
            murb_unit_counts = obj.get_val(h2k_dict, "HouseFile,House,Specifications,NumberOf")
            model_data.set_building_details(
                {
                    "storeys_in_building": murb_unit_counts.get("@storeysInBuilding", 0),
                    "res_units": murb_unit_counts.get("@dwellingUnits", 0),
                    "non_res_units": murb_unit_counts.get("@nonResUnits", 0),
                    "units_visited": murb_unit_counts.get("@unitsVisited", 0),
                    "common_space_area": h2k.get_number_field(h2k_dict, "common_space_area"),
                    "non_res_unit_area": h2k.get_number_field(h2k_dict, "non_res_unit_area"),
                }
            )

        # ================ 5. HPXML Section: Building Summary ================
        # Building site details
        building_sum_site_dict = hpxml_dict["HPXML"]["Building"]["BuildingDetails"][
            "BuildingSummary"
        ]["Site"]

        # Front-facing direction
        building_sum_site_dict["AzimuthOfFrontOfHome"] = h2k.get_selection_field(
            h2k_dict, "azimuth_of_home"
        )

        # Shielding of home
        building_sum_site_dict["ShieldingofHome"] = h2k.get_selection_field(
            h2k_dict, "shielding_of_home"
        )

        # Ground Conductivity
        building_sum_site_dict["Soil"]["Conductivity"] = h2k.get_selection_field(
            h2k_dict, "ground_conductivity"
        )

        # Building occupancy
        num_occupants = 3  # SOC Hardcoded
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"][
            "BuildingOccupancy"
        ] = {"NumberofResidents": num_occupants}
        model_data.set_building_details({"num_occupants": num_occupants})

        # Building construction details
        building_const_dict = hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"][
            "BuildingConstruction"
        ]

        # Residential facility type
        res_facility_type = h2k.get_selection_field(h2k_dict, "res_facility_type")
        logger.info(f"Residential Facility Type: {res_facility_type}")
        model_data.set_building_details({"res_facility_type": res_facility_type})
        building_const_dict["ResidentialFacilityType"] = res_facility_type

        # Number of conditioned floors above grade
        num_ag_storeys = h2k.get_selection_field(h2k_dict, "num_ag_storeys")
        building_const_dict["NumberofConditionedFloorsAboveGrade"] = num_ag_storeys

        # Number of conditioned floors (including basement if applicable)
        basement_dict = obj.get_val(h2k_dict, "HouseFile,House,Components,Basement")
        basement_dict = (basement_dict if isinstance(basement_dict, list) else [basement_dict])[0]
        num_bg_storeys = 1 if "@exposedSurfacePerimeter" in basement_dict.keys() else 0
        num_tot_storeys = num_ag_storeys + num_bg_storeys
        building_const_dict["NumberofConditionedFloors"] = num_tot_storeys

        # Number of bedrooms
        num_bedrooms = h2k.get_number_field(h2k_dict, "num_bedrooms")
        building_const_dict["NumberofBedrooms"] = num_bedrooms
        model_data.set_building_details({"num_bedrooms": num_bedrooms})

        # Number of bathrooms (with validation)
        num_bathrooms = h2k.get_number_field(h2k_dict, "num_bathrooms")
        if num_bathrooms < 1:
            model_data.add_warning_message(
                {
                    "message": "The h2k model does not have any bathrooms specified. One bathroom has been added to the HPXML model to prevent calculation errors."
                }
            )
        building_const_dict["NumberofBathrooms"] = max(num_bathrooms, 1)

        # Conditioned building volume
        house_volume = h2k.get_number_field(h2k_dict, "house_volume")
        building_const_dict["ConditionedBuildingVolume"] = house_volume

        logger.debug("Building details processed successfully")

    except Exception as e:
        raise HPXMLGenerationError(
            f"Failed to process building details: {e}", component="building_details"
        )
