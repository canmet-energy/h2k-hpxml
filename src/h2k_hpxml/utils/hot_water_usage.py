# Utility functions that calculate expected hot water usage in HPXML

from ..core import h2k_parser as h2k
from .operating_conditions import get_hot_water_reduction

# OS-HPXML specifies mixed water flow for fixtures/waste (hotwater_appliances.rb)
T_MIX_F = 105.0


def calc_hot_to_mixed_ratio(model_data) -> float:
    """Convert H2K hot-water volume targets to OS mixed-water fixture flows."""
    t_inlet_f = model_data.get_building_detail("water_heater_inlet_temp_f")
    t_set_f = model_data.get_building_detail("hot_water_setpoint_f")

    if t_inlet_f is None or t_set_f is None:
        return 1.0
    if t_set_f <= t_inlet_f:
        return 1.0
    return (T_MIX_F - t_inlet_f) / (t_set_f - t_inlet_f)


def get_fixtures_multiplier(h2k_dict, model_data):
    #Target accounts for other hot water use
    target_daily_hot_water_usgpd = h2k.get_number_field(h2k_dict, "total_daily_hot_water")
    num_occupants = model_data.get_operating_condition("num_occupants")
    low_flow_shower_reduction = get_hot_water_reduction(
        model_data, "low_flow_shower_reduction", num_occupants
    )
    low_flow_bathroom_faucet_reduction = get_hot_water_reduction(
        model_data, "low_flow_bathroom_faucet_reduction", num_occupants
    )

    clothes_washer_usgpd = model_data.get_building_detail("clothes_washer_usgpd")
    dishwasher_usgpd = model_data.get_building_detail("dishwasher_usgpd")

    target_fixture_waste_usgpd = target_daily_hot_water_usgpd - (
        clothes_washer_usgpd + dishwasher_usgpd 
    ) - low_flow_shower_reduction - low_flow_bathroom_faucet_reduction

    if target_fixture_waste_usgpd <= 0:
        model_data.add_warning_message(
            {
                "message": "The calculated fixture hot water usage requirement was below zero. Default values will be used, which will result in a discrepancy in hot water usage between HOT2000 and HPXML."
            }
        )
        return 1

    frac_low_flow_fixtures = 0  #TODO: update with ROC if applicable

    fixture_usgpd = calc_fixture_hot_water(num_occupants, frac_low_flow_fixtures)
    waste_usgpd = calc_distribution_waste(num_occupants, frac_low_flow_fixtures)

    base_mixed_water_usgpd = (fixture_usgpd + waste_usgpd)

    hot_to_mixed_ratio = calc_hot_to_mixed_ratio(model_data)

    fixtures_multiplier = target_fixture_waste_usgpd / (base_mixed_water_usgpd * hot_to_mixed_ratio)

    return fixtures_multiplier


# returns hot water fixture usage in US Gal/day
def calc_fixture_hot_water(num_occupants, frac_low_flow_fixtures):
    # Based on Operational calculation in HotWaterAppliances.get_fixtures_gpd

    ref_f_gpd = max(-4.84 + 18.6 * num_occupants, 0)

    f_eff = 1.0 - (0.05 * frac_low_flow_fixtures)

    return f_eff * ref_f_gpd


# returns hot water distribution waste usage in US Gal/day
# All Calculations use asset method for Standard hot water distribution system type
def calc_distribution_waste(
    num_occupants,
    frac_low_flow_fixtures,
):
    sys_factor = 1.0  # Always standard distribution system and pipe r value < 3

    ref_w_gpd = 7.16 * (num_occupants**0.7)

    o_frac = 0.25
    o_cd_eff = 0.0

    # ref_pipe_l = get_std_pipe_length(
    #     has_uncond_bsmnt, has_cond_bsmnt, conditioned_floor_area, num_storeys
    # )
    p_ratio = 1  # hot_water_distribution.standard_piping_length / ref_pipe_l

    o_w_gpd = ref_w_gpd * o_frac * (1.0 - o_cd_eff)  # Eq. 4.2-12
    s_w_gpd = (ref_w_gpd - ref_w_gpd * o_frac) * p_ratio * sys_factor  # Eq. 4.2-13

    wd_eff = 1.0

    f_eff = 1.0 - (0.05 * frac_low_flow_fixtures)

    mw_gpd = f_eff * (o_w_gpd + s_w_gpd * wd_eff)

    return mw_gpd


# not used because we're always using the standard pipe length so the ratio is 1
def get_std_pipe_length(has_uncond_bsmnt, has_cond_bsmnt, conditioned_floor_area, num_storeys):
    bsmnt = 0
    if has_uncond_bsmnt & (not has_cond_bsmnt):
        bsmnt = 1

    return (
        2.0 * (conditioned_floor_area / num_storeys) ** 0.5 + 10.0 * num_storeys + 5.0 * bsmnt
    )  # PipeL in ANSI 301
