## Assumptions
- Attic/gable ceilings are assumed to not have gable walls defined in the h2k file. They are created in the translation process by assuming conventional rectangular geometry, where half the "length" ceiling input is assumed to be one side of the rectangle.
- All attics are assumed to be vented
- Area of gable ends of cathedral ceilings are assumed to have been defined within h2k wall components.
- Attic/Hip type ceilings assume that the "length" input provided is the ceiling perimeter (all edges are compressed)
- Scissor ceiling surfaces are assumed to be at half the pitch of the roof (i.e. if a roof slope is 4/12, ceiling surface slope is 2/12)
- HPXML's default occupant and appliance schedules are used.
- Split level and split entry options in HOT2000 are treated as 2 storeys when counting the number of conditioned floors in HPXML.
- The HPXML workflow states that enclosed spaces such as garages should be explicitly included in the model. However, HOT2000 files do not account for these spaces, so they are ignored in the translation process.

- The "Adjacent to unconditioned space" checkbox in HOT2000 is assumed to be equivalent to "other non-freezing space" for attached buildings, and but there is no allowable HPXML equivalent for detached buildings. Therefore, we must use "outside" for buffered wall exteriors for detached buildings unless we model the entire garage or there is another HPXML workaround


- Windows can only be attached to wall components in HPXML, not doors. The current solution is to attach windows on doors to the parent wall of the door, and subtract the window area from the door area.
- For basement walls, the AssemblyEffectiveRValue includes the concrete or wood wall portion.
- Pony wall area is calculated as `pony wall height` * `exposed basement perimeter`.
- Above slab insulation is mapped to below slab insulation in HPXML, which has no above slab option.
- For slab perimeter insulation (UnderSlabInsulation), we include any under-footing measurement in the width provided to HPXML, if applicable.
- Carpet fraction and R-value for slabs overwritten with 0, otherwise HPXML defaults to values >0.
- Standard operating conditions are hard coded for base loads.
- Appliance Energy Guide Label inputs have been reverse engineered to achieve appliance water and energy consumption results that match HOT2000's standard operating conditions.
- All "exterior use" consumption in HOT2000's baseloads are lumped under exterior lighting in HPXML.


- Heating system types require efficiency to be defined in a specific way: Furnaces and boilers require AFUE, and Stoves and Fireplaces require Percents (Steady state in h2k). These efficiency input types are not interchangeable in HPXML, but are in H2k. This means that, if an h2k furnace has its efficiency defined in terms of steady state percent, that value will be interpreted by HPXML as an AFUE value. There doesn't appear to be a way around this without an explicit relationship between the two efficiency types.
- Electric auxiliary energy (330 kWh/y for oil and 170 kWh/y for gas) overwritten with 0 kWh/year for boilers because no discernible difference in consumption is observed between homes with furnaces vs boilers in h2k.
- Hot water heating capcity will use the "input capacity" field in the hot water section if it's present. However, this field isn't always present. It's also within a section of the hot water screen called "Standby", so it's unclear if this field has the same interpretation as HPXML
- Using HPXML's built-in assumptions about hot water distribution pipe length
- Unrestricted GSHP/WSHP cutoffs are enforced by applying a switchover temp of -40C
- When a supplementary heating system's equipment type is "Other (describe)" in h2k, the "Space Heater" HPXML system is used

### Results-dependent translations
#### Boiler Electric Auxiliary Energy
- The amount of auxiliary electricity used by boiler primary heating systems is equal to the calculated electric space heating consumption for non-electric boilers, and the difference between the "primary" heating system consumption and the "total" space heating electricity consumption for electric boilers. These metrics are present in the results section of the HOT2000 file, and if a file does not have results then the auxiliary electric energy will be 0. This method does not work when an electric boiler is paired with a heat pump, as the results are not aggregated to the degree required. When a non-electric boiler is paired with a heat pump, the auxiliary electricity is equal to the "total" space heating electricity consumption minus the "heatPump"

#### Solar DHW
- HPXML requires the fraction of hot water heating load provided by solar thermal (if present). This information is only available in the results section of the h2k file. As such, files that include solar thermal systems must include results, otherwise a warning will be flagged. The fraction is calculated as the primary DHW system consumption (always solar) divided by the primary + secondary consumption.

#### Supplementary Heating Systems
- The translation looks at the total energy consumption of each supplementary heating system and compares it to the primary heating system to determine fraction of heating loads served




### Field Assumptions:
- Building Site Type = suburban
- Building Site Surroundings = stand-alone
