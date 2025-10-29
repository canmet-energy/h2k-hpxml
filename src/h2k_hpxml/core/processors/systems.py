"""
Building systems processing for H2K to HPXML translation.

This module handles processing of all building systems including HVAC, water heating,
mechanical ventilation, appliances, lighting, and miscellaneous loads.
"""

from ...components.baseload_appliances import get_appliances
from ...components.baseload_lighting import get_lighting
from ...components.baseload_miscloads import get_plug_loads
from ...components.system_coordinator import get_systems
from ...exceptions import HPXMLGenerationError
from ...utils import hot_water_usage
from ...utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def process_systems_and_loads(h2k_dict, hpxml_dict, model_data):
    """
    Process all building systems and loads, updating HPXML structure.

    Args:
        h2k_dict: Parsed H2K dictionary
        hpxml_dict: Parsed HPXML dictionary
        model_data: ModelData instance for tracking building information

    Returns:
        None: Modifies hpxml_dict and model_data in place

    Raises:
        HPXMLGenerationError: If systems processing fails
    """
    logger.info("Processing building systems and loads")

    try:
        # ================ 8. HPXML Section: Systems ================
        # Run appliances first so we know hot water consumption
        appliance_result = get_appliances(h2k_dict, model_data)

        systems_results = get_systems(h2k_dict, model_data)
        hvac_dict = systems_results["hvac_dict"]
        dhw_dict = systems_results["dhw_dict"]
        mech_vent_dict = systems_results["mech_vent_dict"]
        solar_dhw_dict = systems_results["solar_dhw_dict"]
        generation_dict = systems_results["generation_dict"]

        # Calculate hot water fixture multiplier
        fixtures_multiplier = hot_water_usage.get_fixtures_multiplier(h2k_dict, model_data)

        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Systems"] = {
            **({"HVAC": hvac_dict} if model_data.get_is_hvac_translated() else {}),
            **({"MechanicalVentilation": mech_vent_dict} if mech_vent_dict != {} else {}),
            **(
                {
                    "WaterHeating": {
                        **dhw_dict,
                        "extension": {"WaterFixturesUsageMultiplier": fixtures_multiplier},
                    }
                }
                if dhw_dict != {}
                else {}
            ),
            **({"SolarThermal": solar_dhw_dict} if solar_dhw_dict != {} else {}),
            **({"Photovoltaics": generation_dict} if generation_dict != {} else {}),
        }

        # Specify presence of flues if any have been detected while processing systems
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Enclosure"]["AirInfiltration"] = {
            **hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Enclosure"]["AirInfiltration"],
            "extension": {
                "HasFlueOrChimneyInConditionedSpace": len(model_data.get_flue_diameters()) > 0
            },
        }

        # ================ 9. HPXML Section: Appliances ================
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Appliances"] = appliance_result

        # ================ 10. HPXML Section: Lighting & Ceiling Fans ================
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Lighting"] = get_lighting(
            h2k_dict, model_data
        )

        # ================ 11. HPXML Section: Pools & Permanent Spas ================
        # Not considered under SOC, possibly under atypical loads

        # ================ 12. HPXML Section: Misc Loads ================
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["MiscLoads"] = get_plug_loads(
            h2k_dict, model_data
        )

        logger.debug("Building systems and loads processed successfully")

    except Exception as e:
        raise HPXMLGenerationError(f"Failed to process systems and loads: {e}", component="systems")
