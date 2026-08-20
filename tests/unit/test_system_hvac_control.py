"""Tests for HVAC control setback configuration."""

from unittest.mock import MagicMock
from unittest.mock import patch

from h2k_hpxml.components.system_hvac_control import get_hvac_control
from h2k_hpxml.core.model import ModelData
from h2k_hpxml.utils.operating_conditions import get_soc_house_parameters

H2K_SETPOINTS = {
    "setpoint_heating_day": 68.0,
    "setpoint_cooling_day": 77.0,
    "setpoint_heating_night": 64.0,
    "setback_heating_duration": 8.0,
}


def _mock_h2k_numbers(_h2k_dict, field_key):
    return H2K_SETPOINTS[field_key]


def _make_model_data(apply_temperature_setback=None):
    model_data = ModelData()
    model_data.set_operating_conditions("SOC", get_soc_house_parameters())
    config_manager = MagicMock()
    if apply_temperature_setback is None:
        config_manager.get_bool.return_value = False
    else:
        config_manager.get_bool.return_value = apply_temperature_setback
    model_data.set_config_manager(config_manager)
    return model_data, config_manager


@patch(
    "h2k_hpxml.components.system_hvac_control.h2k.get_number_field",
    side_effect=_mock_h2k_numbers,
)
def test_apply_temperature_setback_false_disables_setback(_mock_get_number):
    model_data, config_manager = _make_model_data(apply_temperature_setback=False)

    result = get_hvac_control({}, model_data)

    config_manager.get_bool.assert_called_once_with(
        "hvac_control", "apply_temperature_setback", False
    )
    assert result["SetpointTempHeatingSeason"] == 68.0
    assert result["SetbackTempHeatingSeason"] == 68.0
    assert result["TotalSetbackHoursperWeekHeating"] == 0
    assert result["SetpointTempCoolingSeason"] == 77.0


@patch(
    "h2k_hpxml.components.system_hvac_control.h2k.get_number_field",
    side_effect=_mock_h2k_numbers,
)
def test_apply_temperature_setback_true_preserves_h2k_setback(_mock_get_number):
    model_data, _ = _make_model_data(apply_temperature_setback=True)

    result = get_hvac_control({}, model_data)

    assert result["SetpointTempHeatingSeason"] == 68.0
    assert result["SetbackTempHeatingSeason"] == 64.0
    assert result["TotalSetbackHoursperWeekHeating"] == 56.0


@patch(
    "h2k_hpxml.components.system_hvac_control.h2k.get_number_field",
    side_effect=_mock_h2k_numbers,
)
def test_missing_config_manager_defaults_to_no_setback(_mock_get_number):
    model_data = ModelData()
    model_data.set_operating_conditions("SOC", get_soc_house_parameters())

    result = get_hvac_control({}, model_data)

    assert result["SetbackTempHeatingSeason"] == 68.0
    assert result["TotalSetbackHoursperWeekHeating"] == 0
