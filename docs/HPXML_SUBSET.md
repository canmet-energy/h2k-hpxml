# HPXML Subset Schema for H2K Conversion

## Overview

This document describes the streamlined HPXML v4.0 subset schema created specifically for the H2K-HPXML conversion tool. The subset contains only the 266 elements actually used by the converter, making it significantly smaller and more manageable than the full HPXML v4.0 specification.

## Purpose

The HPXML subset schema serves several important purposes:

1. **Validation**: Ensures generated HPXML files conform to the expected structure before EnergyPlus simulation
2. **Documentation**: Clearly defines exactly what HPXML elements the H2K converter supports
3. **UI Generation**: Enables automatic form generation for HPXML editing or viewing tools
4. **Maintenance**: Easier to maintain and understand than tracking the full HPXML v4.0 spec
5. **Type Safety**: Can be used to generate type-safe code in various programming languages

## Key Statistics

- **Full HPXML v4.0**: ~10,000+ elements
- **H2K Subset**: 266 elements (~2.6% of full schema)
- **XSD File Size**: ~2,500 lines (vs. 50,000+ for full schema)
- **HPXML Version**: 4.0
- **Namespace**: `http://hpxmlonline.com/2023/09`

## Schema Location

```
src/h2k_hpxml/resources/schemas/hpxml_subset.xsd
```

## Major Differences from Full HPXML v4.0

### Elements Included

The subset includes only elements used by the H2K conversion:

**Building Structure** (30 elements)
- Basic building information (type, floors, area, volume)
- Occupancy details
- Site and climate data

**Enclosure** (87 elements)
- Air infiltration
- Attics and foundations
- Roofs, walls, foundation walls, rim joists
- Floors/ceilings and slabs
- Windows, skylights, doors
- Insulation and interior finishes

**HVAC Systems** (61 elements)
- Heating systems (furnaces, boilers, baseboards, heat pumps)
- Cooling systems (central AC)
- Heat pumps (air-to-air, mini-split)
- HVAC controls (thermostats, setpoints)
- Distribution systems (ducts, hydronic)

**Ventilation** (9 elements)
- Mechanical ventilation fans
- Heat recovery ventilators (HRVs)
- Exhaust-only systems

**Water Heating** (13 elements)
- Water heating systems
- Hot water distribution
- Water fixtures

**Appliances** (23 elements)
- Clothes washer/dryer
- Dishwasher
- Refrigerator
- Cooking range and oven

**Lighting & Loads** (9 elements)
- Interior/exterior lighting
- Plug loads (TVs, other equipment)

**Simulation Control** (16 elements)
- Software info
- Timestep settings
- Emissions scenarios
- Utility bill scenarios

### Elements Excluded

The following HPXML elements are **not** included in the subset:

- PV/solar generation systems
- Battery storage
- Pool and spa equipment
- Advanced window properties (frame type, gas fill, multiple panes)
- Ground-source heat pumps
- Many advanced HVAC distribution types
- Dehumidifiers and ceiling fans
- Whole-house ventilation systems (other than HRVs)
- Advanced renewable energy systems

### Simplified Enumerations

Many enumerations are restricted to only values actually used:

**FuelType**:
```xml
<xs:enumeration value="electricity"/>
<xs:enumeration value="natural gas"/>
<xs:enumeration value="propane"/>
<xs:enumeration value="fuel oil"/>
<xs:enumeration value="wood"/>
<xs:enumeration value="wood pellets"/>
```

**ResidentialFacilityType**:
```xml
<xs:enumeration value="single-family detached"/>
<xs:enumeration value="single-family attached"/>
```

**Siding** (always the same in H2K conversion):
```xml
<xs:enumeration value="wood siding"/>
```

**RoofType**:
```xml
<xs:enumeration value="asphalt or fiberglass shingles"/>
```

**InteriorFinish**:
```xml
<xs:enumeration value="gypsum board"/>
<xs:enumeration value="none"/>
```

### Added Constraints

The subset schema includes stricter constraints based on H2K conversion patterns:

**Azimuth** (restricted to cardinal and ordinal directions):
```xml
<xs:simpleType name="AzimuthType">
  <xs:restriction base="xs:integer">
    <xs:enumeration value="0"/>    <!-- North -->
    <xs:enumeration value="45"/>   <!-- NE -->
    <xs:enumeration value="90"/>   <!-- East -->
    <xs:enumeration value="135"/>  <!-- SE -->
    <xs:enumeration value="180"/>  <!-- South -->
    <xs:enumeration value="225"/>  <!-- SW -->
    <xs:enumeration value="270"/>  <!-- West -->
    <xs:enumeration value="315"/>  <!-- NW -->
  </xs:restriction>
</xs:simpleType>
```

