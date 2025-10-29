# H2K-HPXML Project Background

## Project Overview

NRCan/CMHC is investigating energy use in Canada's existing housing stock and exploring policy measures to enhance energy efficiency and affordability for Canadians. The primary tool used to evaluate building energy performance in Canada is NRCan's Hot2000 (H2K) software. H2K is a building energy simulator that estimates the annual energy consumption of homes across Canada. NRCan has also developed a comprehensive database of archetypes representing housing across the country, using over 30 years of data from the EnerGuide for housing program. This location-specific database includes more than 6,000 archetypes, each reflecting regional housing characteristics.

However, H2K has some limitations, including the inability to provide hourly energy data. H2K only produces annual energy estimates. This lack of hourly resolution restricts its capacity to support analyses of modern energy conservation measures, such as thermal and electrical storage technologies, renewable energy, advanced building automation, and other innovative solutions. Furthermore, H2K cannot assess the effects of time-of-use (TOU) electricity rates or peak demand on housing affordability.

In contrast, the software created by the U.S. Department of Energy (U.S. DOE), EnergyPlus/HPXML, provides high resolution sub-hourly outputs. EnergyPlus/HPXML was developed in 2001 to be the standard simulation tool used by the U.S. DOE to support housing and building energy analysis. Over $3M is annually invested in EnergyPlus/HPXML to support R&D, as well as national programs. It provides detailed simulation information at a sub-hourly resolution that can examine time-of-use (TOU) technologies and help examine evaluate several advanced energy conservation measures.

## Project Goals

The goal of this work is to leverage the 6000 H2K archetype model data, by translating them to EnergyPlus/HPXML. These new models will then produce sub-hourly natural gas and electricity usage profiles to better analyze the Canadian housing stock. This will create an unprecedented level of information on how these homes consume electricity and natural gas on a sub hourly basis. It can also provide estimates on the hourly temperatures these homes experience in extreme weather events.

This data could be used to better understand thermal safety measures (overheating) that could be applied to existing and new homes. The affordability of different HVAC systems combined with TOU electricity rates could show what are the most cost-effective systems based on TOU electric utility rates. It could also be used to explore new technologies such as energy storage to support electrification. This and other analyses are possible and open up a door to a wealth of analysis for housing down the road.

## Why HPXML?

HPXML, or Home Performance eXtensible Markup Language, is a standardized data format designed for the residential energy efficiency industry. It enables consistent data collection, sharing, and analysis across different software systems, tools, and stakeholders involved in home energy performance. Developed by the Building Performance Institute (BPI) and managed by the National Renewable Energy Laboratory (NREL), HPXML provides a common structure for information about home energy audits, improvements, and performance metrics. By using HPXML, organizations can streamline processes, improve data accuracy, and easily integrate with energy efficiency programs, certifications, and incentives.

