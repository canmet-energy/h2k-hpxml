from ..core import data_utils as obj
from ..core import h2k_parser as h2k

# OS-HPXML rejects electric-backup heat pumps when compressor and backup lockout
# temperatures are within 5F of each other (defaults.rb set_heat_pump_control_temperatures).
ELECTRIC_LOCKOUT_DEADBAND_F = 5.0


def _is_fossil_backup_fuel(fuel):
    return fuel is not None and fuel != "electricity"


def build_backup_temperature_fields(
    switchover_type,
    switchover_temp,
    backup_fuel,
    heat_pump_type=None,
):
    """
    Map H2K heat-pump cutoff settings to OS-HPXML temperature controls.

    H2K provides a single cutoff (Restricted / Unrestricted / Balance point).
    OS-HPXML uses different elements depending on backup fuel and HP type:

    - Fossil-fuel backup (dual-fuel), non-GSHP:
        BackupHeatingSwitchoverTemperature — compressor off and backup on below T
    - Fossil-fuel backup, ground-to-air:
        Switchover is forbidden; use equal compressor/backup lockouts instead
    - Electric backup:
        BackupHeatingLockoutTemperature = T (backup only below T) and
        CompressorLockoutTemperature = T - 5F (required deadband)

    Balance / unrestricted omit explicit fields so OS-HPXML defaults apply.
    """
    if switchover_type in (None, "balance", "unrestricted"):
        return {}

    if switchover_type != "restricted" or switchover_temp is None:
        return {}

    temp = float(switchover_temp)

    if _is_fossil_backup_fuel(backup_fuel):
        if heat_pump_type == "ground-to-air":
            # Schematron: ground-to-air must not have BackupHeatingSwitchoverTemperature
            return {
                "CompressorLockoutTemperature": temp,
                "BackupHeatingLockoutTemperature": temp,
            }
        return {"BackupHeatingSwitchoverTemperature": temp}

    # Electric backup: exclusive switchover is not allowed; use lockouts with deadband.
    return {
        "CompressorLockoutTemperature": temp - ELECTRIC_LOCKOUT_DEADBAND_F,
        "BackupHeatingLockoutTemperature": temp,
    }


def _split_temperature_fields(temperature_fields):
    """
    Split lockout/switchover fields for HPXML element order.

    Schema order requires CompressorLockoutTemperature before BackupType, while
    BackupHeatingSwitchoverTemperature / BackupHeatingLockoutTemperature come after
    backup capacity fields.
    """
    compressor_fields = {}
    backup_fields = {}
    if "CompressorLockoutTemperature" in temperature_fields:
        compressor_fields["CompressorLockoutTemperature"] = temperature_fields[
            "CompressorLockoutTemperature"
        ]
    for key in (
        "BackupHeatingSwitchoverTemperature",
        "BackupHeatingLockoutTemperature",
    ):
        if key in temperature_fields:
            backup_fields[key] = temperature_fields[key]
    return compressor_fields, backup_fields


def _backup_system_fields(
    heat_pump_backup_type,
    heat_pump_backup_system_id,
    heat_pump_backup_fuel,
    heat_pump_backup_eff_unit,
    heat_pump_backup_efficiency,
    heat_pump_backup_autosized,
    heat_pump_backup_capacity,
    backup_temperature_fields,
):
    """Build BackupType / BackupSystem / efficiency / backup-temperature fields."""
    if heat_pump_backup_type == "separate":
        return {
            "BackupType": "separate",
            "BackupSystem": {"@idref": heat_pump_backup_system_id},
            **backup_temperature_fields,
        }
    if heat_pump_backup_type == "integrated":
        return {
            "BackupType": "integrated",
            "BackupSystemFuel": heat_pump_backup_fuel,
            "BackupAnnualHeatingEfficiency": {
                "Units": heat_pump_backup_eff_unit,
                "Value": heat_pump_backup_efficiency,
            },
            **(
                {}
                if heat_pump_backup_autosized
                else {"BackupHeatingCapacity": heat_pump_backup_capacity}
            ),
            **backup_temperature_fields,
        }
    return {}


