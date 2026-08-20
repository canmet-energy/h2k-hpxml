"""SOC/ROC operating condition parameters for H2K to HPXML translation."""


# Flow for applying operating conditions
# 1. Operating conditions not specified? Apply SOC by default
# 2. ROC specified? Apply ROC (H2K ReducedOperatingConditions overrides when present)
# 3. General specified? Apply General, where content is taken from body of h2k file: <BaseLoads>, <Temperatures>


from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from ..core.model import ModelData

logger = get_logger(__name__)

OperatingParameters = dict[str, Any]

HOT_WATER_REDUCTION_KEYS = (
    "daily_clothes_washer_reduction",
    "daily_dishwasher_reduction",
    "low_flow_shower_reduction",
    "low_flow_bathroom_faucet_reduction",
)

SOC_HOUSE_PARAMETERS: OperatingParameters = {
    "num_occupants": 3,
    "heating_setpoint": 68,  # 20C equivalent (no setback)
    "cooling_setpoint": 77,  # 25C
    # Electrical base loads (kWh/day)
    "daily_elec_interior_lighting": 2.6,
    "daily_elec_appliances": 6.3,
    "daily_elec_other_electrical": 9.7,  # Includes freezers and microwaves
    "daily_elec_exterior_use": 0.9,
    "daily_elec_common_space": 0.0,
    "daily_elec_total": 19.5,
    # Appliance breakdown (kWh/year)
    "annual_elec_refrigerator": 639,
    "annual_elec_range": 565,
    "annual_elec_clothes_washer": 148,  # 197 * 3/4
    "annual_elec_dishwasher": 260,
    "annual_elec_clothes_dryer": 687,  # 916 * 3/4
    # Daily hot water reduction (US gal/day, per dwelling unit)
    "daily_clothes_washer_reduction": 0.0,
    "daily_dishwasher_reduction": 0.0,
    "low_flow_shower_reduction": 0.0,
    "low_flow_bathroom_faucet_reduction": 0.0,
}

# Per-unit values for MURB; scaled for whole-building or single-unit simulations.
SOC_MURB_UNIT_PARAMETERS: OperatingParameters = {
    "num_occupants": 2,
    "heating_setpoint": 68,
    "cooling_setpoint": 77,
    "daily_elec_interior_lighting": 1.7,
    "daily_elec_appliances": 5.2,
    "daily_elec_other_electrical": 4.4,
    "daily_elec_exterior_use": 0.4,
    "daily_elec_common_space_per_m2": 0.086,  # kWh/m2/day
    "daily_elec_total": 11.7,
    "annual_elec_refrigerator": 639,
    "annual_elec_range": 565,
    "annual_elec_clothes_washer": 98.5,  # 197 * 2/4
    "annual_elec_dishwasher": 130,
    "annual_elec_clothes_dryer": 458,  # 916 * 2/4
    # Daily hot water reduction (US gal/day, per dwelling unit)
    "daily_clothes_washer_reduction": 0.0,
    "daily_dishwasher_reduction": 0.0,
    "low_flow_shower_reduction": 0.0,
    "low_flow_bathroom_faucet_reduction": 0.0,
}

# ROC adjustments — placeholders for future implementation.
# Amount of electrical base load if ROC is applied
# All in kWh/day of NEW TOTAL LOAD (not reduction)
ROC_ELECTRICAL_REDUCTION = {
    "interior_lighting_25_75": 1.6,  # kWh/day new total (25%-75% LED)
    "interior_lighting_over_75": 0.6,  # kWh/day new total (>75% LED)
}

# amount of hot water reduction from SOC if ROC is applied
# All in US Gal/day reduction (per dwelling unit)
ROC_HOT_WATER_REDUCTION = {
    "low_flow_showers": 5.0,  # US Gal/day reduction
    "low_flow_bathroom_faucets": 2.6,
    "clothes_washer": 4.8,
    "dishwasher": 0.8,
}

VALID_OPERATING_CONDITIONS = ("SOC", "ROC", "GENERAL")