**SystemIdentifier Pattern**:
```xml
<xs:pattern value="[A-Za-z]+[0-9]+"/>
<!-- Examples: Window1, HeatingSystem2, Wall3 -->
```

**Value Ranges**:
- `ZeroToOneDecimal`: For fractions, SHGC, absorptance, emittance
- `PositiveDecimal`: For areas, capacities, R-values
- `NonNegativeDecimal`: For optional measurements

### Custom Extension Elements

The subset includes H2K-specific extension elements:

**H2kLabel** (preserves original H2K component names):
```xml
<Window>
  <SystemIdentifier id="Window1"/>
  <!-- ... other elements ... -->
  <extension>
    <H2kLabel>Front Bay Window</H2kLabel>
  </extension>
</Window>
```

**HeatingAutosizingFactor** / **CoolingAutosizingFactor**:
```xml
<HeatingSystem>
  <!-- ... -->
  <extension>
    <HeatingAutosizingFactor>1.2</HeatingAutosizingFactor>
  </extension>
</HeatingSystem>
```

**HeatingCapacityRetention** (for heat pumps):
```xml
<HeatPump>
  <!-- ... -->
  <extension>
    <HeatingCapacityRetention>
      <Fraction>0.75</Fraction>
      <Temperature>5.0</Temperature>
    </HeatingCapacityRetention>
  </extension>
</HeatPump>
```

**WaterFixturesUsageMultiplier**:
```xml
<WaterHeating>
  <!-- ... -->
  <extension>
    <WaterFixturesUsageMultiplier>1.0</WaterFixturesUsageMultiplier>
  </extension>
</WaterHeating>
```

### Referential Integrity

The subset schema enforces referential integrity through XSD keys and keyrefs:

```xml
<!-- All SystemIdentifier/@id values must be unique -->
<xs:key name="SystemIdentifierKey">
  <xs:selector xpath=".//*"/>
  <xs:field xpath="SystemIdentifier/@id"/>
</xs:key>

<!-- @idref attributes must reference valid IDs -->
<xs:keyref name="AttachedToWallRef" refer="SystemIdentifierKey">
  <xs:selector xpath=".//AttachedToWall"/>
  <xs:field xpath="@idref"/>
</xs:keyref>
```

This ensures:
- Windows reference valid walls
- HVAC systems reference valid distribution systems
- Heat pumps reference valid backup systems
- Attics/foundations reference valid structural elements

## Using the Subset Schema

### Python Validation

```python
from h2k_hpxml.utils.hpxml_validator import validate_hpxml

# Validate a single file
result = validate_hpxml("output.xml")

if result.is_valid:
    print("✓ Valid HPXML file")
else:
    print(f"✗ Found {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  Line {error.line}: {error.message}")
```

### Command-Line Validation

```bash
# Validate a single file
python -m h2k_hpxml.utils.hpxml_validator output.xml

# Batch validate a directory
python -m h2k_hpxml.utils.hpxml_validator --batch output_folder/

# Recursive validation with verbose output
python -m h2k_hpxml.utils.hpxml_validator --batch output/ --recursive --verbose
```

### Integration in Conversion Pipeline

```python
from h2k_hpxml.core.translator import h2ktohpxml
from h2k_hpxml.utils.hpxml_validator import validate_hpxml

# Convert H2K to HPXML
hpxml_path = h2ktohpxml("input.h2k", output_path="output.xml")

# Validate the result
result = validate_hpxml(hpxml_path)

if not result.is_valid:
    print("Warning: Generated HPXML has validation errors")
    print(result.format_errors())
```

## Schema Structure

### Root Element

```xml
<HPXML xmlns="http://hpxmlonline.com/2023/09" schemaVersion="4.0">
  <XMLTransactionHeaderInformation>
    <!-- Metadata about file generation -->
  </XMLTransactionHeaderInformation>

  <SoftwareInfo>
    <!-- Simulation control and scenarios -->
  </SoftwareInfo>

  <Building>
    <!-- Building details (one or more) -->
  </Building>
</HPXML>
```

### Building Hierarchy

