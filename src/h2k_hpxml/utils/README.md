# H2K-HPXML Utils

This directory contains utility modules that provide supporting functionality for the H2K-HPXML application.

## Active Utility Files

### Domain-Specific Utilities

#### `weather.py` (120 lines)
**Purpose**: Weather data processing and climate zone utilities
**Key Functions**:
- `get_climate_zone()` - Determine climate zone from location
- `get_cwec_file()` - Get weather file paths
**Usage**: Used by weather processing and CLI resilience tool

#### `units.py` (182 lines)
**Purpose**: Unit conversion utilities
**Key Functions**:
- `convert_unit()` - Convert between different unit systems
**Usage**: Used by heating system components for unit standardization

#### `hot_water_usage.py` (98 lines)
**Purpose**: Hot water usage pattern calculations
**Key Functions**:
- Hot water draw pattern calculations
- Usage scheduling utilities
**Usage**: Used by systems processor for hot water system modeling

### System Infrastructure

#### `logging.py` (139 lines)
**Purpose**: Centralized logging configuration
**Key Functions**:
- `get_logger()` - Get configured logger instance
**Usage**: Used by 10+ core modules (translator, model, processors, CLI tools)

#### `dependencies.py` (1690 lines)
**Purpose**: External dependency management system
**Key Functions**:
- `DependencyManager` - Check, install, and manage OpenStudio/OpenStudio-HPXML
- `validate_dependencies()` - Validate system dependencies
- CLI interface for dependency management (`h2k-deps` command)
**Usage**: Used by CLI tools and workflows for dependency validation

#### `common.py` (401 lines)
**Purpose**: Common utility functions and shared logic
**Key Functions**:
- Shared component processing utilities
- Common validation and helper functions
**Usage**: Internal utilities used across multiple modules

## Package Exports

The `__init__.py` file exports key functions for easy importing:

```python
from h2k_hpxml.utils import convert_unit, get_climate_zone, get_cwec_file
```

## Archived Files

See `archive/README.md` for information about utilities that have been archived (moved out of active use to reduce clutter).

## Moved to Core

The following utilities were moved to `/core` as they are fundamental to H2K parsing:
- `h2k.py` → `core/h2k_parser.py` - H2K data parsing and extraction
- `obj.py` → `core/data_utils.py` - Nested dictionary navigation

These can now be imported from:
```python
from h2k_hpxml.core import get_composite_rval, get_val
```

## Usage Patterns

- **Weather processing** uses `weather.py` for climate data handling
- **System components** use `units.py` for unit conversions
- **Hot water systems** use `hot_water_usage.py` for usage calculations
- **All modules** use `logging.py` for standardized logging
- **CLI tools** use `dependencies.py` for external dependency management
- **Multiple modules** use `common.py` for shared utility functions

## File Organization

- **Domain utilities** (< 200 lines): `weather.py`, `units.py`, `hot_water_usage.py`, `logging.py`
- **System utilities** (> 400 lines): `dependencies.py`, `common.py`
- **Archive**: `archive/` - Contains unused utilities preserved for potential future use
- **Core utilities**: Moved to `/core` - Contains H2K parsing fundamentals
