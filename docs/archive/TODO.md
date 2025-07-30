
# Development tasks todo

- Pre check to make sure the h2k file is valid (see if results section is present?)


- Update emission factors and fuel costs
- FSA lookup for suburban vs rural building site
- MURB functionality (must ensure that HPXML can handle both types)
- Account for LED lighting fractions to change LightingType
- Atypical electical loads
- Check for anything in h2k that would go under "Fuel Loads"
- Error handling if R-value is ever 0
- Ensure that "attic - vented" vs "unvented" aligns with HVAC distribution system inputs
- Update annual results checker to work with h2k files in general mode
- Check if something is happening with window R-value assumptions in the HPXML workflow ( is it making assumptions about the frame, when those are already built-in to h2k?)


# HVAC Systems to build

- Heating Systems (Type1 & Supplementary Systems)
- Cooling Systems (Air conditioning Type 2 Systems)
- Heat Pumps (ASHP, WSHP, GSHP Type 2 Systems)
- HVAC Detailed Perf. Data (not in h2k)
- Geothermal Loops (not explicit in h2k)
- HVAC Control (not explicit in h2k)
- HVAC Distribution (not explicit in h2k, sometimes implicit)
- Mechanical Ventilation Fans (Ventilation section)
- Local Ventilation Fans (range hoods and bathroom fans: supplementary ventilation systems)
- Whole House Fans (whole-house fans that provide cooling load reduction, to be investigated further)
- Water Heating Systems (Domestic Hot Water)
- Hot Water Distribution (includes DWHR)
- Water Fixtures (information on low-flow fixtures from Base loads section)
- Solar Thermal (from DHW)
- Photovoltaics (Generation section)
- Batteries (Battery specs not provided in h2k)
- Generators (not explicit in h2k)


### To-be addressed HVAC components (identified throughout translation)
- Dual fuel system (bi-energy)
- flue diameter inputs
- distribution system selection
- Combos (after heating and hot water complete)
