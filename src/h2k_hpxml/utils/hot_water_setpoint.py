"""Hot water setpoint helpers shared across translation components."""

from __future__ import annotations

from ..core import h2k_parser as h2k


def resolve_hot_water_setpoint_f(h2k_dict) -> float:
    """Return the DHW setpoint in Fahrenheit from H2K baseload inputs."""
    hot_water_temperature = h2k.get_number_field(h2k_dict, "hot_water_temperature")
    hot_water_temperature_adv_uspec = h2k.get_number_field(
        h2k_dict, "hot_water_temperature_adv_uspec"
    )
    if hot_water_temperature > 0:
        return hot_water_temperature
    return hot_water_temperature_adv_uspec
