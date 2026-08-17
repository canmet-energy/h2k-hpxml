from ..core import h2k_parser as h2k


# Returns the HVAC Control system dictionary
# Essentially contains the "Temperatures" section of h2k
def get_hvac_control(h2k_dict, model_data):

    setpoint_heating_day = model_data.get_operating_condition("heating_setpoint")
    setpoint_cooling_day = model_data.get_operating_condition("cooling_setpoint")

    # TODO: these will be used when in general mode, but configured in the operating conditions section
    # setpoint_heating_day = h2k.get_number_field(h2k_dict, "setpoint_heating_day")
    # setpoint_cooling_day = h2k.get_number_field(h2k_dict, "setpoint_cooling_day")

    setpoint_heating_night = h2k.get_number_field(h2k_dict, "setpoint_heating_night")
    setback_heating_duration = h2k.get_number_field(h2k_dict, "setback_heating_duration")

    # H2K always defines setback fields, but SOC assumes no setback unless enabled in config.
    apply_temperature_setback = model_data.get_config_bool(
        "hvac_control", "apply_temperature_setback", fallback=False
    )

    if not apply_temperature_setback:
        setpoint_heating_night = setpoint_heating_day
        setback_heating_duration = 0
    


    hvac_control_dict = {
        "SystemIdentifier": {"@id": "HVACControl1"},
        "SetpointTempHeatingSeason": setpoint_heating_day,
        "SetbackTempHeatingSeason": setpoint_heating_night,
        "TotalSetbackHoursperWeekHeating": setback_heating_duration * 7,
        "SetpointTempCoolingSeason": setpoint_cooling_day,
    }

    return hvac_control_dict


# Element Order:
# SystemInfo
# ConnectedDevice
# AttachedToZone
# ControlType
# SetpointTempHeatingSeason
# SetbackTempHeatingSeason
# TotalSetbackHoursperWeekHeating
# SetupTempCoolingSeason
# SetpointTempCoolingSeason
# TotalSetupHoursperWeekCooling
# HotWaterResetControl
# HeatLowered
# ACAdjusted
# FractionThermostaticRadiatorValves
# FractionElectronicZoneValves
# HVACSystemsServed
# HeatingSeason
# CoolingSeason
