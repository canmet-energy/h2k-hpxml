def get_lighting(h2k_dict, model_data):
    # building_type = model_data.get_building_detail("building_type")

    daily_elec_interior_lighting = model_data.get_operating_condition("daily_elec_interior_lighting")
    daily_elec_exterior_use = model_data.get_operating_condition("daily_elec_exterior_use")

    # TODO: account for lighting fractions to change LightingType
    return {
        "LightingGroup": [
            {
                "SystemIdentifier": {"@id": "LightingGroup1"},
                "Location": "interior",
                # "FractionofUnitsInLocation": 1, #Not when kWh is specified
                # "LightingType": {"CompactFluorescent": None},
                "Load": {
                    "Units": "kWh/year",
                    "Value": daily_elec_interior_lighting * 365,
                },
            },
            {
                "SystemIdentifier": {"@id": "LightingGroup2"},
                "Location": "exterior",
                # "FractionofUnitsInLocation": 1,#Not when kWh is specified
                # "LightingType": {"CompactFluorescent": None},
                "Load": {
                    "Units": "kWh/year",
                    "Value": daily_elec_exterior_use * 365,
                },
            },
        ]
    }


# FluorescentTube, CompactFluorescent, LightEmittingDiode
