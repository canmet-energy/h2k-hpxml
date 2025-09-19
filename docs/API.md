# H2K-HPXML API Reference

Complete API reference for using H2K-HPXML as a Python library.

## Table of Contents

- [Core API Functions](#core-api-functions)
- [Configuration API](#configuration-api)
- [Utilities and Helpers](#utilities-and-helpers)
- [Data Models](#data-models)
- [Exception Handling](#exception-handling)
- [Type Definitions](#type-definitions)
- [Examples](#examples)

## Core API Functions

### h2k_hpxml.api

Main public API for H2K to HPXML conversion.

#### convert_h2k_file()

Convert a single H2K file to HPXML format.

```python
def convert_h2k_file(
    input_path: str,
    output_path: Optional[str] = None,
    simulate: bool = True,
    mode: str = 'SOC',
    hourly_outputs: Optional[List[str]] = None,
    debug: bool = False
) -> str
```

**Parameters:**
- `input_path` (str): Path to the input H2K file
- `output_path` (str, optional): Path for the output HPXML file. If None, auto-generated based on input filename
- `simulate` (bool): Whether to run EnergyPlus simulation after conversion. Default: True
- `mode` (str): Translation mode. Options: 'SOC', 'ASHRAE140'. Default: 'SOC'
- `hourly_outputs` (List[str], optional): List of hourly output types to generate. Options: 'ALL', 'Heating', 'Cooling', 'DHW', etc.
- `debug` (bool): Enable debug logging. Default: False

**Returns:**
- `str`: Path to the generated HPXML file

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If invalid parameters are provided
- `TranslationError`: If H2K to HPXML conversion fails
- `SimulationError`: If EnergyPlus simulation fails (when simulate=True)

**Example:**
```python
from h2k_hpxml.api import convert_h2k_file

# Basic conversion
output_path = convert_h2k_file('input.h2k')

# Advanced conversion
output_path = convert_h2k_file(
    input_path='house.h2k',
    output_path='results/house.xml',
    simulate=True,
    mode='SOC',
    hourly_outputs=['ALL'],
    debug=True
)
```

#### run_full_workflow()

Run complete workflow including validation, conversion, and simulation.

```python
def run_full_workflow(
    input_path: str,
    output_directory: Optional[str] = None,
    simulate: bool = True,
    mode: str = 'SOC',
    hourly_outputs: Optional[List[str]] = None,
    parallel: bool = True,
    max_workers: Optional[int] = None
) -> Dict[str, Any]
```

**Parameters:**
- `input_path` (str): Path to H2K file or directory containing H2K files
- `output_directory` (str, optional): Output directory for results. Auto-generated if None
- `simulate` (bool): Run EnergyPlus simulation. Default: True
- `mode` (str): Translation mode. Default: 'SOC'
- `hourly_outputs` (List[str], optional): Hourly output types to generate
- `parallel` (bool): Use parallel processing for multiple files. Default: True
- `max_workers` (int, optional): Maximum number of parallel workers. Auto-detected if None

**Returns:**
- `Dict[str, Any]`: Results dictionary containing:
  - `successful_conversions` (int): Number of successful conversions
  - `failed_conversions` (int): Number of failed conversions
  - `output_files` (List[str]): List of generated output files
  - `errors` (List[str]): List of error messages for failed conversions
  - `processing_time` (float): Total processing time in seconds

**Example:**
```python
from h2k_hpxml.api import run_full_workflow

# Process single file
results = run_full_workflow('house.h2k', simulate=True)

# Process directory with parallel processing
results = run_full_workflow(
    input_path='h2k_files/',
    output_directory='results/',
    parallel=True,
    max_workers=4
)

print(f"Processed {results['successful_conversions']} files")
```

#### batch_convert_h2k_files()

Efficiently convert multiple H2K files with progress tracking.

```python
def batch_convert_h2k_files(
    input_files: List[str],
    output_directory: str,
    simulate: bool = True,
    mode: str = 'SOC',
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `input_files` (List[str]): List of H2K file paths to convert
- `output_directory` (str): Directory for output files
- `simulate` (bool): Run EnergyPlus simulation. Default: True
- `mode` (str): Translation mode. Default: 'SOC'
- `max_workers` (int, optional): Number of parallel workers. Auto-detected if None
- `progress_callback` (Callable, optional): Function called with (completed, total) for progress tracking

**Returns:**
- `Dict[str, Any]`: Results dictionary with detailed conversion results

**Example:**
```python
from h2k_hpxml.api import batch_convert_h2k_files
import glob

def progress_tracker(completed, total):
    percentage = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percentage:.1f}%)")

h2k_files = glob.glob('*.h2k')
results = batch_convert_h2k_files(
    input_files=h2k_files,
    output_directory='output/',
    progress_callback=progress_tracker
)
```

#### validate_dependencies()

Check if required external dependencies are available.

```python
def validate_dependencies() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Validation results containing:
  - `valid` (bool): True if all dependencies are available
  - `openstudio_path` (str): Path to OpenStudio binary
  - `hpxml_path` (str): Path to OpenStudio-HPXML directory
  - `energyplus_path` (str): Path to EnergyPlus binary
  - `missing` (List[str]): List of missing dependencies

**Example:**
```python
from h2k_hpxml.api import validate_dependencies

deps = validate_dependencies()
if not deps['valid']:
    print(f"Missing dependencies: {deps['missing']}")
    # Setup dependencies or exit
else:
    print("All dependencies available")
```

## Configuration API

### h2k_hpxml.config.manager

Configuration management for H2K-HPXML.

#### ConfigManager

Main configuration class for managing settings.

```python
class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file. Uses default if None.
        """
```

**Properties:**
- `openstudio_binary` (str): Path to OpenStudio CLI binary
- `energyplus_binary` (str): Path to EnergyPlus binary
- `hpxml_os_path` (Path): Path to OpenStudio-HPXML directory
- `config_file_path` (Path): Path to the configuration file

**Methods:**

##### get()
```python
def get(self, section: str, key: str, fallback: Any = None) -> Any:
    """Get configuration value."""
```

##### set()
```python
def set(self, section: str, key: str, value: Any) -> None:
    """Set configuration value."""
```

##### get_path()
```python
def get_path(self, section: str, key: str) -> Optional[Path]:
    """Get configuration value as Path object."""
```

##### save()
```python
def save(self) -> None:
    """Save current configuration to file."""
```

**Example:**
```python
from h2k_hpxml.config.manager import ConfigManager

# Initialize configuration
config = ConfigManager()

# Access settings
print(f"OpenStudio: {config.openstudio_binary}")
print(f"Weather vintage: {config.get('weather', 'vintage')}")

# Modify settings
config.set('simulation', 'timesteps_per_hour', '6')
config.save()
```

## Utilities and Helpers

### h2k_hpxml.utils.dependencies

Dependency management utilities.

#### setup_dependencies()
```python
def setup_dependencies(auto_install: bool = False) -> bool:
    """
    Setup H2K-HPXML dependencies.

    Args:
        auto_install: Automatically download and install missing dependencies

    Returns:
        True if all dependencies are configured
    """
```

#### check_openstudio()
```python
def check_openstudio(binary_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Check OpenStudio installation status.

    Returns:
        Dictionary with status information
    """
```

### h2k_hpxml.utils.file_utils

File and path utilities.

#### find_h2k_files()
```python
def find_h2k_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Find all H2K files in a directory.

    Args:
        directory: Directory to search
        recursive: Search subdirectories

    Returns:
        List of H2K file paths
    """
```

#### create_output_directory()
```python
def create_output_directory(base_path: str, name: str) -> Path:
    """
    Create output directory with unique name if needed.

    Returns:
        Path to created directory
    """
```

### h2k_hpxml.utils.weather

Weather data utilities.

#### get_weather_file()
```python
def get_weather_file(location: str, vintage: str = 'CWEC2020') -> Optional[str]:
    """
    Get weather file path for a location.

    Args:
        location: H2K location string
        vintage: Weather data vintage (CWEC2020, EWY2020)

    Returns:
        Path to weather file or None if not found
    """
```

## Data Models

### h2k_hpxml.core.model

Core data models used throughout the translation process.

#### ModelData

Container for building data and translation state.

```python
class ModelData:
    def __init__(self):
        """Initialize empty model data."""
```

**Attributes:**
- `building_id` (str): Unique building identifier
- `counters` (Dict[str, int]): Component counters for ID generation
- `warnings` (List[str]): Warning messages collected during translation
- `hvac_systems` (List[Dict]): HVAC system data
- `zones` (List[Dict]): Thermal zone data

**Methods:**

##### increment_counter()
```python
def increment_counter(self, component_type: str) -> int:
    """
    Increment counter for component type and return new value.

    Args:
        component_type: Type of component (e.g., 'wall', 'window')

    Returns:
        New counter value
    """
```

##### add_warning_message()
```python
def add_warning_message(self, message: str) -> None:
    """Add warning message to the collection."""
```

##### get_component_id()
```python
def get_component_id(self, component_type: str, base_name: str = None) -> str:
    """
    Generate unique component ID.

    Args:
        component_type: Type of component
        base_name: Optional base name for ID

    Returns:
        Unique component ID
    """
```

**Example:**
```python
from h2k_hpxml.core.model import ModelData

model_data = ModelData()

# Generate component IDs
wall_id = model_data.get_component_id('wall', 'ExteriorWall')
# Returns: 'Wall_ExteriorWall_1'

window_counter = model_data.increment_counter('window')
# Returns: 1

# Add warnings
model_data.add_warning_message('Using default insulation value')

print(f"Warnings: {len(model_data.warnings)}")
```

## Exception Handling

### Custom Exceptions

#### TranslationError
```python
class TranslationError(Exception):
    """Raised when H2K to HPXML translation fails."""
    pass
```

#### SimulationError
```python
class SimulationError(Exception):
    """Raised when EnergyPlus simulation fails."""
    pass
```

#### ConfigurationError
```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass
```

#### DependencyError
```python
class DependencyError(Exception):
    """Raised when required dependencies are missing or invalid."""
    pass
```

**Example Exception Handling:**
```python
from h2k_hpxml.api import convert_h2k_file
from h2k_hpxml.exceptions import TranslationError, SimulationError

try:
    result = convert_h2k_file('input.h2k', simulate=True)
    print(f"Success: {result}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except TranslationError as e:
    print(f"Translation failed: {e}")
except SimulationError as e:
    print(f"Simulation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Type Definitions

### Common Types

```python
from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path

# Translation mode
TranslationMode = Literal['SOC', 'ASHRAE140']

# Hourly output types
HourlyOutputType = Literal[
    'ALL', 'Heating', 'Cooling', 'DHW', 'Lighting',
    'InteriorEquipment', 'Fans', 'Pumps'
]

# Configuration sections
ConfigSection = Literal['paths', 'simulation', 'weather', 'logging']

# Component types
ComponentType = Literal[
    'wall', 'window', 'door', 'foundation', 'roof', 'floor',
    'hvac_heating', 'hvac_cooling', 'dhw', 'ventilation'
]

# Result dictionary type
ConversionResult = Dict[str, Union[int, List[str], float]]
```

### Function Signatures with Types

```python
def convert_h2k_file(
    input_path: str,
    output_path: Optional[str] = None,
    simulate: bool = True,
    mode: TranslationMode = 'SOC',
    hourly_outputs: Optional[List[HourlyOutputType]] = None,
    debug: bool = False
) -> str: ...

def batch_convert_h2k_files(
    input_files: List[str],
    output_directory: str,
    simulate: bool = True,
    mode: TranslationMode = 'SOC',
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> ConversionResult: ...
```

## Examples

### Basic Usage Examples

#### Simple Conversion
```python
from h2k_hpxml.api import convert_h2k_file

# Convert H2K to HPXML (no simulation)
hpxml_file = convert_h2k_file(
    input_path='house.h2k',
    simulate=False
)
print(f"HPXML created: {hpxml_file}")
```

#### Full Simulation Workflow
```python
from h2k_hpxml.api import convert_h2k_file

# Convert and simulate with hourly outputs
result = convert_h2k_file(
    input_path='house.h2k',
    output_path='results/house.xml',
    simulate=True,
    hourly_outputs=['Heating', 'Cooling', 'DHW']
)

# Simulation results will be in results/house/ directory
```

### Advanced Usage Examples

#### Batch Processing with Error Handling
```python
from h2k_hpxml.api import batch_convert_h2k_files
from h2k_hpxml.exceptions import TranslationError
import glob
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_archetype_files():
    """Process all archetype H2K files with robust error handling."""

    # Find all H2K files
    h2k_files = glob.glob('archetypes/**/*.h2k', recursive=True)
    logger.info(f"Found {len(h2k_files)} H2K files")

    # Progress tracking
    def progress_callback(completed, total):
        percentage = (completed / total) * 100
        logger.info(f"Progress: {completed}/{total} ({percentage:.1f}%)")

    try:
        # Process files
        results = batch_convert_h2k_files(
            input_files=h2k_files,
            output_directory='results/',
            simulate=False,  # HPXML only for speed
            max_workers=4,
            progress_callback=progress_callback
        )

        # Report results
        logger.info(f"Successfully processed: {results['successful_conversions']}")
        logger.info(f"Failed: {results['failed_conversions']}")

        if results['errors']:
            logger.error("Errors encountered:")
            for error in results['errors']:
                logger.error(f"  {error}")

        return results

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise

# Run processing
results = process_archetype_files()
```

#### Custom Configuration
```python
from h2k_hpxml.config.manager import ConfigManager
from h2k_hpxml.api import convert_h2k_file
import os

# Setup custom configuration
config = ConfigManager()

# Override settings temporarily
original_mode = config.get('simulation', 'default_mode')
config.set('simulation', 'default_mode', 'ASHRAE140')
config.set('simulation', 'timesteps_per_hour', '6')

# Or use environment variables
os.environ['H2K_SIMULATION_MODE'] = 'ASHRAE140'
os.environ['H2K_TIMESTEPS_PER_HOUR'] = '6'

try:
    # Run conversion with custom settings
    result = convert_h2k_file(
        'test_house.h2k',
        mode='ASHRAE140'
    )
    print(f"Converted with ASHRAE140 mode: {result}")

finally:
    # Restore original settings
    config.set('simulation', 'default_mode', original_mode)
    config.save()
```

#### Integration with Data Analysis
```python
from h2k_hpxml.api import run_full_workflow
import pandas as pd
import json
from pathlib import Path

def analyze_conversion_results(results_dir):
    """Analyze conversion results and create summary report."""

    results_path = Path(results_dir)
    summary_data = []

    # Process each building result
    for building_dir in results_path.iterdir():
        if not building_dir.is_dir():
            continue

        # Read annual energy data
        annual_file = building_dir / 'annual_energy.json'
        if annual_file.exists():
            with open(annual_file) as f:
                energy_data = json.load(f)

            summary_data.append({
                'building': building_dir.name,
                'total_energy_kwh': energy_data.get('total_site_energy_kwh', 0),
                'heating_kwh': energy_data.get('heating_energy_kwh', 0),
                'cooling_kwh': energy_data.get('cooling_energy_kwh', 0),
                'electricity_kwh': energy_data.get('electricity_total_kwh', 0)
            })

    # Create DataFrame for analysis
    df = pd.DataFrame(summary_data)

    # Generate summary statistics
    summary_stats = {
        'total_buildings': len(df),
        'avg_total_energy': df['total_energy_kwh'].mean(),
        'avg_heating_energy': df['heating_kwh'].mean(),
        'total_electricity': df['electricity_kwh'].sum()
    }

    return df, summary_stats

# Run analysis workflow
results = run_full_workflow(
    input_path='archetype_files/',
    output_directory='analysis_results/',
    simulate=True,
    parallel=True
)

# Analyze results
df, stats = analyze_conversion_results('analysis_results/')
print(f"Analyzed {stats['total_buildings']} buildings")
print(f"Average energy consumption: {stats['avg_total_energy']:.0f} kWh/year")
```

This API reference provides complete documentation for integrating H2K-HPXML into your Python applications, with comprehensive examples for both basic usage and advanced workflows.