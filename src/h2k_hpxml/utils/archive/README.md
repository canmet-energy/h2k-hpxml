# Utils Archive

This directory contains utility files that have been archived as they are not actively used by the H2K-HPXML application.

## Archived Files

### `energy.py` (11 lines)
**Reason**: Not imported anywhere in the codebase
**Content**: Energy conversion factors dictionary
**Status**: Contains potentially useful constants but currently unused

### `emissions.py` (25 lines)
**Reason**: Not imported anywhere in the codebase
**Content**: Emission factors for fuel types by province
**Status**: Contains potentially useful constants but currently unused

### `cli_helpers.py` (508 lines)
**Reason**: Not imported anywhere in the codebase
**Content**: CLI utility functions for command-line interfaces
**Status**: Large utility module that was never integrated

### `h2k_weather_names.py` (175 lines)
**Reason**: Data generation script, not part of runtime application
**Content**: Script that processes weather data and generates `h2k_weather_names.csv`
**Status**: One-time data processing tool - the CSV file it generates is used by the application

## Recovery

These files can be moved back to the active utils directory if needed:

```bash
# Example: restore energy.py
mv src/h2k_hpxml/utils/archive/energy.py src/h2k_hpxml/utils/
```

## Archive Date
Files archived: July 31, 2025

## Total Lines Archived
719 lines of code moved to archive to clean up active codebase.
