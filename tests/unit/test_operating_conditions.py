"""Tests for operating condition parameter resolution."""

import pytest

from h2k_hpxml.core.model import ModelData
from h2k_hpxml.utils.operating_conditions import ROC_HOT_WATER_REDUCTION
from h2k_hpxml.utils.operating_conditions import apply_operating_conditions
from h2k_hpxml.utils.operating_conditions import get_hot_water_reduction
from h2k_hpxml.utils.operating_conditions import get_soc_house_parameters
from h2k_hpxml.utils.operating_conditions import get_soc_murb_unit_parameters
from h2k_hpxml.utils.operating_conditions import resolve_operating_parameters


def test_soc_house_parameters():
    params = get_soc_house_parameters()
    assert params["num_occupants"] == 3
    assert params["daily_elec_total"] == 19.5
    assert params["annual_elec_clothes_dryer"] == 687
    assert params["daily_clothes_washer_reduction"] == 0.0


def test_soc_murb_parameters_scales_with_units():
    params = get_soc_murb_unit_parameters(num_units=4, common_space_area=100.0)
    assert params["num_occupants"] == 8
    assert params["daily_elec_interior_lighting"] == pytest.approx(6.8)
    assert params["daily_elec_common_space"] == pytest.approx(8.6)
    assert params["annual_elec_clothes_dryer"] == pytest.approx(1832.0)
    assert params["daily_clothes_washer_reduction"] == 0.0


def test_apply_operating_conditions_house():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    model_data = ModelData()
    model_data.set_building_details({"building_type": "house"})

    apply_operating_conditions(h2k_dict, model_data, "SOC")

    assert model_data.get_operating_condition_mode() == "SOC"
    assert model_data.get_operating_condition("num_occupants") == 3
    assert model_data.get_building_detail("num_occupants") == 3


def test_apply_operating_conditions_whole_murb():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    model_data = ModelData()
    model_data.set_building_details(
        {
            "building_type": "whole-murb",
            "res_units": 10,
            "common_space_area": 50.0,
        }
    )

    apply_operating_conditions(h2k_dict, model_data, "SOC")

    assert model_data.get_operating_condition("num_occupants") == 20
    assert model_data.get_building_detail("murb_units") == 10


def test_roc_applies_hot_water_reductions_without_h2k_section():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    soc = resolve_operating_parameters(h2k_dict, "SOC", "house")
    roc = resolve_operating_parameters(h2k_dict, "ROC", "house")

    assert roc["annual_elec_refrigerator"] == soc["annual_elec_refrigerator"]
    assert roc["daily_clothes_washer_reduction"] == ROC_HOT_WATER_REDUCTION["clothes_washer"]
    assert roc["low_flow_shower_reduction"] == ROC_HOT_WATER_REDUCTION["low_flow_showers"]


def test_roc_murb_does_not_double_scale_electrical_targets():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    soc = resolve_operating_parameters(h2k_dict, "SOC", "whole-murb", num_units=4)
    roc = resolve_operating_parameters(h2k_dict, "ROC", "whole-murb", num_units=4)

    assert roc["annual_elec_refrigerator"] == soc["annual_elec_refrigerator"]
    assert roc["daily_elec_interior_lighting"] == soc["daily_elec_interior_lighting"]


def test_roc_h2k_overrides_are_per_unit_and_scaled_once_for_murb():
    h2k_dict = {
        "HouseFile": {
            "Program": {
                "Options": {
                    "ReducedOperatingConditions": {
                        "Lighting": {"@value": "1.2"},
                        "ApplianceConsumption": {"@refrigerator": "500"},
                    }
                }
            }
        }
    }
    roc = resolve_operating_parameters(h2k_dict, "ROC", "whole-murb", num_units=4)

    assert roc["daily_elec_interior_lighting"] == pytest.approx(4.8)
    assert roc["annual_elec_refrigerator"] == pytest.approx(2000.0)


def test_roc_hot_water_reduction_stored_per_unit_for_murb():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    roc = resolve_operating_parameters(h2k_dict, "ROC", "whole-murb", num_units=4)

    assert roc["daily_clothes_washer_reduction"] == ROC_HOT_WATER_REDUCTION["clothes_washer"]
    assert roc["low_flow_shower_reduction"] == ROC_HOT_WATER_REDUCTION["low_flow_showers"]


def test_get_hot_water_reduction_scales_for_building_scope():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    model_data = ModelData()
    model_data.set_building_details({"building_type": "whole-murb", "res_units": 4})
    apply_operating_conditions(h2k_dict, model_data, "ROC")

    building_occ = model_data.get_operating_condition("num_occupants")
    per_unit = model_data.get_operating_condition("daily_clothes_washer_reduction")

    assert get_hot_water_reduction(model_data, "daily_clothes_washer_reduction", building_occ) == (
        per_unit * 4
    )
    assert get_hot_water_reduction(model_data, "daily_clothes_washer_reduction", 2) == per_unit


def test_invalid_operating_condition_raises():
    h2k_dict = {"HouseFile": {"Program": {"Options": {}}}}
    with pytest.raises(ValueError, match="Invalid operating condition"):
        resolve_operating_parameters(h2k_dict, "HOC", "house")