More information on the HPXML standard can be found [here](https://hpxml-guide.readthedocs.io/en/latest/overview.html).

## Technical Approach

The H2K-HPXML translator converts Canadian Hot2000 building energy models to the HPXML format, which can then be simulated using EnergyPlus through the OpenStudio-HPXML workflow. This approach leverages:

- **OpenStudio SDK** - Building modeling and simulation platform
- **OpenStudio-HPXML** - NREL's HPXML implementation for residential buildings
- **EnergyPlus** - Advanced building energy simulation engine

The translation process maps H2K's building components, systems, and schedules to equivalent HPXML representations while accounting for differences in modeling approaches between Canadian and US standards.

## Development Roadmap

The overall goal of this project is to have full support of all H2K features translated to OpenStudio/EnergyPlus via HPXML format. We have taken an incremental approach to release the translator as we add functionality. This allows researchers and stakeholders to use, and evaluate the translation capabilities as we develop them.

### Phase 1: Loads Translation ✅ Complete
**Target Completion**: Summer 2024
**Status**: Completed & available for use

**Scope**:
- Schedules and occupancy patterns
- Plug loads and lighting
- Envelope characteristics (walls, windows, doors, foundations)
- Climate file mapping between Canadian and US weather data
- Default fixed HVAC systems

**Deliverables**:
- [Presentation comparing results](presentations/H2k-HPXML-20240214-V2.pdf)

### Phase 2: HVAC Systems ✅ Complete
**Target Completion**: Spring 2025
**Status**: Completed - Beta Testing

**Scope**:
- All HVAC system types supported by H2K
- All fuel types (natural gas, electricity, oil, propane, wood)
- Domestic hot water systems
- Air distribution systems
- Heat recovery ventilators

**Deliverables**:
- [Technical report comparing results](reports/H2k-HPXML-Systems-Report.pdf)
- [Presentation on systems implementation](presentations/H2k-HPXML-EPlus-Systems-Update-20250326.pdf)

### Phase 3: Multi-Unit Residential Buildings 🔄 Planned
**Target Completion**: TBD
**Status**: Not Started

**Scope**:
- Multi-unit residential building (MURB) translation
- Shared systems and equipment
- Individual unit modeling within larger buildings
- District-level energy analysis

## Current Implementation Status

A detailed list of completed sections related to the HPXML standard is available in the [status documentation](status/status.md). This includes assumptions made during translation and issues discovered during development.

**Component Versioning**: Versioning of components targeted for each OpenStudio SDK is maintained [here](https://github.com/canmet-energy/model-dev-container/blob/main/versioning.md). This ensures development and results remain consistent across component upgrades.

## Impact and Applications

The H2K-HPXML translation capability enables:

### Energy Policy Analysis
- **Time-of-Use Rate Impact**: Analyze how TOU electricity rates affect housing affordability
- **Peak Demand Analysis**: Understand when and how Canadian homes contribute to grid peak demand
- **Electrification Studies**: Model the impact of heat pump adoption and electric vehicle charging

### Advanced Technology Assessment
- **Thermal Storage**: Evaluate battery thermal storage and phase change materials
- **Electrical Storage**: Model battery systems for load shifting and resilience
- **Renewable Integration**: Assess solar PV and small wind systems on residential buildings
- **Smart Building Controls**: Analyze advanced automation and demand response

### Resilience and Safety
- **Thermal Safety**: Predict overheating risks during extreme weather events
- **Power Outage Impacts**: Model how homes perform during extended outages
- **Climate Adaptation**: Understand building performance under future climate scenarios

### Housing Stock Analysis
- **National Archetypes**: Process all 6,000+ Canadian housing archetypes for comprehensive analysis
- **Regional Variations**: Compare energy performance across Canada's diverse climate zones
- **Retrofit Potential**: Identify most effective energy efficiency measures by region and building type

## Research and Validation

The translation methodology has been validated through:

- **Comparative Analysis**: Detailed comparison of H2K vs HPXML/EnergyPlus results
- **Stakeholder Review**: Input from Canadian building energy modeling community
- **Field Data Validation**: Comparison against measured building performance data where available
- **Continuous Testing**: Automated regression testing against baseline results

All validation reports and presentations are available in the [docs/reports](reports/) and [docs/presentations](presentations/) directories.

## Project Team and Funding

This project is a collaboration between:

- **Natural Resources Canada (NRCan)** - Policy research and technical guidance
- **Canada Mortgage and Housing Corporation (CMHC)** - Housing research and implementation
- **Building Energy Modeling Community** - Technical review and validation

The project leverages significant US DOE investment in EnergyPlus/HPXML (over $3M annually) while adapting the tools for Canadian building practices and climate conditions.

## Future Directions

Beyond the current three-phase roadmap, potential future enhancements include:

- **Real-Time Integration**: Connect with smart home systems for live building performance monitoring
- **Machine Learning**: Use historical data to improve prediction accuracy and identify optimization opportunities
- **Urban Scale Modeling**: Extend from individual buildings to neighborhood and city-scale energy analysis
- **International Collaboration**: Share methodologies with other countries developing similar translation capabilities

The H2K-HPXML project represents a significant advancement in Canadian building energy analysis capabilities, providing the foundation for next-generation policy analysis and technology assessment in the residential sector.