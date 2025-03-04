import math

from ..utils import obj, h2k


# TODO: Flue diameter not handled


# Translates data from the supplementary heating systems section
# All FractionHeatLoadServed elements hardcoded at 0 until we figure out how to determine this
def get_secondary_heating_systems(h2k_dict, model_data):

    results = model_data.get_results("SOC")

    if (
        "SupplementaryHeatingSystems"
        not in obj.get_val(h2k_dict, "HouseFile,House,HeatingCooling").keys()
    ):
        return []

    suppl_heating_systems = obj.get_val(
        h2k_dict, "HouseFile,House,HeatingCooling,SupplementaryHeatingSystems,System"
    )

    if suppl_heating_systems == {}:
        return []

    # Always process as array
    suppl_heating_systems = (
        suppl_heating_systems
        if isinstance(suppl_heating_systems, list)
        else [suppl_heating_systems]
    )

    secondary_heating_results = []

    # ===================== START DETERMINATION OF FractionHeatLoadServed ===================== #
    # CHECKING RESULTS TO DETERMINE FRACTIONHEATLOAD NOT CURRENTLY USED
    # Look at results to determine fraction of heating loads served by each system
    # Note that we have to look at whether a pilot light is present and subtract that amount
    primary_heating_results = obj.get_val(results, "Annual,Consumption,SpaceHeating")
    has_heat_pump = (
        float(obj.get_val(results, "Annual,Consumption,Electrical,@heatPump")) > 0
    )

    suppl_heating_results = obj.get_val(
        results, "Annual,Consumption,SupplementalHeating"
    )

    primary_pilot_GJpery = model_data.get_building_detail("primary_pilot_light_GJpery")

    # without pilot light
    primary_heating_GJpery = max(
        0, float(primary_heating_results.get("@primary", 0)) - primary_pilot_GJpery
    )

    # The "secondary" heating energy section in the results only holds heat pump
    heat_pump_heating_GJpery = (
        float(primary_heating_results.get("@secondary", 0)) if has_heat_pump else 0
    )

    total_annual_heating_GJpery = primary_heating_GJpery + heat_pump_heating_GJpery
    heating_fraction_dict = {
        "primary": {
            "value": primary_heating_GJpery,
            "fraction": primary_heating_GJpery / total_annual_heating_GJpery,
        },
        "secondary": {
            "value": heat_pump_heating_GJpery,
            "fraction": heat_pump_heating_GJpery / total_annual_heating_GJpery,
        },
        "system1": {"value": 0, "fraction": 0},
        "system2": {"value": 0, "fraction": 0},
        "system3": {"value": 0, "fraction": 0},
        "system4": {"value": 0, "fraction": 0},
        "system5": {"value": 0, "fraction": 0},
    }

    for suppl_sys_key in suppl_heating_results.keys():
        heating_energy_value = round(float(suppl_heating_results[suppl_sys_key]), 4)

        rank = suppl_sys_key.replace("@system", "")

        matching_system = [
            float(x.get("Specifications", {}).get("@pilotLight", 0))
            for x in suppl_heating_systems
            if x.get("@rank", None) == rank
        ]

        matching_system_pilot_light_GJpery = round(
            (matching_system[0] if len(matching_system) > 0 else 0) * 365 / 1000, 4
        )

        total_annual_heating_GJpery += max(
            0, heating_energy_value - matching_system_pilot_light_GJpery
        )

        heating_fraction_dict[f"system{rank}"] = {
            "value": max(0, heating_energy_value - matching_system_pilot_light_GJpery),
            "fraction": 0,
        }

    # Make sure that our fractions always exactly equal 1 by tracking the remainder and reassigning it to the primary system
    remaining_fraction = 1
    for sys_key in heating_fraction_dict.keys():
        fraction = heating_fraction_dict[sys_key]["value"] / total_annual_heating_GJpery
        heating_fraction_dict[sys_key] = {
            "value": heating_fraction_dict[sys_key]["value"],
            "fraction": fraction,
        }

        if sys_key != "primary":
            remaining_fraction -= fraction

    heating_fraction_dict["primary"] = {
        "value": heating_fraction_dict["primary"]["value"],
        "fraction": remaining_fraction,
    }

    # ===================== END DETERMINATION OF FractionHeatLoadServed ===================== #

    suppl_heating_distribution_types = []
    for system_data in suppl_heating_systems:

        system_type = h2k.get_selection_field(system_data, "suppl_heating_equip_type")
        flue_diameter = h2k.get_number_field(system_data, "suppl_heating_flue_diameter")
        if flue_diameter > 0:
            model_data.set_flue_diameters(flue_diameter)

        # Determine what the primary (type1) heating system type is, if required
        type1_system_type = model_data.get_building_detail("primary_heating_equip_type")
        system_type = type1_system_type if system_type == "primary" else system_type

        new_system = {}
        if system_type == "baseboard":
            new_system = get_electric_resistance(system_data, system_type, model_data)

        elif system_type == "stove":
            new_system = get_stove(system_data, model_data)

        elif system_type == "fireplace":
            new_system = get_fireplace(system_data, model_data)

        elif system_type == "furnace":
            new_system = get_furnace(system_data, model_data)
            # Need this to be included here, so that the distribution system doesn't get missed
            suppl_heating_distribution_types = [
                *suppl_heating_distribution_types,
                "air_regular velocity",
            ]

        elif system_type == "space heater":
            new_system = get_space_heater(system_data, model_data)

        elif system_type == "radiant floor":
            # Uses "Electric Resistance", always electric
            new_system = get_electric_resistance(system_data, system_type, model_data)

        elif system_type == "radiant ceiling":
            # Uses "Electric Resistance", always electric
            new_system = get_electric_resistance(system_data, system_type, model_data)

        elif system_type == "boiler":
            # The only way to get here is if the equipment type is set to "same as type 1"
            new_system = get_boiler(system_data, model_data)
            suppl_heating_distribution_types = [
                *suppl_heating_distribution_types,
                "hydronic_radiator",
            ]

        # new_system = get_suppl_heating_system(system_data, model_data)
        secondary_heating_results = [*secondary_heating_results, new_system]

    secondary_heating_results = [x for x in secondary_heating_results if x != {}]

    model_data.set_suppl_heating_distribution_types(suppl_heating_distribution_types)

    return secondary_heating_results