```
Building
├── BuildingID [@id]
├── Site / SiteID [@id]
├── ProjectStatus / EventType
└── BuildingDetails
    ├── BuildingSummary
    │   ├── Site (location, climate, soil)
    │   ├── BuildingOccupancy
    │   └── BuildingConstruction
    ├── ClimateandRiskZones
    │   └── WeatherStation
    ├── Enclosure
    │   ├── AirInfiltration
    │   ├── Attics / Attic
    │   ├── Foundations / Foundation
    │   ├── Roofs / Roof
    │   ├── Walls / Wall
    │   ├── FoundationWalls / FoundationWall
    │   ├── RimJoists / RimJoist
    │   ├── Floors / Floor
    │   ├── Slabs / Slab
    │   ├── Windows / Window
    │   ├── Skylights / Skylight
    │   └── Doors / Door
    ├── Systems
    │   ├── HVAC
    │   │   ├── HVACPlant
    │   │   │   ├── PrimarySystems
    │   │   │   ├── HeatingSystem
    │   │   │   ├── CoolingSystem
    │   │   │   └── HeatPump
    │   │   ├── HVACControl
    │   │   └── HVACDistribution
    │   ├── MechanicalVentilation
    │   │   └── VentilationFans / VentilationFan
    │   └── WaterHeating
    │       ├── WaterHeatingSystem
    │       ├── HotWaterDistribution
    │       └── WaterFixture
    ├── Appliances
    │   ├── ClothesWasher
    │   ├── ClothesDryer
    │   ├── Dishwasher
    │   ├── Refrigerator
    │   ├── CookingRange
    │   └── Oven
    ├── Lighting
    │   └── LightingGroup
    └── MiscLoads
        └── PlugLoad
```

## Common Validation Errors

### Missing Required Elements

```
Error: Element 'Building': Missing child element 'BuildingID'
Fix: Ensure every Building has a BuildingID element with an id attribute
```

### Invalid Azimuth Value

```
Error: Element 'Azimuth': '123' is not a valid value
Fix: Use only 0, 45, 90, 135, 180, 225, 270, or 315
```

### Broken References

```
Error: Key 'SystemIdentifierKey' not satisfied
Fix: Ensure @idref attributes reference existing SystemIdentifier/@id values
```

### Invalid SystemIdentifier Pattern

```
Error: Element 'SystemIdentifier', attribute 'id': 'Window_1' does not match pattern
Fix: Use format like 'Window1' (letters followed by numbers, no underscores)
```

### Out of Range Values

```
Error: Element 'SHGC': Value '1.5' is greater than maximum '1'
Fix: SHGC must be between 0 and 1
```

## Testing

Comprehensive tests are available in:
```
tests/unit/test_hpxml_validation.py
```

Run tests with:
```bash
pytest tests/unit/test_hpxml_validation.py -v
```

## Generating New XSD from Code

If you modify the conversion code and add new HPXML elements, you'll need to update the subset schema:

1. **Identify new elements**: Review your code changes in `src/h2k_hpxml/components/` and `src/h2k_hpxml/core/processors/`

2. **Add to schema**: Update `src/h2k_hpxml/resources/schemas/hpxml_subset.xsd` with new element definitions

3. **Test validation**: Run validation tests to ensure existing files still validate

4. **Update documentation**: Document new elements in this file

## Future Enhancements

Potential improvements to the subset schema:

1. **Stricter Validation**: Add more constraints based on HPXML v4.0 schematron rules
2. **Better Error Messages**: Custom error messages for common issues
3. **UI Schema**: Generate JSON Schema for web-based form generation
4. **Multiple Versions**: Support validation of different HPXML versions (3.x, 4.0, 4.1)
5. **Conditional Constraints**: Add context-dependent validation (e.g., heat pump backup requirements)

## References

- **Full HPXML Specification**: https://hpxml.nrel.gov/
- **HPXML v4.0 Schema**: https://github.com/NREL/OpenStudio-HPXML
- **H2K Documentation**: https://www.nrcan.gc.ca/energy-efficiency/energuide-canada/21006
- **EnergyPlus**: https://energyplus.net/

## License

This subset schema is derived from HPXML v4.0 and maintains compatibility with the HPXML license. The schema is provided as part of the H2K-HPXML conversion tool for use with Canadian housing energy modeling.

## Maintenance

The subset schema is maintained by the H2K-HPXML project team. For issues or questions:

- **GitHub Issues**: https://github.com/[your-org]/h2k-hpxml/issues
- **Schema Location**: `src/h2k_hpxml/resources/schemas/hpxml_subset.xsd`
- **Validator Code**: `src/h2k_hpxml/utils/hpxml_validator.py`
- **Tests**: `tests/unit/test_hpxml_validation.py`

---

**Last Updated**: January 2025
**Schema Version**: HPXML v4.0 Subset
**Document Version**: 1.0