def get_hot_water_reduction(model_data: ModelData, key: str, num_occupants: int) -> float:
    """
    Return hot water reduction (US gal/day) for the occupancy scope of a calculation.

    Reductions are stored per dwelling unit. Scale to the whole building when
    num_occupants matches the building operating-condition occupant count.
    """
    per_unit = float(model_data.get_operating_condition(key) or 0.0)
    building_occupants = model_data.get_operating_condition("num_occupants")
    if building_occupants and num_occupants >= building_occupants:
        murb_units = int(model_data.get_building_detail("murb_units") or 1)
        return per_unit * murb_units
    return per_unit


def get_soc_house_parameters() -> OperatingParameters:
    """Return SOC parameters for a single-family house (3 occupants)."""
    return dict(SOC_HOUSE_PARAMETERS)


def _get_per_unit_soc_base(building_type: str) -> OperatingParameters:
    if building_type == "house":
        return dict(SOC_HOUSE_PARAMETERS)
    return dict(SOC_MURB_UNIT_PARAMETERS)


def _scale_murb_unit_parameters_to_building(
    per_unit: OperatingParameters,
    num_units: int,
    common_space_area: float = 0.0,
) -> OperatingParameters:
    """Scale per-unit MURB SOC/ROC parameters to a whole-building simulation."""
    num_units = max(int(num_units), 1)
    common_space_load = common_space_area * per_unit["daily_elec_common_space_per_m2"]
    daily_unit_load = (
        per_unit["daily_elec_interior_lighting"]
        + per_unit["daily_elec_appliances"]
        + per_unit["daily_elec_other_electrical"]
        + per_unit["daily_elec_exterior_use"]
    ) * num_units

    scaled = {
        "num_occupants": num_units * per_unit["num_occupants"],
        "heating_setpoint": per_unit["heating_setpoint"],
        "cooling_setpoint": per_unit["cooling_setpoint"],
        "daily_elec_interior_lighting": per_unit["daily_elec_interior_lighting"] * num_units,
        "daily_elec_appliances": per_unit["daily_elec_appliances"] * num_units,
        "daily_elec_other_electrical": per_unit["daily_elec_other_electrical"] * num_units,
        "daily_elec_exterior_use": per_unit["daily_elec_exterior_use"] * num_units,
        "daily_elec_common_space": common_space_load,
        "daily_elec_total": daily_unit_load + common_space_load,
        "annual_elec_refrigerator": per_unit["annual_elec_refrigerator"] * num_units,
        "annual_elec_range": per_unit["annual_elec_range"] * num_units,
        "annual_elec_clothes_washer": per_unit["annual_elec_clothes_washer"] * num_units,
        "annual_elec_dishwasher": per_unit["annual_elec_dishwasher"] * num_units,
        "annual_elec_clothes_dryer": per_unit["annual_elec_clothes_dryer"] * num_units,
    }
    for key in HOT_WATER_REDUCTION_KEYS:
        scaled[key] = per_unit[key]
    return scaled


def get_soc_murb_unit_parameters(
    num_units: int, common_space_area: float = 0.0
) -> OperatingParameters:
    """Return SOC parameters scaled for a MURB simulation."""
    return _scale_murb_unit_parameters_to_building(
        SOC_MURB_UNIT_PARAMETERS, num_units, common_space_area
    )


def get_soc_parameters(
    building_type: str, num_units: int = 1, common_space_area: float = 0.0
) -> OperatingParameters:
    """Resolve SOC parameters from building type and unit count."""
    if building_type == "house":
        return get_soc_house_parameters()
    return get_soc_murb_unit_parameters(num_units, common_space_area)


def _apply_roc_hot_water_reductions(per_unit: OperatingParameters) -> None:
    per_unit["daily_clothes_washer_reduction"] = ROC_HOT_WATER_REDUCTION["clothes_washer"]
    per_unit["daily_dishwasher_reduction"] = ROC_HOT_WATER_REDUCTION["dishwasher"]
    per_unit["low_flow_shower_reduction"] = ROC_HOT_WATER_REDUCTION["low_flow_showers"]
    per_unit["low_flow_bathroom_faucet_reduction"] = ROC_HOT_WATER_REDUCTION[
        "low_flow_bathroom_faucets"
    ]