# Translates electric suppl heating systems that use the "baseboard", "radiant floor", or "radiant ceiling" ElectricDistribution types
def get_electric_resistance(system_data, system_type, model_data):
    rank = obj.get_val(system_data, "@rank")

    suppl_heating_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    suppl_heating_efficiency = h2k.get_number_field(
        system_data, "suppl_heating_efficiency"
    )

    # By default we assume electric resistance, overwriting with radiant if present
    # “baseboard”, “radiant floor”, or “radiant ceiling”
    elec_resistance = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "HeatingSystemType": {
            "ElectricResistance": {"ElectricDistribution": system_type}
        },
        "HeatingSystemFuel": "electricity",
        "HeatingCapacity": suppl_heating_capacity,
        "AnnualHeatingEfficiency": {
            "Units": "Percent",  # Only unit type allowed here. Note actual value must be a fraction
            "Value": suppl_heating_efficiency,
        },
        "FractionHeatLoadServed": 0,  # Hardcoded for now
    }

    return elec_resistance


def get_furnace(system_data, model_data):
    rank = obj.get_val(system_data, "@rank")
    furnace_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    furnace_efficiency = h2k.get_number_field(system_data, "suppl_heating_efficiency")

    furnace_pilot_light = h2k.get_number_field(system_data, "suppl_heating_pilot_light")

    furnace_fuel_type = h2k.get_selection_field(system_data, "furnace_fuel_type")

    furnace_dict = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "DistributionSystem": {
            "@idref": model_data.get_system_id("hvac_air_distribution")
        },
        "HeatingSystemType": {
            "Furnace": None
        },  # potential to add pilot light info later
        "HeatingSystemFuel": furnace_fuel_type,
        "HeatingCapacity": furnace_capacity,
        "AnnualHeatingEfficiency": {
            "Units": (
                "AFUE"  # "Percent" if is_steady_state == "true" else "AFUE"
            ),  # "AFUE" / "Percent"
            "Value": furnace_efficiency,
        },
        "FractionHeatLoadServed": 0,
    }

    # Add pilot light if present
    if furnace_pilot_light > 0:
        furnace_dict["HeatingSystemType"] = {
            "Furnace": {
                "PilotLight": "true",
                "extension": {"PilotLightBtuh": furnace_pilot_light},
            }
        }

    return furnace_dict