def _apply_restricted_defrost_backup_control(heat_pump_dict, switchover_type):
    """
    OS-HPXML defaults BackupHeatingActiveDuringDefrost=true for ducted
    integrated backup. That EMS path burns backup fuel whenever outdoor
    temp is below the defrost limit (~40F), ignoring switchover/lockout.

    H2K restricted cutoff means backup must not operate above the cutoff,
    so disable defrost backup heat when an explicit restricted cutoff is set.
    """
    if switchover_type != "restricted":
        return heat_pump_dict
    if heat_pump_dict.get("BackupType") != "integrated":
        return heat_pump_dict
    extension = heat_pump_dict.setdefault("extension", {})
    extension["BackupHeatingActiveDuringDefrost"] = False
    return heat_pump_dict


# Translates heat pump data from the "Type2" heating system section of h2k
# Heat pump back-up types defined based on primary heating system type as follows:
#   "integrated": furnace
#   "separate": baseboards, boiler, fireplace, stove
def get_heat_pump(h2k_dict, model_data):
    type2_heating_system = obj.get_val(h2k_dict, "HouseFile,House,HeatingCooling,Type2")

    # h2k files cannot be built without a Type 1 heating system, so we don't need to check for the presence of one
    type2_type = [x for x in list(type2_heating_system.keys()) if x != "@shadingInF280Cooling"]

    type2_type = "None" if len(type2_type) == 0 else type2_type[0]

    type2_data = type2_heating_system.get(type2_type, {})

    # Get common specs
    cooling_sensible_heat_fraction = h2k.get_number_field(
        type2_data, "cooling_sensible_heat_fraction"
    )
    hp_heating_eff = h2k.get_number_field(type2_data, "heat_pump_heating_efficiency")
    hp_cooling_eff = h2k.get_number_field(type2_data, "heat_pump_cooling_efficiency")
    hp_capacity = h2k.get_number_field(type2_data, "heat_pump_capacity")
    is_auto_sized = (
        "Calculated" == obj.get_val(type2_data, "Specifications,OutputCapacity,English")
        or hp_capacity == 0
    )

    is_heating_cop = obj.get_val(type2_data, "Specifications,HeatingEfficiency,@isCop") == "true"

    is_cooling_cop = obj.get_val(type2_data, "Specifications,CoolingEfficiency,@isCop") == "true"

    # H2k's conversions:
    # COP = hspf * 0.376 + 0.78
    # COP = seer * 0.115 + 1.428;

    # Need heating efficiency in either HSPF or COP
    if is_heating_cop:
        # Heating provided in COP
        hp_heating_cop = hp_heating_eff
        hp_heating_hspf = (hp_heating_eff - 0.78) / 0.376
    else:
        # Heating provided in HSPF
        hp_heating_cop = hp_heating_eff * 0.376 + 0.78
        hp_heating_hspf = hp_heating_eff

    # Need cooling efficiency in either SEER or EER
    if is_cooling_cop:
        # Cooling provided in COP
        hp_cooling_eer = hp_cooling_eff * 3.412
        hp_cooling_seer = (hp_cooling_eff - 1.428) / 0.115
    else:
        # Cooling provided in SEER
        # TODO: in v11.13, we can use the raw value here because they moved from SEER to EER
        hp_cooling_eer = -0.02 * (hp_cooling_eff**2) + 1.12 * hp_cooling_eff
        hp_cooling_seer = hp_cooling_eff

    # Get backup system details, note this may get overwritten if we're dealing with mini-splits
    heat_pump_backup_type = model_data.get_building_detail(
        "heat_pump_backup_type"
    )  # "separate" or "integrated"
    model_data.get_building_detail("heat_pump_backup_system")
    heat_pump_backup_fuel = model_data.get_building_detail("heat_pump_backup_fuel")
    heat_pump_backup_efficiency = model_data.get_building_detail("heat_pump_backup_efficiency")
    heat_pump_backup_eff_unit = model_data.get_building_detail("heat_pump_backup_eff_unit")
    heat_pump_backup_autosized = model_data.get_building_detail("heat_pump_backup_autosized")
    heat_pump_backup_capacity = model_data.get_building_detail("heat_pump_backup_capacity")
    heat_pump_backup_system_id = model_data.get_building_detail("heat_pump_backup_system_id")

    # Get switchover information
    switchover_type = h2k.get_selection_field(type2_data, "heat_pump_switchover_type")
    switchover_temp = None
    if switchover_type == "restricted":
        switchover_temp = h2k.get_number_field(type2_data, "heat_pump_switchover_temp")
    elif switchover_type == "unrestricted":
        # Unrestricted outdoor-air cutoff is only unrealistic for air-source HPs
        if type2_type == "AirHeatPump":
            model_data.add_warning_message(
                {
                    "message": "An unrestricted cutoff was specified for an ASHP system. Review this setting before proceeding as it reflects an unrealistic system configuration."
                }
            )
    elif switchover_type == "balance":
        # Use OS-HPXML defaults for compressor/backup lockout temperatures
        pass

    # determine if in heating or heating+cooling configuration
    heating_and_cooling = obj.get_val(type2_data, "Equipment,Function,English") == "Heating/Cooling"

    def temperature_and_backup_fields(heat_pump_type):
        temperature_fields = build_backup_temperature_fields(
            switchover_type,
            switchover_temp,
            heat_pump_backup_fuel,
            heat_pump_type=heat_pump_type,
        )
        compressor_fields, backup_temp_fields = _split_temperature_fields(temperature_fields)
        backup_fields = _backup_system_fields(
            heat_pump_backup_type,
            heat_pump_backup_system_id,
            heat_pump_backup_fuel,
            heat_pump_backup_eff_unit,
            heat_pump_backup_efficiency,
            heat_pump_backup_autosized,
            heat_pump_backup_capacity,
            backup_temp_fields,
        )
        return compressor_fields, backup_fields

    heat_pump_dict = {}
    if type2_type == "AirHeatPump":
        # Default backup logic for central ASHP
        # If neither CompressorLockoutTemperature nor BackupHeatingSwitchoverTemperature provided,
        # CompressorLockoutTemperature defaults to 25F if fossil fuel backup
        # otherwise -20F if CompressorType is “variable speed” otherwise 0F.

        # Default backup logic for mini split ASHP
        # If neither CompressorLockoutTemperature nor BackupHeatingSwitchoverTemperature provided,
        # CompressorLockoutTemperature defaults to 25F if fossil fuel backup otherwise -20F.

        # Default backup logic for packaged terminal ASHP
        # If neither CompressorLockoutTemperature nor BackupHeatingSwitchoverTemperature provided,
        # CompressorLockoutTemperature defaults to 25F if fossil fuel backup otherwise 0F.

        air_heat_pump_equip_type = h2k.get_selection_field(type2_data, "air_heat_pump_equip_type")

        if air_heat_pump_equip_type == "mini-split":
            # Defaults for determining low-temp heat pump capacity:
            # If neither extension/HeatingCapacityRetention nor HeatingCapacity17F nor HeatingDetailedPerformanceData provided, heating capacity retention defaults to 0.0461 * HSPF + 0.1594 (at 5F).
            heat_pump_backup_type = "separate"
            model_data.set_building_details(
                {
                    "heat_pump_backup_type": "separate",
                }
            )
            compressor_fields, backup_fields = temperature_and_backup_fields("mini-split")

            heat_pump_dict = {
                "SystemIdentifier": {"@id": model_data.get_system_id("heat_pump")},
                "HeatPumpType": "mini-split",
                "HeatPumpFuel": "electricity",
                **({} if is_auto_sized else {"HeatingCapacity": hp_capacity}),
                # "HeatingCapacity17F": None, #could be included here if we had the info
                **({} if is_auto_sized else {"CoolingCapacity": hp_capacity}),
                # OS-HPXML requires mini-split compressor type to be variable speed
                "CompressorType": "variable speed",
                **compressor_fields,
                "CoolingSensibleHeatFraction": cooling_sensible_heat_fraction,
                **backup_fields,
                "FractionHeatLoadServed": 1,
                "FractionCoolLoadServed": 1,
                "AnnualCoolingEfficiency": {
                    "Units": "SEER",  # only option
                    "Value": round(hp_cooling_seer, 2),
                },
                "AnnualHeatingEfficiency": {
                    "Units": "HSPF",  # only option
                    "Value": round(hp_heating_hspf, 2),
                },
                "extension": {
                    "HeatingCapacityFraction17F": {
                        "Fraction": 0.563635566,
                    },  # Based on h2k HP curve
                    **(
                        {
                            "HeatingAutosizingFactor": 1,
                            "CoolingAutosizingFactor": 1,
                        }
                        if is_auto_sized
                        else {}
                    ),
                },
            }

        else:
            # air-to-air
            # Defaults for determining low-temp heat pump capacity:
            # If neither extension/HeatingCapacityRetention nor HeatingCapacity17F nor HeatingDetailedPerformanceData provided, heating capacity retention defaults based on CompressorType:
            # - single/two stage: 0.425 (at 5F)
            # - variable speed: 0.0461 * HSPF + 0.1594 (at 5F)
            compressor_fields, backup_fields = temperature_and_backup_fields("air-to-air")

            heat_pump_dict = {
                "SystemIdentifier": {"@id": model_data.get_system_id("heat_pump")},
                "DistributionSystem": {"@idref": model_data.get_system_id("hvac_air_distribution")},
                "HeatPumpType": "air-to-air",
                "HeatPumpFuel": "electricity",
                **({} if is_auto_sized else {"HeatingCapacity": hp_capacity}),
                # "HeatingCapacity17F": None, #could be included here if we had the info
                **({} if is_auto_sized else {"CoolingCapacity": hp_capacity}),
                "CompressorType": "single stage" if hp_cooling_seer <= 15 else "two stage" if hp_cooling_seer <= 21 else "variable speed",
                **compressor_fields,
                "CoolingSensibleHeatFraction": (
                    cooling_sensible_heat_fraction if heating_and_cooling else 0.76
                ),
                **backup_fields,
                "FractionHeatLoadServed": 1,
                "FractionCoolLoadServed": 1 if heating_and_cooling else 0,
                # SEER = 10 is a placeholder to prevent hpxml from crashing, but it's only used when the HP is in heating-only mode
                "AnnualCoolingEfficiency": {
                    "Units": "SEER",  # only option
                    "Value": round(hp_cooling_seer, 2) if heating_and_cooling else 10,
                },
                "AnnualHeatingEfficiency": {
                    "Units": "HSPF",  # only option
                    "Value": round(hp_heating_hspf, 2),
                },
                "extension": {
                    "HeatingCapacityFraction17F": {
                        "Fraction": 0.563635566,
                    },  # Based on h2k HP curve
                    **(
                        {
                            "HeatingAutosizingFactor": 1,
                            "CoolingAutosizingFactor": 1,
                        }
                        if is_auto_sized
                        else {}
                    ),
                },
            }

            model_data.set_ac_hp_distribution_type("air_regular velocity")

    elif type2_type in ("WaterHeatPump", "GroundHeatPump"):
        # H2K WaterHeatPump is a residential water-source HP. OS-HPXML's
        # "water-loop-to-air" type is for shared multifamily loops (requires a
        # shared boiler/chiller and hydronic water-loop distribution), so map
        # both H2K WSHP and GSHP to ground-to-air.
        compressor_fields, backup_fields = temperature_and_backup_fields("ground-to-air")
        heat_pump_dict = {
            "SystemIdentifier": {"@id": model_data.get_system_id("heat_pump")},
            "DistributionSystem": {"@idref": model_data.get_system_id("hvac_air_distribution")},
            "HeatPumpType": "ground-to-air",
            "HeatPumpFuel": "electricity",
            **({} if is_auto_sized else {"HeatingCapacity": hp_capacity}),
            **({} if is_auto_sized else {"CoolingCapacity": hp_capacity}),
            "CompressorType": "single stage",
            **compressor_fields,
            "CoolingSensibleHeatFraction": cooling_sensible_heat_fraction,
            **backup_fields,
            "FractionHeatLoadServed": 1,
            "FractionCoolLoadServed": 1,
            "AnnualCoolingEfficiency": {
                "Units": "EER",  # only option
                "Value": round(hp_cooling_eer, 2),
            },
            "AnnualHeatingEfficiency": {
                "Units": "COP",  # only option
                "Value": round(hp_heating_cop, 2),
            },
            # extension
            **(
                {
                    "extension": {
                        "HeatingAutosizingFactor": 1,
                        "CoolingAutosizingFactor": 1,
                    }
                }
                if is_auto_sized
                else {}
            ),
        }

        model_data.set_ac_hp_distribution_type("air_regular velocity")

    heat_pump_dict = _apply_restricted_defrost_backup_control(
        heat_pump_dict, switchover_type
    )

    return heat_pump_dict
