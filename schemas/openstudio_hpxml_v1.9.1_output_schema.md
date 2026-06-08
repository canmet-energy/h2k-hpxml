# OpenStudio-HPXML v1.9.1 Output Schema

**Version**: 1.9.1  
**Repository**: https://github.com/NatLabRockies/OpenStudio-HPXML/tree/v1.9.1  

---

## Quick Reference

**Output Files**:
- `results_annual.csv`
- `results_timeseries.csv`

**Data Format**:
- Annual: SI units (from EnergyPlus) → Imperial units (MBtu, °F, lb, gal)
- Timeseries: Hourly values in Imperial units (kWh, kBtu, °F, cfm)
- All timestamps: ISO-8601 format (YYYY-MM-DDTHH:MM:SS)

---

## Table of Contents

1. [Annual Output Schema](#1-annual-output-schema)
   1. [Energy Use](#11-energy-use)
   2. [Fuel Use](#12-fuel-use)
   3. [End Use: Electricity](#13-end-use-electricity)
   4. [End Use: Natural Gas/Fuel Oil/Propane/Wood/Coal](#14-end-use-natural-gasfuel-oilpropanewoodcoal)
   5. [System Use](#15-system-use)
   6. [Emissions](#16-emissions)
   7. [Loads](#17-loads)
   8. [Unmet Hours](#18-unmet-hours)
   9. [Peak Electricity](#19-peak-electricity)
   10. [Peak Load](#110-peak-load)
   11. [Component Load: Heating](#111-component-load-heating)
   12. [Component Load: Cooling](#112-component-load-cooling)
   13. [Hot Water](#113-hot-water)
   14. [Resilience](#114-resilience)
   15. [HVAC Capacity](#115-hvac-capacity)
   16. [HVAC Design Temperature](#116-hvac-design-temperature)
   17. [HVAC Design Load: Heating](#117-hvac-design-load-heating)
   18. [HVAC Design Load: Cooling Sensible](#118-hvac-design-load-cooling-sensible)
   19. [HVAC Design Load: Cooling Latent](#119-hvac-design-load-cooling-latent)
   20. [HVAC Geothermal Loop](#120-hvac-geothermal-loop)
2. [Timeseries Output Schema](#2-timeseries-output-schema)
   1. [Time](#21-time)
   2. [Energy Use](#22-energy-use)
   3. [Fuel Use](#23-fuel-use)
   4. [End Use: Electricity](#24-end-use-electricity)
   5. [End Use: Other Fuels](#25-end-use-other-fuels)
   6. [System Use](#26-system-use)
   7. [Emissions](#27-emissions)
   8. [Emission Fuels](#28-emission-fuels)
   9. [Emission End Uses](#29-emission-end-uses)
   10. [Hot Water](#210-hot-water)
   11. [Loads](#211-loads)
   12. [Component Loads](#212-component-loads)
   13. [Unmet Hours](#213-unmet-hours)
   14. [Zone Temperatures](#214-zone-temperatures)
   15. [Airflows](#215-airflows)
   16. [Weather](#216-weather)
   17. [Resilience](#217-resilience)
   18. [EnergyPlus Output Variables](#218-energyplus-output-variables)
3. [HPXML → EnergyPlus Variable Mapping](#3-hpxml--energyplus-variable-mapping)
   1. [Understanding EnergyPlus Naming](#31-understanding-energyplus-naming)
   2. [Mapping Tables by Category](#32-mapping-tables-by-category)
4. [Data Extraction Process from EnergyPlus Outputs](#4-data-extraction-process-from-energyplus-outputs)
   1. [Load MessagePack Data Files](#41-load-messagepack-data-files)
   2. [Extract Annual Meter Data](#42-extract-annual-meter-data)
   3. [Extract Annual Output Variables](#43-extract-annual-output-variables)
   4. [Extract Timeseries Data](#44-extract-timeseries-data)
   5. [Extract Tabular Reports](#45-extract-tabular-reports)
   6. [Apply Post-Processing](#46-apply-post-processing)
   7. [Generate Output CSVs](#47-generate-output-csvs)
5. [Source Files](#5-source-files)

---

---

## 1. Annual Output Schema

### File Format: `results_annual.csv`

**Structure**: 2-column CSV
- Column 1: Parameter name (string)
- Column 2: Value (numeric)

**Example**:
```csv
Energy Use: Total,85.42
Fuel Use: Electricity: Total,40.34
End Use: Electricity: Heating,32.76
```

### Schema by Category

#### 1.1 Energy Use

**Pattern**: `Energy Use: {Category}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Total building energy consumption (annual).

| Parameter Name | Description |
|----------------|-------------|
| Energy Use: Total | Total energy consumption; includes any battery charging/discharging |
| Energy Use: Net | Subtracts any power produced by PV or generators |

#### 1.2 Fuel Use

**Pattern**: `Fuel Use: {FuelType}: {Category}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Fuel consumption by fuel type (annual).

| Parameter Name | Description |
|----------------|-------------|
| Fuel Use: Electricity: Total | Total electricity consumption, includes any battery charging/discharging |
| Fuel Use: Electricity: Net | Subtracts any power produced by PV or generators |
| Fuel Use: Natural Gas: Total | Natural gas consumed |
| Fuel Use: Fuel Oil: Total | Includes "fuel oil", "fuel oil 1", "fuel oil 2", "fuel oil 4", "fuel oil 5/6", "kerosene", and "diesel" |
| Fuel Use: Propane: Total | Propane consumed |
| Fuel Use: Wood Cord: Total | Wood cord consumed |
| Fuel Use: Wood Pellets: Total | Wood pellets consumed |
| Fuel Use: Coal: Total | Includes "coal", "anthracite coal", "bituminous coal", and "coke" |

#### 1.3 End Use: Electricity

**Pattern**: `End Use: Electricity: {EndUse}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Electricity consumption for each end use type. All end uses are mutually exclusive — the sum equals total electricity consumption.  
**Note**: For example, "Heating" excludes energy reported in "Heating Fans/Pumps". The sum of all end uses equals the total fuel use.

| Parameter Name | Description |
|----------------|-------------|
| End Use: Electricity: Heating | Excludes heat pump backup and fans/pumps |
| End Use: Electricity: Heating Fans/Pumps | Supply fan (air distribution) or circulating pump (hydronic distribution or geothermal loop) |
| End Use: Electricity: Heating Heat Pump Backup | Excludes heat pump backup fans/pumps |
| End Use: Electricity: Heating Heat Pump Backup Fans/Pumps | Supply fan or circulating pump during heat pump backup |
| End Use: Electricity: Cooling | Excludes fans/pumps |
| End Use: Electricity: Cooling Fans/Pumps | Supply fan (air distribution) and circulating pump (geothermal loop) |
| End Use: Electricity: Hot Water | Excludes recirc pump and solar thermal pump |
| End Use: Electricity: Hot Water Recirc Pump | Hot water recirculation pump |
| End Use: Electricity: Hot Water Solar Thermal Pump | Non-zero only when using detailed (not simple) solar thermal inputs |
| End Use: Electricity: Lighting Interior | Indoor lighting |
| End Use: Electricity: Lighting Garage | Garage lighting |
| End Use: Electricity: Lighting Exterior | Includes exterior holiday lighting |
| End Use: Electricity: Mech Vent | Excludes preheating/precooling |
| End Use: Electricity: Mech Vent Preheating | Electric preheating for ventilation |
| End Use: Electricity: Mech Vent Precooling | Electric precooling for ventilation |
| End Use: Electricity: Whole House Fan | Whole house fan |
| End Use: Electricity: Refrigerator | Refrigerator |
| End Use: Electricity: Freezer | Standalone freezer |
| End Use: Electricity: Dehumidifier | Dehumidifier |
| End Use: Electricity: Dishwasher | Dishwasher |
| End Use: Electricity: Clothes Washer | Washing machine |
| End Use: Electricity: Clothes Dryer | Electric clothes dryer |
| End Use: Electricity: Range/Oven | Electric cooking |
| End Use: Electricity: Ceiling Fan | Ceiling fans |
| End Use: Electricity: Television | TV and set-top boxes |
| End Use: Electricity: Plug Loads | Excludes independently reported plug loads (e.g., well pump) |
| End Use: Electricity: Electric Vehicle Charging | EV charging |
| End Use: Electricity: Well Pump | Well pump |
| End Use: Electricity: Pool Heater | Electric pool heater |
| End Use: Electricity: Pool Pump | Pool circulation pump |
| End Use: Electricity: Permanent Spa Heater | Electric spa heater |
| End Use: Electricity: Permanent Spa Pump | Spa circulation pump |
| End Use: Electricity: PV | Negative value for any power produced |
| End Use: Electricity: Generator | Negative value for any power produced |
| End Use: Electricity: Battery | Positive value for charging (including efficiency losses); negative value for discharging |

#### 1.4 End Use: Natural Gas/Fuel Oil/Propane/Wood/Coal

**Pattern**: `End Use: {FuelType}: {EndUse}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Fuel consumption for each end use type for non-electricity fuels. Separate parameters exist for each fuel type and end use combination.  
**Note**: {FuelType} can be: Natural Gas, Fuel Oil, Propane, Wood Cord, Wood Pellets, or Coal.

| Parameter Name (Examples with Natural Gas) | Description |
|---------------------------------------------|-------------|
| End Use: Natural Gas: Heating | Excludes heat pump backup |
| End Use: Natural Gas: Heating Heat Pump Backup | Heat pump backup heating |
| End Use: Natural Gas: Hot Water | Water heating |
| End Use: Natural Gas: Clothes Dryer | Clothes dryer |
| End Use: Natural Gas: Range/Oven | Cooking |
| End Use: Natural Gas: Mech Vent Preheating | Ventilation preheating |
| End Use: Natural Gas: Pool Heater | Pool heating |
| End Use: Natural Gas: Permanent Spa Heater | Spa heating |
| End Use: Natural Gas: Grill | Outdoor grill |
| End Use: Natural Gas: Lighting | Gas/oil lighting |
| End Use: Natural Gas: Fireplace | Fireplace |
| End Use: Natural Gas: Generator | Positive value for any fuel consumed |

#### 1.5 System Use

**Pattern**: `System Use: {SystemID}: {FuelType}: {EndUse}`  
**Unit**: kWh (for electricity) or kBtu (for other fuels)  
**Data Type**: Numeric  
**Description**: End use energy for each heating, cooling, and water heating system defined in the HPXML file. System IDs correspond to HPXML element IDs.  
**Note**: {SystemID} examples include HeatingSystem1, CoolingSystem1, HeatPump1, WaterHeatingSystem1, VentilationFan1. End uses include: Heating, Heating Fans/Pumps, Heating Heat Pump Backup, Heating Heat Pump Backup Fans/Pumps, Cooling, Cooling Fans/Pumps, Hot Water, Hot Water Recirc Pump, Mech Vent, Mech Vent Preheating, Mech Vent Precooling.

| Parameter Name (Examples) | Description |
|---------------------------|-------------|
| System Use: HeatingSystem1: Natural Gas: Heating | Natural gas consumption for HeatingSystem1 heating |
| System Use: HeatingSystem1: Electricity: Heating Fans/Pumps | Electricity for HeatingSystem1 fans and pumps |
| System Use: CoolingSystem1: Electricity: Cooling | Electricity for CoolingSystem1 cooling (compressor) |
| System Use: CoolingSystem1: Electricity: Cooling Fans/Pumps | Electricity for CoolingSystem1 cooling fans/pumps |
| System Use: HeatPump1: Electricity: Heating | Electricity for HeatPump1 heating mode |
| System Use: HeatPump1: Electricity: Cooling | Electricity for HeatPump1 cooling mode |
| System Use: HeatPump1: Natural Gas: Heating Heat Pump Backup | Backup heating fuel consumption for heat pump |
| System Use: WaterHeatingSystem1: Electricity: Hot Water | Electricity for water heater |
| System Use: WaterHeatingSystem1: Electricity: Hot Water Recirc Pump | Electricity for hot water recirculation pump |
| System Use: VentilationFan1: Electricity: Mech Vent | Electricity for mechanical ventilation fan |
| System Use: VentilationFan1: Electricity: Mech Vent Preheating | Electricity for ventilation air preheating |
| System Use: VentilationFan1: Electricity: Mech Vent Precooling | Electricity for ventilation air precooling |

#### 1.6 Emissions

**Pattern**: `Emissions: {EmissionsType}: {ScenarioName}: {Category}`  
**Unit**: lb (pounds)  
**Data Type**: Numeric  
**Description**: Emissions for each emissions scenario defined in the HPXML file. Multiple emissions types and scenarios may be present.  
**Note**: {EmissionsType} examples: CO2, CO2e, NOx, SO2. {ScenarioName} is user-defined (e.g., "LRMER_High_RE_Cost_15" where LRMER = Long-Run Marginal Emissions Rate, a forward-looking grid emissions methodology). Categories include: Total (includes battery charging/discharging), Net (subtracts PV/generator production), {FuelType}: Total (emissions by fuel), {FuelType}: {EndUse} (emissions by fuel and end use).

| Parameter Name (Examples: CO2e for LRMER scenario) | Description |
|---------------------------------------------------|-------------|
| Emissions: CO2e: LRMER_High_RE_Cost_15: Total | Total CO2e emissions including battery and PV |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Net | Net CO2e emissions (total minus PV/generator production) |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Total | CO2e emissions from electricity use |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Natural Gas: Total | CO2e emissions from natural gas use |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Heating | CO2e emissions from electric heating |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Cooling | CO2e emissions from cooling |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Natural Gas: Hot Water | CO2e emissions from gas water heating |
| Emissions: NOx: LRMER_High_RE_Cost_15: Total | Total NOx emissions |
| Emissions: SO2: LRMER_High_RE_Cost_15: Total | Total SO2 emissions |
| Emissions: CO2: LRMER_High_RE_Cost_15: Total | Total CO2 emissions (without equivalency factors) |

#### 1.7 Loads

**Pattern**: `Load: {LoadType}: {Component}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Annual heating, cooling, and hot water loads delivered by HVAC/DHW systems.  
**Note**: The "Delivered" loads represent the energy delivered by the HVAC/DHW system. If a system is significantly undersized, there will be unmet load not reflected by these values. If the home is not fully conditioned (e.g., a room air conditioner that only meets 30% of the cooling load), the reported load will be likewise reduced compared to a home that is fully conditioned.

| Parameter Name | Description |
|----------------|-------------|
| Load: Heating: Delivered | Total heating load delivered, including distribution losses |
| Load: Heating: Heat Pump Backup | Heating load delivered by the heat pump backup only, including distribution losses |
| Load: Cooling: Delivered | Total cooling load delivered, including distribution losses |
| Load: Hot Water: Delivered | Total hot water load delivered, including contributions by desuperheaters or solar thermal systems |
| Load: Hot Water: Tank Losses | Standby losses from water heater tank |
| Load: Hot Water: Desuperheater | Hot water load delivered by the desuperheater |
| Load: Hot Water: Solar Thermal | Hot water load delivered by the solar thermal system |

#### 1.8 Unmet Hours

**Pattern**: `Unmet Hours: {HVACType}`  
**Unit**: hr  
**Data Type**: Numeric  
**Description**: Number of hours when heating or cooling setpoints are not maintained during the heating/cooling season.  
**Note**: These numbers reflect the number of hours during the heating/cooling season when the conditioned space temperature deviates more than 0.2 deg-C (0.36 deg-F) from the heating/cooling setpoint.

| Parameter Name | Description |
|----------------|-------------|
| Unmet Hours: Heating | Number of hours where the heating setpoint is not maintained |
| Unmet Hours: Cooling | Number of hours where the cooling setpoint is not maintained |

#### 1.9 Peak Electricity

**Pattern**: `Peak Electricity: {Season} Total`  
**Unit**: W  
**Data Type**: Numeric  
**Description**: Maximum electricity demand during winter, summer, and annual periods.

| Parameter Name | Description |
|----------------|-------------|
| Peak Electricity: Winter Total | Maximum value in Dec/Jan/Feb (or Jun/Jul/Aug in the southern hemisphere) |
| Peak Electricity: Summer Total | Maximum value in Jun/Jul/Aug (or Dec/Jan/Feb in the southern hemisphere) |
| Peak Electricity: Annual Total | Maximum value in any month |

#### 1.10 Peak Load

**Pattern**: `Peak Load: {HVACType}: Delivered`  
**Unit**: kBtu/hr  
**Data Type**: Numeric  
**Description**: Peak heating and cooling loads delivered by HVAC systems.  
**Note**: The "Delivered" peak loads represent the energy delivered by the HVAC system. If a system is significantly undersized, there will be unmet peak load not reflected by these values. If the home is not fully conditioned (e.g., a room air conditioner that only meets 30% of the cooling load), the reported peak load will be likewise reduced compared to a home that is fully conditioned.

| Parameter Name | Description |
|----------------|-------------|
| Peak Load: Heating: Delivered | Includes HVAC distribution losses |
| Peak Load: Cooling: Delivered | Includes HVAC distribution losses |

#### 1.11 Component Load: Heating

**Pattern**: `Component Load: Heating: {Component}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Component loads represent the estimated contribution of different building components to the annual heating building load. The sum of component loads for heating will roughly equal the annual heating building load reported above.  
**Note**: This section is only available if the `--add-component-loads` argument is used. The argument is not used by default for faster performance. If the home is not fully conditioned, reported loads will be reduced accordingly.

| Parameter Name | Description |
|----------------|-------------|
| Component Load: Heating: Roofs | Heat gain/loss through HPXML `Roof` elements adjacent to conditioned space |
| Component Load: Heating: Ceilings | Heat gain/loss through HPXML `Floor` elements (inferred to be ceilings) adjacent to conditioned space |
| Component Load: Heating: Walls | Heat gain/loss through HPXML `Wall` elements adjacent to conditioned space |
| Component Load: Heating: Rim Joists | Heat gain/loss through HPXML `RimJoist` elements adjacent to conditioned space |
| Component Load: Heating: Foundation Walls | Heat gain/loss through HPXML `FoundationWall` elements adjacent to conditioned space |
| Component Load: Heating: Doors | Heat gain/loss through HPXML `Door` elements adjacent to conditioned space |
| Component Load: Heating: Windows Conduction | Heat gain/loss attributed to conduction through HPXML `Window` elements |
| Component Load: Heating: Windows Solar | Heat gain/loss attributed to solar gains through HPXML `Window` elements |
| Component Load: Heating: Skylights Conduction | Heat gain/loss attributed to conduction through HPXML `Skylight` elements |
| Component Load: Heating: Skylights Solar | Heat gain/loss attributed to solar gains through HPXML `Skylight` elements |
| Component Load: Heating: Floors | Heat gain/loss through HPXML `Floor` elements (inferred to be floors) adjacent to conditioned space |
| Component Load: Heating: Slabs | Heat gain/loss through HPXML `Slab` elements adjacent to conditioned space |
| Component Load: Heating: Internal Mass | Heat gain/loss from internal mass (e.g., furniture, interior walls/floors) |
| Component Load: Heating: Infiltration | Heat gain/loss from airflow induced by stack and wind effects |
| Component Load: Heating: Natural Ventilation | Heat gain/loss from airflow through operable windows |
| Component Load: Heating: Mechanical Ventilation | Heat gain/loss from airflow/fan energy from mechanical ventilation systems (including clothes dryer exhaust) |
| Component Load: Heating: Whole House Fan | Heat gain/loss from airflow due to a whole house fan |
| Component Load: Heating: Ducts | Heat gain/loss from conduction and leakage losses through supply/return ducts outside conditioned space |
| Component Load: Heating: Internal Gains | Heat gain/loss from appliances, plug loads, water heater tank losses, etc. |
| Component Load: Heating: Lighting | Heat gain/loss from lighting in the conditioned space |

#### 1.12 Component Load: Cooling

**Pattern**: `Component Load: Cooling: {Component}`  
**Unit**: MBtu  
**Data Type**: Numeric  
**Description**: Component loads represent the estimated contribution of different building components to the annual cooling building load. The sum of component loads for cooling will roughly equal the annual cooling building load reported above.  
**Note**: If the home is not fully conditioned (e.g., a room air conditioner that only meets 30% of the cooling load), the reported component loads will be likewise reduced compared to a home that is fully conditioned.

| Parameter Name | Description |
|----------------|-------------|
| Component Load: Cooling: Roofs | Heat gain/loss through HPXML `Roof` elements adjacent to conditioned space |
| Component Load: Cooling: Ceilings | Heat gain/loss through HPXML `Floor` elements (inferred to be ceilings) adjacent to conditioned space |
| Component Load: Cooling: Walls | Heat gain/loss through HPXML `Wall` elements adjacent to conditioned space |
| Component Load: Cooling: Rim Joists | Heat gain/loss through HPXML `RimJoist` elements adjacent to conditioned space |
| Component Load: Cooling: Foundation Walls | Heat gain/loss through HPXML `FoundationWall` elements adjacent to conditioned space |
| Component Load: Cooling: Doors | Heat gain/loss through HPXML `Door` elements adjacent to conditioned space |
| Component Load: Cooling: Windows Conduction | Heat gain/loss attributed to conduction through HPXML `Window` elements |
| Component Load: Cooling: Windows Solar | Heat gain/loss attributed to solar gains through HPXML `Window` elements |
| Component Load: Cooling: Skylights Conduction | Heat gain/loss attributed to conduction through HPXML `Skylight` elements |
| Component Load: Cooling: Skylights Solar | Heat gain/loss attributed to solar gains through HPXML `Skylight` elements |
| Component Load: Cooling: Floors | Heat gain/loss through HPXML `Floor` elements (inferred to be floors) adjacent to conditioned space |
| Component Load: Cooling: Slabs | Heat gain/loss through HPXML `Slab` elements adjacent to conditioned space |
| Component Load: Cooling: Internal Mass | Heat gain/loss from internal mass (e.g., furniture, interior walls/floors) |
| Component Load: Cooling: Infiltration | Heat gain/loss from airflow induced by stack and wind effects |
| Component Load: Cooling: Natural Ventilation | Heat gain/loss from airflow through operable windows |
| Component Load: Cooling: Mechanical Ventilation | Heat gain/loss from airflow/fan energy from mechanical ventilation systems (including clothes dryer exhaust) |
| Component Load: Cooling: Whole House Fan | Heat gain/loss from airflow due to a whole house fan |
| Component Load: Cooling: Ducts | Heat gain/loss from conduction and leakage losses through supply/return ducts outside conditioned space |
| Component Load: Cooling: Internal Gains | Heat gain/loss from appliances, plug loads, water heater tank losses, etc. |
| Component Load: Cooling: Lighting | Heat gain/loss from lighting in the conditioned space |

#### 1.13 Hot Water

**Pattern**: `Hot Water: {EndUse}`  
**Unit**: gal  
**Data Type**: Numeric  
**Description**: Annual hot water consumption by end use type.  
**Note**: All values are gallons of *hot* water (e.g., at water heater setpoint), not *total* water (e.g., at the fixture temperature).

| Parameter Name | Description |
|----------------|-------------|
| Hot Water: Clothes Washer | Annual hot water use by clothes washer |
| Hot Water: Dishwasher | Annual hot water use by dishwasher |
| Hot Water: Fixtures | Showers and faucets |
| Hot Water: Distribution Waste | Water wasted in distribution piping |

#### 1.14 Resilience

**Pattern**: `Resilience: {ResourceType}`  
**Unit**: hr  
**Data Type**: Numeric  
**Description**: Average resilience hours for battery storage systems.  
**Note**: Calculation is performed every timestep and then averaged, which assumes a power outage is equally likely to occur every hour of the year. The entire electric load is treated as a "critical load" that would be supported during an outage. Resilience hours are set to 0 for any timestep where the battery is not charged, even if there is sufficient PV to power the building.

| Parameter Name | Description |
|----------------|-------------|
| Resilience: Battery | Average length of time the battery state of charge can meet the electric load |

#### 1.15 HVAC Capacity

**Pattern**: `HVAC Capacity: {HVACType}`  
**Unit**: Btu/h  
**Data Type**: Numeric  
**Description**: Total HVAC system capacities (cooling, heating, and heat pump backup).  
**Note**: Autosized HVAC systems are based on design temperatures and design loads. For heat pumps with a minimum compressor lockout temperature greater than the heating design temperature (e.g., a dual-fuel heat pump in a cold climate), the compressor will be sized based on heating design loads calculated at the compressor lockout temperature. This is done to prevent unutilized capacity at temperatures below the compressor lockout temperature. Any heat pump backup will still be based on heating design loads calculated using the heating design temperature.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Capacity: Cooling | Total HVAC cooling capacity |
| HVAC Capacity: Heating | Total HVAC heating capacity |
| HVAC Capacity: Heat Pump Backup | Total HVAC heat pump backup capacity |

#### 1.16 HVAC Design Temperature

**Pattern**: `HVAC Design Temperature: {HVACType}`  
**Unit**: °F  
**Data Type**: Numeric  
**Description**: Design temperatures for heating and cooling used in HVAC equipment autosizing.  
**Note**: Design temperatures are used in the design load calculations for autosizing of HVAC equipment. Design temperatures can also be found in the `in.xml` file.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Design Temperature: Heating | 99% heating drybulb temperature |
| HVAC Design Temperature: Cooling | 1% cooling drybulb temperature |

#### 1.17 HVAC Design Load: Heating

**Pattern**: `HVAC Design Load: Heating: {Component}`  
**Unit**: Btu/h  
**Data Type**: Numeric  
**Description**: Design load outputs, used for autosizing of HVAC equipment. Design loads are based on block load ACCA Manual J calculations using design temperatures.  
**Note**: Design loads can also be found in the `in.xml` file.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Design Load: Heating: Total | Total heating design load |
| HVAC Design Load: Heating: Ducts | Heating design load for ducts |
| HVAC Design Load: Heating: Windows | Heating design load for windows |
| HVAC Design Load: Heating: Skylights | Heating design load for skylights |
| HVAC Design Load: Heating: Doors | Heating design load for doors |
| HVAC Design Load: Heating: Walls | Heating design load for walls |
| HVAC Design Load: Heating: Roofs | Heating design load for roofs |
| HVAC Design Load: Heating: Floors | Heating design load for floors |
| HVAC Design Load: Heating: Slabs | Heating design load for slabs |
| HVAC Design Load: Heating: Ceilings | Heating design load for ceilings |
| HVAC Design Load: Heating: Infiltration | Heating design load for infiltration |
| HVAC Design Load: Heating: Ventilation | Heating design load for ventilation |
| HVAC Design Load: Heating: Piping | Heating design load for hydronic piping |

#### 1.18 HVAC Design Load: Cooling Sensible

**Pattern**: `HVAC Design Load: Cooling Sensible: {Component}`  
**Unit**: Btu/h  
**Data Type**: Numeric  
**Description**: Sensible cooling design loads based on block load ACCA Manual J calculations.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Design Load: Cooling Sensible: Total | Total sensible cooling design load |
| HVAC Design Load: Cooling Sensible: Ducts | Sensible cooling design load for ducts |
| HVAC Design Load: Cooling Sensible: Windows | Sensible cooling design load for windows |
| HVAC Design Load: Cooling Sensible: Skylights | Sensible cooling design load for skylights |
| HVAC Design Load: Cooling Sensible: Doors | Sensible cooling design load for doors |
| HVAC Design Load: Cooling Sensible: Walls | Sensible cooling design load for walls |
| HVAC Design Load: Cooling Sensible: Roofs | Sensible cooling design load for roofs |
| HVAC Design Load: Cooling Sensible: Floors | Sensible cooling design load for floors |
| HVAC Design Load: Cooling Sensible: Slabs | Sensible cooling design load for slabs |
| HVAC Design Load: Cooling Sensible: Ceilings | Sensible cooling design load for ceilings |
| HVAC Design Load: Cooling Sensible: Infiltration | Sensible cooling design load for infiltration |
| HVAC Design Load: Cooling Sensible: Ventilation | Sensible cooling design load for ventilation |
| HVAC Design Load: Cooling Sensible: Internal Gains | Sensible cooling design load for internal gains |
| HVAC Design Load: Cooling Sensible: Blower Heat | Sensible cooling design load for blower fan heat |
| HVAC Design Load: Cooling Sensible: AED Excursion | Sensible cooling design load for Adequate Exposure Diversity (AED) excursion |

#### 1.19 HVAC Design Load: Cooling Latent

**Pattern**: `HVAC Design Load: Cooling Latent: {Component}`  
**Unit**: Btu/h  
**Data Type**: Numeric  
**Description**: Latent cooling design loads based on block load ACCA Manual J calculations.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Design Load: Cooling Latent: Total | Total latent cooling design load |
| HVAC Design Load: Cooling Latent: Ducts | Latent cooling design load for ducts |
| HVAC Design Load: Cooling Latent: Infiltration | Latent cooling design load for infiltration |
| HVAC Design Load: Cooling Latent: Ventilation | Latent cooling design load for ventilation |
| HVAC Design Load: Cooling Latent: Internal Gains | Latent cooling design load for internal gains |

#### 1.20 HVAC Geothermal Loop

**Pattern**: `HVAC Geothermal Loop: {Parameter}`  
**Unit**: count or ft  
**Data Type**: Numeric  
**Description**: Geothermal ground loop sizing parameters (borehole count and depth).  
**Note**: Outputs for individual geothermal loops can be found in the `in.xml` file.

| Parameter Name | Description |
|----------------|-------------|
| HVAC Geothermal Loop: Borehole/Trench Count | Total number of vertical boreholes |
| HVAC Geothermal Loop: Borehole/Trench Length | Length (i.e., average depth) of each borehole |

---

## 2. Timeseries Output Schema

### File Format: `results_timeseries.csv`

**Structure**: Multi-column CSV with 8,760 rows (one per hour when timestep is one hour)
- Row 1: Column headers
- Row 2: Units
- Rows 3-8762: Hourly data

**Example**:
```csv
Time,Energy Use: Total,Fuel Use: Electricity: Total
,kBtu,kWh
2007-01-01T00:00:00,12.45,1.35
2007-01-01T01:00:00,11.89,1.28
...
```

### Column Schema

#### 2.1 Time

**Pattern**: `Time`  
**Unit**: ISO-8601  
**Data Type**: String  
**Description**: Timestamp for each hourly timestep in format YYYY-MM-DDTHH:MM:SS.

| Parameter Name | Description |
|----------------|-------------|
| Time | Timestamp (YYYY-MM-DDTHH:MM:SS) |

#### 2.2 Energy Use

**Pattern**: `Energy Use: {Category}`  
**Unit**: kBtu  
**Data Type**: Numeric  
**Description**: Total building energy consumption at each timestep.

| Parameter Name | Description |
|----------------|-------------|
| Energy Use: Total | Energy use for building total (includes any battery charging/discharging) |
| Energy Use: Net | Subtracts any power produced by PV or generators |

#### 2.3 Fuel Use

**Pattern**: `Fuel Use: {FuelType}: {Category}`  
**Unit**: kWh (electricity) or kBtu (other fuels)  
**Data Type**: Numeric  
**Description**: Fuel consumption by fuel type at each timestep.  
**Note**: Energy use for each fuel type in kBtu for fossil fuels and kWh for electricity.

| Parameter Name | Description |
|----------------|-------------|
| Fuel Use: Electricity: Total | Energy use for electricity (includes any battery charging/discharging) |
| Fuel Use: Electricity: Net | Subtracts any power produced by PV or generators |
| Fuel Use: Natural Gas: Total | Energy use for natural gas |
| Fuel Use: Fuel Oil: Total | Energy use for fuel oil |
| Fuel Use: Propane: Total | Energy use for propane |
| Fuel Use: Wood Cord: Total | Energy use for wood cord |
| Fuel Use: Wood Pellets: Total | Energy use for wood pellets |
| Fuel Use: Coal: Total | Energy use for coal |

#### 2.4 End Use: Electricity

**Pattern**: `End Use: Electricity: {EndUse}`  
**Unit**: kWh  
**Data Type**: Numeric  
**Description**: Energy use for each electricity end use type. All end uses from Annual Output Schema are available as timeseries columns.

| Parameter Name | Description |
|----------------|-------------|
| End Use: Electricity: Heating | Heating energy (excludes heat pump backup and fans/pumps) |
| End Use: Electricity: Heating Fans/Pumps | Heating system fans and pumps |
| End Use: Electricity: Heating Heat Pump Backup | Heat pump backup heating |
| End Use: Electricity: Heating Heat Pump Backup Fans/Pumps | Heat pump backup fans/pumps |
| End Use: Electricity: Cooling | Cooling energy (excludes fans/pumps) |
| End Use: Electricity: Cooling Fans/Pumps | Cooling system fans and pumps |
| End Use: Electricity: Hot Water | Water heating (excludes recirc pump) |
| End Use: Electricity: Hot Water Recirc Pump | Hot water recirculation pump |
| End Use: Electricity: Hot Water Solar Thermal Pump | Solar thermal system pump |
| End Use: Electricity: Lighting Interior | Indoor lighting |
| End Use: Electricity: Lighting Garage | Garage lighting |
| End Use: Electricity: Lighting Exterior | Exterior and holiday lighting |
| End Use: Electricity: Mech Vent | Mechanical ventilation (excludes preconditioning) |
| End Use: Electricity: Mech Vent Preheating | Ventilation preheating |
| End Use: Electricity: Mech Vent Precooling | Ventilation precooling |
| End Use: Electricity: Whole House Fan | Whole house fan |
| End Use: Electricity: Refrigerator | Refrigerator |
| End Use: Electricity: Freezer | Standalone freezer |
| End Use: Electricity: Dehumidifier | Dehumidifier |
| End Use: Electricity: Dishwasher | Dishwasher |
| End Use: Electricity: Clothes Washer | Washing machine |
| End Use: Electricity: Clothes Dryer | Electric clothes dryer |
| End Use: Electricity: Range/Oven | Electric cooking |
| End Use: Electricity: Ceiling Fan | Ceiling fans |
| End Use: Electricity: Television | TV and set-top boxes |
| End Use: Electricity: Plug Loads | Miscellaneous plug loads |
| End Use: Electricity: Electric Vehicle Charging | EV charging |
| End Use: Electricity: Well Pump | Well pump |
| End Use: Electricity: Pool Heater | Electric pool heater |
| End Use: Electricity: Pool Pump | Pool circulation pump |
| End Use: Electricity: Permanent Spa Heater | Electric spa heater |
| End Use: Electricity: Permanent Spa Pump | Spa circulation pump |
| End Use: Electricity: PV | Photovoltaic power produced (negative value) |
| End Use: Electricity: Generator | Generator power produced (negative value) |
| End Use: Electricity: Battery | Battery charging (positive) / discharging (negative) |

#### 2.5 End Use: Other Fuels

**Pattern**: `End Use: {FuelType}: {EndUse}`  
**Unit**: kBtu  
**Data Type**: Numeric  
**Fuel Types**: Natural Gas, Fuel Oil, Propane, Wood Cord, Wood Pellets, Coal  
**Description**: Energy use for each end use type for non-electricity fuels. Each fuel type has its own set of columns following the pattern above.  
**Note**: Similar columns exist for Fuel Oil, Propane, Wood Cord, Wood Pellets, and Coal, following the same pattern with different fuel type names.

| Parameter Name (Examples with Natural Gas) | Description |
|---------------------------------------------|-------------|
| End Use: Natural Gas: Heating | Natural gas heating (excludes heat pump backup) |
| End Use: Natural Gas: Heating Heat Pump Backup | Natural gas heat pump backup |
| End Use: Natural Gas: Hot Water | Natural gas water heating |
| End Use: Natural Gas: Clothes Dryer | Natural gas clothes dryer |
| End Use: Natural Gas: Range/Oven | Natural gas cooking |
| End Use: Natural Gas: Mech Vent Preheating | Natural gas ventilation preheating |
| End Use: Natural Gas: Pool Heater | Natural gas pool heater |
| End Use: Natural Gas: Permanent Spa Heater | Natural gas spa heater |
| End Use: Natural Gas: Grill | Natural gas grill |
| End Use: Natural Gas: Lighting | Natural gas lighting |
| End Use: Natural Gas: Fireplace | Natural gas fireplace |
| End Use: Natural Gas: Generator | Natural gas generator consumption |

**Note**: Similar columns exist for Fuel Oil, Propane, Wood Cord, Wood Pellets, and Coal, following the same pattern with different fuel type names.

#### 2.6 System Use

**Pattern**: `System Use: {SystemID}: {FuelType}: {EndUse}`  
**Unit**: kWh (for electricity) or kBtu (for other fuels)  
**Data Type**: Numeric  
**Description**: Energy use for each HVAC and water heating system. System IDs are defined in the HPXML file. Unit depends on fuel type.  
**Note**: Actual column names depend on system IDs defined in the HPXML file. Each heating system, cooling system, heat pump, water heater, and ventilation fan has its own set of columns.

| Parameter Name (Examples) | Description |
|---------------------------|-------------|
| System Use: HeatingSystem1: Natural Gas: Heating | Natural gas heating energy for HeatingSystem1 |
| System Use: HeatingSystem1: Natural Gas: Heating Fans/Pumps | Electric fans/pumps for HeatingSystem1 |
| System Use: CoolingSystem1: Electricity: Cooling | Cooling energy for CoolingSystem1 |
| System Use: CoolingSystem1: Electricity: Cooling Fans/Pumps | Cooling fans/pumps for CoolingSystem1 |
| System Use: HeatPump1: Electricity: Heating | Heat pump heating energy |
| System Use: HeatPump1: Electricity: Heating Fans/Pumps | Heat pump heating fans/pumps |
| System Use: HeatPump1: Electricity: Cooling | Heat pump cooling energy |
| System Use: HeatPump1: Electricity: Cooling Fans/Pumps | Heat pump cooling fans/pumps |
| System Use: WaterHeatingSystem1: Electricity: Hot Water | Electric water heater energy |
| System Use: WaterHeatingSystem1: Electricity: Hot Water Recirc Pump | Hot water recirculation pump |
| System Use: VentilationFan1: Electricity: Mech Vent Preheating | Ventilation preheating energy |

#### 2.7 Emissions

**Pattern**: `Emissions: <EmissionsType>: <ScenarioName>: {Category}`  
**Unit**: lb  
**Data Type**: Numeric  
**Description**: Emissions for each scenario defined in the HPXML file. Emissions types include CO2, CO2e, NOx, SO2, etc.  
**Note**: Column names vary based on emissions type (CO2, CO2e, NOx, SO2) and scenario name defined in HPXML file.

| Parameter Name (Examples: CO2e for LRMER scenario) | Description |
|-----------------------------------------------------|-------------|
| Emissions: CO2e: LRMER_High_RE_Cost_15: Total | Total scenario emissions (includes battery charging/discharging) |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Net | Net emissions (subtracts power produced by PV/generators) |

#### 2.8 Emission Fuels

**Pattern**: `Emissions: <EmissionsType>: <ScenarioName>: {FuelType}: Total`  
**Unit**: lb  
**Data Type**: Numeric  
**Description**: Emissions disaggregated by fuel type for each scenario defined in the HPXML file.  
**Note**: Column names vary based on emissions type and scenario name defined in HPXML file.

| Parameter Name (Examples: CO2e for LRMER scenario) | Description |
|-----------------------------------------------------|-------------|
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Total | Electricity emissions (includes battery charging/discharging) |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Net | Net electricity emissions (subtracts PV/generator production) |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Natural Gas: Total | Natural gas emissions |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Fuel Oil: Total | Fuel oil emissions |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Propane: Total | Propane emissions |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Wood Cord: Total | Wood cord emissions |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Wood Pellets: Total | Wood pellets emissions |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Coal: Total | Coal emissions |

**Note**: Column names vary based on emissions type and scenario name defined in HPXML file.

#### 2.9 Emission End Uses

**Pattern**: `Emissions: <EmissionsType>: <ScenarioName>: {FuelType}: {EndUse}`  
**Unit**: lb  
**Data Type**: Numeric  
**Description**: Emissions disaggregated by fuel type and end use for each scenario defined in the HPXML file.  
**Note**: Columns exist for each fuel type and end use combination that is present in the building. Column names vary based on emissions type and scenario name.

| Parameter Name (Examples: CO2e for LRMER scenario) | Description |
|-----------------------------------------------------|-------------|
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Heating | Emissions from electric heating |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Cooling | Emissions from cooling |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Hot Water | Emissions from electric water heating |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Natural Gas: Heating | Emissions from natural gas heating |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Natural Gas: Hot Water | Emissions from natural gas water heating |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: Refrigerator | Emissions from refrigerator |
| Emissions: CO2e: LRMER_High_RE_Cost_15: Electricity: PV | Emissions offset by PV (negative) |

#### 2.10 Hot Water

**Pattern**: `Hot Water: {EndUse}`  
**Unit**: gal  
**Data Type**: Numeric  
**Description**: Hot water consumption by end use type at each timestep.  
**Note**: Water use for each end use type in gallons.

| Parameter Name | Description |
|----------------|-------------|
| Hot Water: Clothes Washer | Water use by clothes washer |
| Hot Water: Dishwasher | Water use by dishwasher |
| Hot Water: Fixtures | Water use by fixtures (showers, sinks) |
| Hot Water: Distribution Waste | Water wasted in distribution piping |

#### 2.11 Loads

**Pattern**: `Load: {LoadType}: {Component}`  
**Unit**: kBtu  
**Data Type**: Numeric  
**Description**: Heating, cooling, and hot water loads at each timestep.  
**Note**: Heating, cooling, and hot water loads in kBtu.

| Parameter Name | Description |
|----------------|-------------|
| Load: Heating: Delivered | Heating load delivered |
| Load: Cooling: Delivered | Cooling load delivered |
| Load: Hot Water: Delivered | Hot water load delivered |
| Load: Hot Water: Tank Losses | Hot water tank standby losses |

#### 2.12 Component Loads

**Pattern**: `Component Load: {Heating|Cooling}: {Component}`  
**Unit**: kBtu  
**Data Type**: Numeric  
**Description**: Heating and cooling loads disaggregated by component. Each component contributes to both heating and cooling loads.

| Parameter Name (Examples) | Description |
|---------------------------|-------------|
| Component Load: Heating: Roofs | Heating load through roofs |
| Component Load: Heating: Walls | Heating load through walls |
| Component Load: Heating: Windows Conduction | Heating load through window conduction |
| Component Load: Heating: Infiltration | Heating load from infiltration |
| Component Load: Heating: Ducts | Heating load from duct losses |
| Component Load: Cooling: Roofs | Cooling load through roofs |
| Component Load: Cooling: Walls | Cooling load through walls |
| Component Load: Cooling: Windows Conduction | Cooling load through window conduction |
| Component Load: Cooling: Infiltration | Cooling load from infiltration |
| Component Load: Cooling: Ducts | Cooling load from duct losses |

#### 2.13 Unmet Hours

**Pattern**: `Unmet Hours: {HVACType}`  
**Unit**: hr  
**Data Type**: Numeric  
**Description**: Binary indicator (0 or 1) for whether heating/cooling setpoint is met at each timestep.  
**Note**: Binary indicator (0 or 1) for whether heating/cooling setpoint is met each timestep.

| Parameter Name | Description |
|----------------|-------------|
| Unmet Hours: Heating | Heating unmet hours (0 or 1 per timestep) |
| Unmet Hours: Cooling | Cooling unmet hours (0 or 1 per timestep) |

#### 14. Zone Temperatures

**Pattern**: `Temperature: {SpaceName}`  
**Unit**: °F  
**Data Type**: Numeric  
**Description**: Zone temperatures for each space in the building, plus heating and cooling setpoints for the conditioned space.  
**Note**: Only columns for spaces present in the building are included. Space names depend on building configuration defined in HPXML file.

| Parameter Name (Examples) | Description |
|---------------------------|-------------|
| Temperature: Conditioned Space | Conditioned space temperature |
| Temperature: Heating Setpoint | Heating thermostat setpoint |
| Temperature: Cooling Setpoint | Cooling thermostat setpoint |
| Temperature: Attic - Vented | Vented attic temperature |
| Temperature: Attic - Unvented | Unvented attic temperature |
| Temperature: Basement - Conditioned | Conditioned basement temperature |
| Temperature: Basement - Unconditioned | Unconditioned basement temperature |
| Temperature: Crawlspace - Vented | Vented crawlspace temperature |
| Temperature: Crawlspace - Unvented | Unvented crawlspace temperature |
| Temperature: Garage | Garage temperature |

#### 2.15 Airflows

**Pattern**: `Airflow: {AirflowType}`  
**Unit**: cfm  
**Data Type**: Numeric  
**Description**: Airflow rates for infiltration, mechanical ventilation (including clothes dryer exhaust), natural ventilation, and whole house fans.

| Parameter Name | Description |
|----------------|-------------|
| Airflow: Infiltration | Infiltration airflow rate (due to stack and wind effects) |
| Airflow: Mechanical Ventilation | Mechanical ventilation airflow rate (includes clothes dryer exhaust) |
| Airflow: Natural Ventilation | Natural ventilation airflow rate (through operable windows/skylights) |
| Airflow: Whole House Fan | Whole house fan airflow rate |

#### 2.16 Weather

**Pattern**: `Weather: {Variable}`  
**Unit**: Varies (°F, %, mph, Btu/(hr·ft²))  
**Data Type**: Numeric  
**Description**: Weather file data including outdoor temperatures, relative humidity, wind speed, and solar radiation at each timestep.

| Parameter Name | Description |
|----------------|-------------|
| Weather: Drybulb Temperature | Outdoor dry bulb temperature (°F) |
| Weather: Wetbulb Temperature | Outdoor wet bulb temperature (°F) |
| Weather: Relative Humidity | Outdoor relative humidity (%) |
| Weather: Wind Speed | Wind speed (mph) |
| Weather: Diffuse Solar Radiation | Diffuse solar radiation on horizontal surface (Btu/(hr·ft²)) |
| Weather: Direct Solar Radiation | Direct normal solar radiation (Btu/(hr·ft²)) |

#### 2.17 Resilience

**Pattern**: `Resilience: {OutputType}`  
**Unit**: hr  
**Data Type**: Numeric  
**Description**: Resilience outputs at each timestep (currently only average resilience hours for battery storage).

| Parameter Name | Description |
|----------------|-------------|
| Resilience: Battery | Average length of time the battery can meet the electric load (hr) |

#### 2.18 EnergyPlus Output Variables

**Pattern**: User-defined  
**Unit**: Varies  
**Data Type**: Varies  
**Description**: Any user-specified EnergyPlus output variables can be included (e.g., 'Zone People Occupant Count'). These are custom variables specified by the user.  
**Note**: Column names, units, and data types depend on the specific EnergyPlus output variables requested by the user.

---

## 3. HPXML → EnergyPlus Variable Mapping

This section shows how HPXML CSV column names map to actual EnergyPlus meters and output variables stored in MessagePack data files.

### 3.1 Understanding EnergyPlus Naming

**Meters**: Pre-aggregated energy totals with naming pattern:
```
{object_name}:{category}:{fuel_type}:Zone:{zone_name}
```

**Output Variables**: Specific simulation results:
```
{Variable Description}
```

**Note**: These names are used in the MessagePack file column headers (`msgpackData['MeterData'][frequency]['Cols']`) and are accessed by matching column indexes during data extraction.

### 3.2 Mapping Tables by Category

#### 3.2.1 Fuel Use

**Pattern**: Facility-level totals aggregate all meters of that fuel type
- `Electricity:Facility` = Sum of all electricity meters
- `NaturalGas:Facility` = Sum of all natural gas meters

**Note**: These are the highest-level aggregation meters in EnergyPlus representing total building consumption by fuel type.

| HPXML CSV Column | EnergyPlus Meter/Variable | Type |
|------------------|---------------------------|------|
| Fuel Use: Electricity: Total | `Electricity:Facility` | Meter |
| Fuel Use: Natural Gas: Total | `NaturalGas:Facility` | Meter |

#### 3.2.2 End Use: Electricity (Appliances)

**Pattern**: `{appliance_name}:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE`  
**Note**: Appliance names (e.g., "clothes dryer", "fridge") are defined by HPXML equipment objects.

| HPXML CSV Column | EnergyPlus Meter | Type |
|------------------|------------------|------|
| End Use: Electricity: Clothes Dryer | `clothes dryer:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Clothes Washer | `clothes washer:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Dishwasher | `dishwasher:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Refrigerator | `fridge:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Range/Oven | `cooking range:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Plug Loads | `misc plug loads:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Mech Vent | `mech vent:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |
| End Use: Electricity: Whole House Fan | `whole house fan:InteriorEquipment:Electricity:Zone:CONDITIONED SPACE` | Meter |

#### 3.2.3 End Use: Electricity (Lighting)

**Pattern**: 
- Interior: `interior lighting:InteriorLights:Electricity`
- Exterior: `exterior lighting:ExteriorLights:Electricity`

**Note**: Lighting meters are split between interior and exterior zones.

| HPXML CSV Column | EnergyPlus Meter | Type |
|------------------|------------------|------|
| End Use: Electricity: Lighting Interior | `interior lighting:InteriorLights:Electricity` | Meter |
| End Use: Electricity: Lighting Exterior | `exterior lighting:ExteriorLights:Electricity` | Meter |

#### 3.2.4 End Use: Electricity (HVAC)

**Pattern**: `{hvac_system}:*:Electricity:Zone:*` where `{hvac_system}` is system-specific (e.g., boiler, furnace, heat pump)  
**Note**: The wildcard `*` matches various components (fans, pumps, compressors) within the HVAC system.

| HPXML CSV Column | EnergyPlus Meter Pattern | Type |
|------------------|--------------------------|------|
| End Use: Electricity: Heating Fans/Pumps | `{hvac_system}:*:Electricity:Zone:*` (fans/pumps) | Meter |
| End Use: Electricity: Cooling | `{hvac_system}:*:Electricity:Zone:*` (compressor) | Meter |
| End Use: Electricity: Cooling Fans/Pumps | `{hvac_system}:*:Electricity:Zone:*` (cooling fans) | Meter |

#### 3.2.5 End Use: Natural Gas (HVAC & Hot Water)

**Pattern**: `{hvac_system}:*:{FuelType}:Zone:*` or `water heater energy adjustment*:InteriorEquipment:{FuelType}:Zone:*`  
**Note**: Natural gas patterns follow similar structure to electricity but with `NaturalGas` fuel type.

| HPXML CSV Column | EnergyPlus Meter Pattern | Type |
|------------------|--------------------------|------|
| End Use: Natural Gas: Heating | `{hvac_system}:*:NaturalGas:Zone:*` | Meter |
| End Use: Natural Gas: Hot Water | `water heater energy adjustment*:InteriorEquipment:NaturalGas:Zone:*` | Meter |

#### 3.2.6 Temperatures

**Pattern**: Output variables with zone-specific `KeyValue` (typically `CONDITIONED SPACE`)  
**Note**: Zone variables require a KeyValue to specify which zone the measurement applies to.

| HPXML CSV Column | EnergyPlus Output Variable | Type |
|------------------|----------------------------|------|
| Temperature: Conditioned Space | `Zone Mean Air Temperature` (KeyValue: CONDITIONED SPACE) | Variable |
| Temperature: Heating Setpoint | `Zone Thermostat Heating Setpoint Temperature` | Variable |
| Temperature: Cooling Setpoint | `Zone Thermostat Cooling Setpoint Temperature` | Variable |

#### 3.2.7 Weather Variables

**Pattern**: `Site {WeatherVariable}`  
**Note**: Weather variables are site-level measurements with no zone specification required.

| HPXML CSV Column | EnergyPlus Output Variable | Type |
|------------------|----------------------------|------|
| Weather: Drybulb Temperature | `Site Outdoor Air Drybulb Temperature` | Variable |
| Weather: Wetbulb Temperature | `Site Outdoor Air Wetbulb Temperature` | Variable |
| Weather: Relative Humidity | `Site Outdoor Air Relative Humidity` | Variable |
| Weather: Wind Speed | `Site Wind Speed` | Variable |
| Weather: Diffuse Solar Radiation | `Site Diffuse Solar Radiation Rate per Area` | Variable |
| Weather: Direct Solar Radiation | `Site Direct Solar Radiation Rate per Area` | Variable |

#### 3.2.8 Component Loads (EMS Output Variables)

**Pattern**: 
- Heating: `loads_htg_{component}_timeseries_outvar`
- Cooling: `loads_clg_{component}_timeseries_outvar`
- Components: walls, windows_conduction, windows_solar, doors, infiltration, mechvent, intgains, roofs, floors, slabs, ceilings, etc.

**Note**: EMS (Energy Management System) variables are custom-calculated component loads created by OpenStudio-HPXML to track heat transfer through individual building components.

| HPXML CSV Column | EnergyPlus EMS Output Variable | Type |
|------------------|--------------------------------|------|
| Component Load: Heating: Walls | `loads_htg_walls_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Windows Conduction | `loads_htg_windows_conduction_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Windows Solar | `loads_htg_windows_solar_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Doors | `loads_htg_doors_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Infiltration | `loads_htg_infil_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Mechanical Ventilation | `loads_htg_mechvent_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Internal Gains | `loads_htg_intgains_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Roofs | `loads_htg_roofs_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Floors | `loads_htg_floors_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Slabs | `loads_htg_slabs_timeseries_outvar` | EMS Variable |
| Component Load: Heating: Ceilings | `loads_htg_ceilings_timeseries_outvar` | EMS Variable |
| Component Load: Cooling: {Component} | `loads_clg_{component}_timeseries_outvar` | EMS Variable |

---

## 4. Data Extraction Process from EnergyPlus Outputs

OpenStudio-HPXML v1.9.1 extracts data from EnergyPlus simulation outputs using the following step-by-step process:

### 4.1 Load MessagePack Data Files

EnergyPlus generates binary MessagePack files (`.msgpack`) instead of SQL databases for performance:

```
output_dir/
├── eplusout.msgpack              # Full simulation data
├── eplusout_runperiod.msgpack    # Annual aggregated data
├── eplusout_hourly.msgpack       # Hourly timeseries (if requested)
├── eplusout_timestep.msgpack     # Sub-hourly timeseries (if requested)
└── eplusout_monthly.msgpack      # Monthly aggregated data (if requested)
```

The ReportSimulationOutput measure loads these files using Ruby's MessagePack library.

### 4.2 Extract Annual Meter Data

For annual fuel consumption (e.g., total electricity):

1. Access `msgpackData['MeterData']['RunPeriod']['Cols']` to get meter column definitions
2. Find column indexes matching desired meter names (e.g., `Electricity:Facility`)
3. Extract values from `msgpackData['MeterData']['RunPeriod']['Rows']`
4. Apply unit conversion (J → MBtu, J → kWh)

### 4.3 Extract Annual Output Variables

For annual temperatures, loads, and other variables:

1. Combine key values and variable names (e.g., `CONDITIONED SPACE:Zone Mean Air Temperature`)
2. Access `msgpackDataRunPeriod['Cols']` to find matching columns
3. Extract row data and apply unit conversions (°C → °F, J → MBtu)
4. Apply directional multiplier if variable represents negative values (e.g., PV generation)

### 4.4 Extract Timeseries Data

For hourly/timestep data:

1. Select appropriate MessagePack file based on frequency (`Hourly`, `TimeStep`, `Daily`, `Monthly`)
2. Access timeseries columns: `msgpackData['MeterData'][frequency]['Cols']`
3. Iterate through all rows: `msgpackData['MeterData'][frequency]['Rows']`
4. Aggregate matching meter/variable values for each timestep
5. Apply unit conversion and create output array (8,760 values for hourly)

### 4.5 Extract Tabular Reports

For peak values and monthly summaries:

1. Access `msgpackData['TabularReports']` array
2. Filter by report name (e.g., `Peak Electricity Total`)
3. Navigate to specific table and row names (e.g., `June`, `July`, `August`)
4. Extract maximum values from specified columns

### 4.6 Apply Post-Processing

**Note**: These are conditional transformations applied by OpenStudio-HPXML's ReportSimulationOutput measure. Not all steps apply to every simulation—each is only executed when the relevant building features or analysis options are present.

#### 4.6.1 EMS Variable Shift (Conditional)

- **When Applied**: Only if component loads are requested (via `--add-component-loads` flag)
- **Purpose**: Corrects 1-timestep reporting lag in EnergyPlus EMS (Energy Management System) output variables

#### 4.6.2 Battery Adjustments (Conditional)

- **When Applied**: Only if building has battery storage system defined in HPXML
- **Purpose**: Separates battery charging/discharging from other electricity consumption

#### 4.6.3 DSE Multipliers (Conditional)

- **When Applied**: Only if using Distribution System Efficiency (DSE) method instead of detailed duct modeling
- **Purpose**: Applies simplified efficiency adjustments to HVAC end uses

#### 4.6.4 Aggregation (Always Applied)

- **When Applied**: Every simulation
- **Purpose**: Sums system-level energy to create end-use totals

#### 4.6.5 Emissions Calculations (Conditional)

- **When Applied**: Only if emissions scenarios are defined in HPXML (`EmissionsScenarios/EmissionsScenario` elements)
- **Purpose**: Applies hourly marginal emissions factors to energy consumption

### 4.7 Generate Output CSVs

1. Round values to appropriate decimal places (3 for annual, variable for timeseries)
2. Write `results_annual.csv` with 2-column format
3. Write `results_timeseries.csv` with multi-column format including timestamps

**Key Differences from SQL Approach**:
- **No SQL queries** - Direct MessagePack binary file parsing for 10x faster I/O
- **Nested data structures** - Navigate Ruby hashes/arrays instead of relational tables
- **Inline unit conversion** - Applied during extraction rather than post-query
- **Built-in aggregation** - Ruby array methods (`map`, `sum`, `select`) handle calculations

---

## 5. Source Files

**OpenStudio-HPXML v1.9.1 Repository**: https://github.com/NREL/OpenStudio-HPXML/tree/v1.9.1

| File | Purpose |
|------|---------|
| `ReportSimulationOutput/measure.rb` | Loads MessagePack data, converts units, generates CSVs |
| `HPXMLtoOpenStudio/measure.rb` | Translates HPXML to OpenStudio model; configures which outputs EnergyPlus generates (Output:Variable requests, EMS programs) |
| `docs/source/workflow_outputs.rst` | Human-readable documentation of outputs |

---
