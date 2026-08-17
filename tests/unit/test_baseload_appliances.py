"""Unit tests for operational clothes washer / dishwasher label derivation."""

from pathlib import Path

import pytest

from h2k_hpxml.components.baseload_appliances import (
    CW_LITERS_PER_CYCLE,
    DW_LITERS_PER_CYCLE,
    GAL_PER_L,
    calc_actual_clothes_washer_usgpd,
    calc_actual_dishwasher_usgpd,
    calc_actual_dryer_kwh,
    calc_required_clothes_washer_specs,
    calc_required_dishwasher_specs,
    get_appliances,
)
from h2k_hpxml.core import h2k_parser as h2k
from h2k_hpxml.core.model import ModelData
from h2k_hpxml.core.processors.building import process_building_details
from h2k_hpxml.core.template_loader import load_and_parse_templates


class _OperatingModelData(ModelData):
    def __init__(self, parameters):
        super().__init__()
        self._parameters = parameters

    def get_operating_condition(self, key, default=None):
        return self._parameters.get(key, default)

    def set_building_details(self, details):
        self.building_details.update(details)


@pytest.mark.parametrize(
    ("num_occupants", "cw_cycles", "dw_cycles", "cw_energy", "dw_energy"),
    [
        (3, 1.9, 1.37, 148, 260),
        (4, 1.88, 1.03, 197, 260),
    ],
)
def test_operational_label_derivation_matches_volume_and_energy_targets(
    num_occupants, cw_cycles, dw_cycles, cw_energy, dw_energy
):
    h2k_dict = {
        "HouseFile": {
            "House": {
                "BaseLoads": {
                    "WaterUsage": {
                        "ClothesWasher": {"@numberPerOccupantPerWeek": cw_cycles},
                        "DishWasher": {"@numberPerOccupantPerWeek": dw_cycles},
                    }
                }
            }
        }
    }
    model_data = _OperatingModelData(
        {
            "annual_elec_clothes_washer": cw_energy,
            "annual_elec_dishwasher": dw_energy,
        }
    )

    cw_target = (CW_LITERS_PER_CYCLE / GAL_PER_L) * cw_cycles * num_occupants / 7
    dw_target = (DW_LITERS_PER_CYCLE / GAL_PER_L) * dw_cycles * num_occupants / 7

    cw_specs = calc_required_clothes_washer_specs(h2k_dict, num_occupants, model_data)
    dw_specs = calc_required_dishwasher_specs(h2k_dict, num_occupants, model_data)

    cw_gpd = model_data.get_building_detail("clothes_washer_usgpd")
    dw_gpd = model_data.get_building_detail("dishwasher_usgpd")

    assert cw_gpd == pytest.approx(cw_target, rel=1e-9)
    assert dw_gpd == pytest.approx(dw_target, rel=1e-9)

    cw_label_kwh, cw_label_cycles, cw_capacity, cw_ghwc, cw_elec_rate, cw_gas_rate, _ = cw_specs
    dw_label_kwh, dw_label_cycles, dw_capacity, dw_ghwc = dw_specs

    assert calc_actual_clothes_washer_usgpd(
        num_occupants,
        cw_label_cycles / 52,
        cw_ghwc,
        cw_gas_rate,
        cw_elec_rate,
        cw_capacity,
        cw_label_kwh,
    ) == pytest.approx(cw_target, rel=1e-9)

    assert calc_actual_dishwasher_usgpd(
        num_occupants,
        dw_label_cycles / 52,
        dw_ghwc,
        1.09,
        dw_label_kwh,
        0.12,
        dw_capacity,
    ) == pytest.approx(dw_target, rel=1e-9)


def test_example_h2k_files_set_numberof_residents_for_operational_path():
    example = Path(__file__).resolve().parents[2] / "src" / "h2k_hpxml" / "examples" / "WizardHouse.h2k"
    h2k_str = example.read_text(encoding="utf-8")
    h2k_dict, hpxml_dict = load_and_parse_templates(h2k_str)
    model_data = ModelData()
    process_building_details(h2k_dict, hpxml_dict, model_data, "STANDARD", "SOC")

    occupancy = hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"][
        "BuildingOccupancy"
    ]
    assert "NumberofResidents" in occupancy
    assert occupancy["NumberofResidents"] == model_data.get_operating_condition("num_occupants")

    cw_cycles = h2k.get_number_field(h2k_dict, "clothes_washer_cycles_per_occ_week")
    calc_required_clothes_washer_specs(h2k_dict, occupancy["NumberofResidents"], model_data)
    assert model_data.get_building_detail("clothes_washer_usgpd") > 0