def get_boiler(system_data, model_data):
    rank = obj.get_val(system_data, "@rank")
    boiler_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    boiler_efficiency = h2k.get_number_field(system_data, "suppl_heating_efficiency")
    boiler_pilot_light = h2k.get_number_field(system_data, "suppl_heating_pilot_light")

    boiler_fuel_type = h2k.get_selection_field(system_data, "furnace_fuel_type")

    boiler_dict = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "DistributionSystem": {
            "@idref": model_data.get_system_id("hvac_hydronic_distribution")
        },
        "HeatingSystemType": {
            "Boiler": None
        },  # potential to add pilot light info later
        "HeatingSystemFuel": boiler_fuel_type,
        "HeatingCapacity": boiler_capacity,
        "AnnualHeatingEfficiency": {
            "Units": (
                "AFUE"  # "Percent" if is_steady_state == "true" else "AFUE"
            ),  # "AFUE" / "Percent"
            "Value": boiler_efficiency,
        },
        "FractionHeatLoadServed": 0,
        "ElectricAuxiliaryEnergy": 0,  # Without this, HPXML assumes 330 kWh/y for oil and 170 kWh/y for gas boilers
    }

    # Add pilot light if present
    if boiler_pilot_light > 0:
        boiler_dict["HeatingSystemType"] = {
            "Boiler": {
                "PilotLight": "true",
                "extension": {"PilotLightBtuh": boiler_pilot_light},
            }
        }

    return boiler_dict


def get_fireplace(system_data, model_data):
    rank = obj.get_val(system_data, "@rank")
    fireplace_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    fireplace_efficiency = h2k.get_number_field(system_data, "suppl_heating_efficiency")

    # Same options as furnace
    fireplace_fuel_type = h2k.get_selection_field(system_data, "furnace_fuel_type")

    fireplace_dict = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "HeatingSystemType": {
            "Fireplace": None
        },  # potential to add pilot light info later
        "HeatingSystemFuel": fireplace_fuel_type,
        "HeatingCapacity": fireplace_capacity,
        "AnnualHeatingEfficiency": {
            "Units": "Percent",  # "AFUE" / "Percent"
            "Value": fireplace_efficiency,
        },
        "FractionHeatLoadServed": 0,
    }

    return fireplace_dict


def get_stove(system_data, model_data):
    rank = obj.get_val(system_data, "@rank")
    stove_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    stove_efficiency = h2k.get_number_field(system_data, "suppl_heating_efficiency")

    stove_fuel_type = h2k.get_selection_field(system_data, "furnace_fuel_type")

    stove_dict = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "HeatingSystemType": {"Stove": None},
        "HeatingSystemFuel": stove_fuel_type,
        "HeatingCapacity": stove_capacity,
        "AnnualHeatingEfficiency": {
            "Units": "Percent",
            "Value": stove_efficiency,
        },
        "FractionHeatLoadServed": 0,
    }

    return stove_dict


def get_space_heater(system_data, model_data):
    rank = obj.get_val(system_data, "@rank")

    suppl_heating_capacity = h2k.get_number_field(system_data, "suppl_heating_capacity")
    suppl_heating_efficiency = h2k.get_number_field(
        system_data, "suppl_heating_efficiency"
    )

    heater_fuel_type = h2k.get_selection_field(system_data, "furnace_fuel_type")

    # By default we assume electric resistance, overwriting with radiant if present
    # “baseboard”, “radiant floor”, or “radiant ceiling”
    space_heater = {
        "SystemIdentifier": {"@id": f"SupplHeatingSystem{rank}"},
        "HeatingSystemType": {"SpaceHeater": None},
        "HeatingSystemFuel": heater_fuel_type,
        "HeatingCapacity": suppl_heating_capacity,
        "AnnualHeatingEfficiency": {
            "Units": "Percent",  # Only unit type allowed here. Note actual value must be a fraction
            "Value": suppl_heating_efficiency,
        },
        "FractionHeatLoadServed": 0,  # Hardcoded for now
    }

    return space_heater