def apply_roc_adjustments(
    building_type: str,
    num_units: int,
    common_space_area: float,
    roc_details: dict | None,
) -> OperatingParameters:
    """
    Apply ROC modifications starting from per-unit SOC bases.

    H2K ReducedOperatingConditions values are treated as per-dwelling-unit targets.
    Whole-building MURB parameters are scaled once at the end.
    """
    num_units = max(int(num_units), 1)
    per_unit = _get_per_unit_soc_base(building_type)
    roc = roc_details or {}

    lighting = roc.get("Lighting", {}).get("@value")
    if lighting is not None:
        per_unit["daily_elec_interior_lighting"] = float(lighting)

    appliances = roc.get("ApplianceConsumption", {})
    appliance_fields = {
        "@refrigerator": "annual_elec_refrigerator",
        "@range": "annual_elec_range",
        "@clothesWasher": "annual_elec_clothes_washer",
        "@dishWasher": "annual_elec_dishwasher",
        "@clothesDryer": "annual_elec_clothes_dryer",
    }
    for h2k_key, param_key in appliance_fields.items():
        value = appliances.get(h2k_key)
        if value is not None and value != "":
            per_unit[param_key] = float(value)

    _apply_roc_hot_water_reductions(per_unit)

    # logger.debug(
    #     "Applied ROC operating parameters for %s (%s units)",
    #     building_type,
    #     num_units,
    # )

    if building_type == "house":
        return dict(per_unit)
    return _scale_murb_unit_parameters_to_building(per_unit, num_units, common_space_area)


def resolve_operating_parameters(
    h2k_dict: dict,
    operating_condition: str,
    building_type: str,
    num_units: int = 1,
    common_space_area: float = 0.0,
) -> OperatingParameters:
    """Resolve final operating parameters for the requested condition."""
    mode = operating_condition.upper()
    if mode not in VALID_OPERATING_CONDITIONS:
        raise ValueError(
            f"Invalid operating condition: {operating_condition}. "
            f"Must be one of {VALID_OPERATING_CONDITIONS}"
        )

    if mode == "GENERAL":
        raise NotImplementedError(
            "General operating condition (H2K BaseLoads/Temperatures) is not yet implemented"
        )

    if mode == "ROC":
        roc_details = (
            h2k_dict.get("HouseFile", {})
            .get("Program", {})
            .get("Options", {})
            .get("ReducedOperatingConditions")
        )
        return apply_roc_adjustments(
            building_type,
            num_units,
            common_space_area,
            roc_details if isinstance(roc_details, dict) else None,
        )

    return get_soc_parameters(building_type, num_units, common_space_area)


def _resolve_murb_unit_count(building_type: str, building_details: dict[str, Any]) -> int:
    if building_type == "house":
        return 1
    if building_type == "single-murb":
        return 1
    return int(building_details.get("res_units") or 1)


def apply_operating_conditions(h2k_dict: dict, model_data: ModelData, operating_condition: str = "SOC") -> None:
    """
    Populate model_data with operating condition parameters.

    Must be called after building type and MURB unit details are set on model_data.
    """
    building_details = model_data.building_details
    building_type = building_details.get("building_type", "house")
    num_units = _resolve_murb_unit_count(building_type, building_details)
    common_space_area = float(building_details.get("common_space_area") or 0.0) / 10.7639

    parameters = resolve_operating_parameters(
        h2k_dict,
        operating_condition,
        building_type,
        num_units,
        common_space_area,
    )

    model_data.set_operating_conditions(operating_condition.upper(), parameters)
    model_data.set_building_details(
        {
            "num_occupants": parameters["num_occupants"],
            "operating_condition": operating_condition.upper(),
            "murb_units": num_units,
        }
    )