def test_house_dryer_cef_is_positive_and_matches_soc_target():
    example = Path(__file__).resolve().parents[2] / "src" / "h2k_hpxml" / "examples" / "WizardHouse.h2k"
    h2k_str = example.read_text(encoding="utf-8")
    h2k_dict, hpxml_dict = load_and_parse_templates(h2k_str)
    model_data = ModelData()
    process_building_details(h2k_dict, hpxml_dict, model_data, "STANDARD", "SOC")

    appliances = get_appliances(h2k_dict, model_data)
    dryer_cef = appliances["ClothesDryer"]["CombinedEnergyFactor"]
    assert dryer_cef > 0

    cw = appliances["ClothesWasher"]
    simulated_kwh = calc_actual_dryer_kwh(
        model_data.get_operating_condition("num_occupants"),
        cw["RatedAnnualkWh"],
        cw["Capacity"],
        cw["IntegratedModifiedEnergyFactor"],
        dryer_cef,
    )
    assert simulated_kwh == pytest.approx(
        model_data.get_operating_condition("annual_elec_clothes_dryer"), rel=1e-6
    )


@pytest.mark.parametrize("num_units", [1, 4])
def test_murb_appliances_use_usage_multiplier_and_match_building_targets(num_units):
    h2k_dict = {
        "HouseFile": {
            "House": {
                "BaseLoads": {
                    "WaterUsage": {
                        "ClothesWasher": {"@numberPerOccupantPerWeek": 1.9},
                        "DishWasher": {"@numberPerOccupantPerWeek": 1.37},
                    }
                },
                "Specifications": {
                    "NumberOf": {
                        "@dwellingUnits": num_units,
                        "@storeysInBuilding": 4,
                    }
                },
            }
        }
    }
    model_data = ModelData()
    model_data.set_building_details(
        {
            "building_type": "whole-murb" if num_units > 1 else "single-murb",
            "res_units": num_units,
            "res_facility_type": "apartment unit",
        }
    )
    from h2k_hpxml.utils.operating_conditions import apply_operating_conditions

    apply_operating_conditions(h2k_dict, model_data, "SOC")

    appliances = get_appliances(h2k_dict, model_data)
    num_occupants = model_data.get_operating_condition("num_occupants")

    cw = appliances["ClothesWasher"]
    dw = appliances["Dishwasher"]
    dryer = appliances["ClothesDryer"]
    dryer_cef = dryer["CombinedEnergyFactor"]
    assert dryer_cef > 0

    cw_mult = cw.get("extension", {}).get("UsageMultiplier", 1.0)
    dw_mult = dw.get("extension", {}).get("UsageMultiplier", 1.0)
    dryer_mult = dryer.get("extension", {}).get("UsageMultiplier", 1.0)

    cw_gpd = (
        calc_actual_clothes_washer_usgpd(
            num_occupants,
            cw["LabelUsage"],
            cw["LabelAnnualGasCost"],
            cw["LabelGasRate"],
            cw["LabelElectricRate"],
            cw["Capacity"],
            cw["RatedAnnualkWh"],
        )
        * cw_mult
    )
    assert cw_gpd == pytest.approx(model_data.get_building_detail("clothes_washer_usgpd"), rel=1e-6)

    dw_gpd = (
        calc_actual_dishwasher_usgpd(
            num_occupants,
            dw["LabelUsage"],
            dw["LabelAnnualGasCost"],
            dw["LabelGasRate"],
            dw["RatedAnnualkWh"],
            dw["LabelElectricRate"],
            dw["PlaceSettingCapacity"],
        )
        * dw_mult
    )
    assert dw_gpd == pytest.approx(model_data.get_building_detail("dishwasher_usgpd"), rel=1e-6)

    simulated_kwh = (
        calc_actual_dryer_kwh(
            num_occupants,
            cw["RatedAnnualkWh"],
            cw["Capacity"],
            cw["IntegratedModifiedEnergyFactor"],
            dryer_cef,
        )
        * dryer_mult
    )
    assert simulated_kwh == pytest.approx(
        model_data.get_operating_condition("annual_elec_clothes_dryer"), rel=1e-6
    )

    if num_units > 1:
        assert cw_mult > 1.0
        assert dw_mult > 1.0
        assert dryer_mult > 1.0
        assert cw["RatedAnnualkWh"] < 900
    else:
        assert "extension" not in cw
        assert "extension" not in dw
        assert "extension" not in dryer
