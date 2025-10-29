# H2K-HPXML Documentation

Welcome to the complete documentation for H2K-HPXML, the Canadian tool for converting Hot2000 (H2K) building energy models to HPXML format for EnergyPlus simulation.

## 📜 [Background](docs/BACKGROUND.md)

## 📊 Project Status

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Phase 1: Loads** | ✅ Complete | [Status](docs/status/status.md) |
| **Phase 2: HVAC Systems** | ✅ Complete | [Report](docs/reports/H2k-HPXML-Systems-Report.pdf) |
| **Phase 3: Multi-Unit Buildings** | 🔄 Planned | TBD |

## Current Capabilities
- ✅ Single zone simulation to mimic Hot2000 approach for validation. 
- ✅ Building envelope (walls, windows, doors, foundations)
- ✅ All HVAC system types (heating, cooling, ventilation)
- ✅ Domestic hot water systems
- ✅ Lighting and plug loads
- ✅ Weather data mapping (Canadian → US weather files)
- ✅ Both translation modes (SOC and ASHRAE140)
- ✅ Parallel processing for batch operations
- ✅ Comprehensive error handling and validation


## 🚀 Getting Started

New to H2K-HPXML? Start here:

- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup instructions for all platforms
- **[User Guide](docs/USER_GUIDE.md)** - Command-line usage and workflows and demo.

### Technical References
- **[API Reference](docs/API.md)** - Complete Python API/Library documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing with VSCode


## 🔍 Detailed Status & Features

### Implementation Status
- **[Current Status](docs/status/status.md)** - Detailed feature completion matrix
- **[Assumptions](docs/status/assumptions.md)** - Translation assumptions and limitations
- **[Known Issues](docs/status/issues.md)** - Current limitations and workarounds

### Technical Reports
- **[Systems Report](docs/reports/H2k-HPXML-Systems-Report.pdf)** - HVAC systems validation
- **[Presentations](docs/presentations/)** - Research presentations and results


## 🤝 Contributing

We welcome contributions! Here's how to get started:

### For Users
- **Report Issues**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
- **Request Features**: Describe your use case and requirements
- **Share Examples**: Help improve documentation with real-world examples

### For Developers
- **Read**: [Development Guide](docs/DEVELOPMENT.md) for complete setup
- **Quick Start**: Use VSCode DevContainer for instant development environment
- **Follow Standards**: Code style, testing, and documentation requirements
- **Submit PRs**: Follow the contribution workflow



## 📞 Support & Community

### Official Resources
- **GitHub Repository**: [canmet-energy/h2k-hpxml](https://github.com/canmet-energy/h2k-hpxml)
- **Issue Tracker**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
- **Releases**: [GitHub Releases](https://github.com/canmet-energy/h2k-hpxml/releases)

### Related Projects
- **OpenStudio**: [OpenStudio Documentation](https://openstudio.net/)
- **OpenStudio-HPXML**: [NREL/OpenStudio-HPXML](https://github.com/NREL/OpenStudio-HPXML)
- **HPXML Standard**: [HPXML Guide](https://hpxml-guide.readthedocs.io/)

### Citing This Work

If you use H2K-HPXML in your research, please cite:

```
NRCan/CMHC H2K-HPXML Translation Tool
Canada Mortgage and Housing Corporation and Natural Resources Canada
https://github.com/canmet-energy/h2k-hpxml
```
