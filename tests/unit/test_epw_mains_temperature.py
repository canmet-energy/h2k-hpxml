from pathlib import Path

import pytest

from h2k_hpxml.core.model import ModelData
from h2k_hpxml.utils.epw_mains_temperature import epw_path_from_weather_file
from h2k_hpxml.utils.epw_mains_temperature import read_epw_mains_annual_temp_f
from h2k_hpxml.utils.hot_water_usage import T_MIX_F, calc_hot_to_mixed_ratio

LONDON_EPW = (
    Path(__file__).resolve().parents[2]
    / "src/h2k_hpxml/resources/weather/CAN_ON_London.AP.716230_CWEC2020.epw"
)


def test_epw_path_from_weather_file_appends_extension():
    # Use a relative pathlib path so separators are correct on Windows and Linux CI.
    weather_file = str(Path("weather") / "CAN_ON_Ottawa.Intl.AP.716280_CWEC2020")
    epw_path = epw_path_from_weather_file(weather_file)
    assert epw_path.name == "CAN_ON_Ottawa.Intl.AP.716280_CWEC2020.epw"


def test_read_epw_mains_annual_temp_f_london():
    inlet_f = read_epw_mains_annual_temp_f(LONDON_EPW)
    assert 45.0 < inlet_f < 65.0


def test_calc_hot_to_mixed_ratio_uses_model_data():
    model_data = ModelData()
    model_data.set_building_details(
        {
            "water_heater_inlet_temp_f": 50.0,
            "hot_water_setpoint_f": 125.0,
        }
    )

    ratio = calc_hot_to_mixed_ratio(model_data)
    expected = (T_MIX_F - 50.0) / (125.0 - 50.0)
    assert ratio == pytest.approx(expected)


def test_calc_hot_to_mixed_ratio_defaults_when_missing():
    model_data = ModelData()
    assert calc_hot_to_mixed_ratio(model_data) == 1.0
