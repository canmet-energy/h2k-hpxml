# H2K-HPXML Python Library Guide

Complete guide for using H2K-HPXML as a Python library in your research and analysis workflows.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core API Functions](#core-api-functions)
- [Configuration Management](#configuration-management)
- [Batch Processing](#batch-processing)
- [Data Analysis Integration](#data-analysis-integration)
- [Advanced Workflows](#advanced-workflows)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Examples and Use Cases](#examples-and-use-cases)

## Installation

### For Data Analysis Projects

```bash
# Create new project with uv (recommended)
uv init my-energy-analysis
cd my-energy-analysis
uv add git+https://github.com/canmet-energy/h2k-hpxml.git@refactor pandas numpy matplotlib

# Or add to existing project
uv add git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Traditional pip installation
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### For Jupyter Notebooks

```bash
# Install in notebook environment
%pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Or with uv
%pip install --upgrade-strategy eager git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### Setup Dependencies

```python
from h2k_hpxml.utils.dependencies import validate_dependencies, setup_dependencies

# Check if dependencies are available
deps = validate_dependencies()
if not deps['valid']:
    print("Setting up dependencies...")
    setup_dependencies()
```

## Quick Start

### Basic Conversion

```python
from h2k_hpxml.api import convert_h2k_file

# Convert single file
output_path = convert_h2k_file(
    input_path='path/to/house.h2k',
    output_path='path/to/house.xml'
)
print(f"Converted to: {output_path}")
```

### Full Workflow with Simulation

```python
from h2k_hpxml.api import run_full_workflow

# Convert and simulate
results = run_full_workflow(
    input_path='path/to/house.h2k',
    simulate=True,
    hourly_outputs=['ALL']
)

print(f"Successful conversions: {results['successful_conversions']}")
print(f"Failed conversions: {results['failed_conversions']}")
print(f"Generated files: {results['output_files']}")
```

### Batch Processing

```python
from h2k_hpxml.api import batch_convert_h2k_files
import glob

# Find all H2K files
h2k_files = glob.glob('archetypes/*.h2k')

# Convert all files
results = batch_convert_h2k_files(
    input_files=h2k_files,
    output_directory='results/',
    simulate=False,  # Skip simulation for faster processing
    max_workers=4    # Parallel processing
)

print(f"Processed {len(results['successful'])} files successfully")
```

## Core API Functions

### convert_h2k_file()

Convert a single H2K file to HPXML format.

```python
from h2k_hpxml.api import convert_h2k_file

output_path = convert_h2k_file(
    input_path: str,                    # Path to H2K file
    output_path: str = None,            # Output path (auto-generated if None)
    simulate: bool = True,              # Run EnergyPlus simulation
    mode: str = 'SOC',                  # Translation mode: 'SOC' or 'ASHRAE140'
    hourly_outputs: list = None,        # Hourly output types
    debug: bool = False                 # Enable debug logging
)
```

**Returns**: String path to the generated HPXML file

### run_full_workflow()

Complete workflow including validation, conversion, and simulation.

```python
from h2k_hpxml.api import run_full_workflow

results = run_full_workflow(
    input_path: str,                    # H2K file or directory
    output_directory: str = None,       # Output directory
    simulate: bool = True,              # Run EnergyPlus simulation
    mode: str = 'SOC',                  # Translation mode
    hourly_outputs: list = None,        # Hourly output types
    parallel: bool = True,              # Use parallel processing for directories
    max_workers: int = None             # Number of parallel workers
)
```

**Returns**: Dictionary with conversion results and statistics

### batch_convert_h2k_files()

Efficient batch processing of multiple H2K files.

```python
from h2k_hpxml.api import batch_convert_h2k_files

results = batch_convert_h2k_files(
    input_files: list,                  # List of H2K file paths
    output_directory: str,              # Output directory
    simulate: bool = True,              # Run EnergyPlus simulation
    mode: str = 'SOC',                  # Translation mode
    max_workers: int = None,            # Parallel workers (auto-detected)
    progress_callback: callable = None  # Progress callback function
)
```

### validate_dependencies()

Check if required dependencies are available.

```python
from h2k_hpxml.api import validate_dependencies

deps = validate_dependencies()
print(f"Valid: {deps['valid']}")
print(f"OpenStudio: {deps['openstudio_path']}")
print(f"HPXML: {deps['hpxml_path']}")
print(f"Missing: {deps['missing']}")
```

## Configuration Management

### ConfigManager Class

```python
from h2k_hpxml.config.manager import ConfigManager

# Initialize configuration
config = ConfigManager()

# Access configuration values
print(f"OpenStudio binary: {config.openstudio_binary}")
print(f"EnergyPlus binary: {config.energyplus_binary}")
print(f"HPXML path: {config.hpxml_os_path}")

# Check specific settings
simulation_mode = config.get('simulation', 'default_mode')
weather_vintage = config.get('weather', 'vintage')
```

### Programmatic Configuration

```python
from h2k_hpxml.config.manager import ConfigManager

# Create configuration with custom settings
config = ConfigManager()

# Override settings temporarily
import os
os.environ['H2K_SIMULATION_MODE'] = 'ASHRAE140'
os.environ['H2K_OPENSTUDIO_BINARY'] = '/custom/path/to/openstudio'

# Use custom configuration
result = convert_h2k_file('input.h2k', mode='ASHRAE140')
```

## Batch Processing

### Parallel Processing Example

```python
from h2k_hpxml.api import batch_convert_h2k_files
from concurrent.futures import ThreadPoolExecutor
import glob
import os

def process_archetype_batch():
    """Process Canadian housing archetypes in parallel."""

    # Find all archetype files
    archetype_files = glob.glob('archetypes/**/*.h2k', recursive=True)
    print(f"Found {len(archetype_files)} archetype files")

    # Setup progress tracking
    def progress_callback(completed, total):
        percentage = (completed / total) * 100
        print(f"Progress: {completed}/{total} ({percentage:.1f}%)")

    # Process in batches
    batch_size = 50
    all_results = []

    for i in range(0, len(archetype_files), batch_size):
        batch = archetype_files[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}")

        results = batch_convert_h2k_files(
            input_files=batch,
            output_directory=f'results/batch_{i//batch_size}/',
            simulate=False,  # HPXML only for speed
            max_workers=os.cpu_count() - 1,
            progress_callback=progress_callback
        )

        all_results.extend(results['successful'])

    return all_results

# Run batch processing
results = process_archetype_batch()
print(f"Total processed: {len(results)}")
```

### Custom Processing Pipeline

```python
import pandas as pd
from pathlib import Path

def custom_processing_pipeline(input_dir, output_dir):
    """Custom processing with metadata tracking."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Create processing log
    processing_log = []

    for h2k_file in input_path.glob('*.h2k'):
        try:
            # Convert file
            result = convert_h2k_file(
                input_path=str(h2k_file),
                output_path=str(output_path / f"{h2k_file.stem}.xml"),
                simulate=True
            )

            # Extract metadata
            file_size = h2k_file.stat().st_size

            # Log results
            processing_log.append({
                'filename': h2k_file.name,
                'input_size_mb': file_size / 1024 / 1024,
                'output_file': result,
                'status': 'success'
            })

        except Exception as e:
            processing_log.append({
                'filename': h2k_file.name,
                'error': str(e),
                'status': 'failed'
            })

    # Save processing report
    df = pd.DataFrame(processing_log)
    df.to_csv(output_path / 'processing_report.csv', index=False)

    return df

# Run custom pipeline
report = custom_processing_pipeline('input/', 'output/')
print(report['status'].value_counts())
```

## Data Analysis Integration

### Working with Pandas

```python
import pandas as pd
import json
from pathlib import Path

def analyze_energy_results(results_dir):
    """Analyze energy simulation results using pandas."""

    results_path = Path(results_dir)
    energy_data = []

    # Process all annual energy JSON files
    for json_file in results_path.glob('**/annual_energy.json'):
        with open(json_file) as f:
            data = json.load(f)

        # Extract key metrics
        energy_data.append({
            'building': json_file.parent.name,
            'total_energy_kwh': data.get('total_site_energy_kwh', 0),
            'heating_kwh': data.get('heating_energy_kwh', 0),
            'cooling_kwh': data.get('cooling_energy_kwh', 0),
            'dhw_kwh': data.get('dhw_energy_kwh', 0),
            'electricity_kwh': data.get('electricity_total_kwh', 0),
            'natural_gas_kwh': data.get('natural_gas_total_kwh', 0)
        })

    # Create DataFrame for analysis
    df = pd.DataFrame(energy_data)

    # Basic statistics
    print("Energy Analysis Summary:")
    print(df.describe())

    # Fuel breakdown
    df['percent_electric'] = (df['electricity_kwh'] / df['total_energy_kwh']) * 100

    return df

# Analyze results
energy_df = analyze_energy_results('simulation_results/')

# Advanced analysis
high_energy_buildings = energy_df[energy_df['total_energy_kwh'] > energy_df['total_energy_kwh'].quantile(0.9)]
print(f"High energy buildings: {len(high_energy_buildings)}")
```

### Integration with NumPy and Matplotlib

```python
import numpy as np
import matplotlib.pyplot as plt
import sqlite3

def analyze_hourly_data(sql_file_path):
    """Analyze hourly simulation data from EnergyPlus SQL output."""

    # Connect to EnergyPlus SQL database
    conn = sqlite3.connect(sql_file_path)

    # Query hourly electricity data
    query = """
    SELECT
        rd.Month, rd.Day, rd.Hour,
        rv.VariableValue as ElectricityRate
    FROM ReportData rd
    JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
    JOIN ReportVariableData rv ON rd.ReportDataIndex = rv.ReportDataIndex
    WHERE rdd.VariableName LIKE '%Electricity%'
    ORDER BY rd.Month, rd.Day, rd.Hour
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convert to numpy arrays for analysis
    hourly_values = df['ElectricityRate'].values

    # Calculate statistics
    peak_demand = np.max(hourly_values)
    average_demand = np.mean(hourly_values)
    load_factor = average_demand / peak_demand

    # Create visualizations
    plt.figure(figsize=(12, 8))

    # Daily profiles
    plt.subplot(2, 2, 1)
    daily_avg = df.groupby('Hour')['ElectricityRate'].mean()
    plt.plot(daily_avg.index, daily_avg.values)
    plt.title('Average Daily Load Profile')
    plt.xlabel('Hour of Day')
    plt.ylabel('Electricity (kW)')

    # Monthly totals
    plt.subplot(2, 2, 2)
    monthly_total = df.groupby('Month')['ElectricityRate'].sum()
    plt.bar(monthly_total.index, monthly_total.values)
    plt.title('Monthly Energy Consumption')
    plt.xlabel('Month')
    plt.ylabel('Total Energy (kWh)')

    # Load duration curve
    plt.subplot(2, 2, 3)
    sorted_loads = np.sort(hourly_values)[::-1]
    plt.plot(range(len(sorted_loads)), sorted_loads)
    plt.title('Load Duration Curve')
    plt.xlabel('Hours')
    plt.ylabel('Load (kW)')

    # Histogram
    plt.subplot(2, 2, 4)
    plt.hist(hourly_values, bins=50, alpha=0.7)
    plt.title('Load Distribution')
    plt.xlabel('Load (kW)')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.show()

    return {
        'peak_demand_kw': peak_demand,
        'average_demand_kw': average_demand,
        'load_factor': load_factor,
        'annual_energy_kwh': np.sum(hourly_values)
    }

# Analyze hourly data
analysis = analyze_hourly_data('results/house/run/eplusout.sql')
print(f"Peak demand: {analysis['peak_demand_kw']:.1f} kW")
print(f"Load factor: {analysis['load_factor']:.2f}")
```

## Advanced Workflows

### Custom Translation Pipeline

```python
from h2k_hpxml.core.translator import h2ktohpxml
from h2k_hpxml.core.model import ModelData
from h2k_hpxml.config.manager import ConfigManager

def custom_translation_workflow(h2k_file, custom_settings):
    """Custom translation with modified settings."""

    # Setup custom configuration
    config = ConfigManager()

    # Override settings
    for section, settings in custom_settings.items():
        for key, value in settings.items():
            config.set(section, key, value)

    # Initialize model data
    model_data = ModelData()

    # Run translation with custom settings
    hpxml_dict = h2ktohpxml(
        h2k_file=h2k_file,
        config=config,
        model_data=model_data,
        mode='SOC'
    )

    # Custom post-processing
    # Modify HPXML dictionary as needed

    return hpxml_dict, model_data

# Example usage
custom_settings = {
    'simulation': {
        'timesteps_per_hour': '6',
        'run_simulation': 'true'
    },
    'weather': {
        'vintage': 'CWEC2020'
    }
}

hpxml_data, model = custom_translation_workflow('input.h2k', custom_settings)
```

### Integration with Other Tools

```python
import subprocess
import json
from pathlib import Path

def energyplus_postprocessing_workflow(hpxml_file):
    """Extended workflow with custom EnergyPlus post-processing."""

    # Convert H2K to HPXML
    hpxml_path = convert_h2k_file(
        input_path=hpxml_file.replace('.h2k', '.h2k'),
        simulate=True,
        hourly_outputs=['ALL']
    )

    # Find the simulation directory
    sim_dir = Path(hpxml_path).parent / 'run'

    # Custom EnergyPlus processing
    if (sim_dir / 'eplusout.sql').exists():
        # Extract custom metrics using SQL queries
        metrics = extract_custom_metrics(sim_dir / 'eplusout.sql')

        # Generate custom reports
        generate_comfort_report(sim_dir)
        generate_cost_analysis(sim_dir, metrics)

        # Create summary JSON
        summary = {
            'building_file': str(hpxml_file),
            'simulation_date': str(datetime.now()),
            'custom_metrics': metrics,
            'files_generated': list(sim_dir.glob('*'))
        }

        with open(sim_dir / 'custom_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)

    return sim_dir

def extract_custom_metrics(sql_file):
    """Extract custom metrics from EnergyPlus SQL output."""

    conn = sqlite3.connect(sql_file)

    # Custom queries for specific metrics
    queries = {
        'unmet_heating_hours': """
            SELECT COUNT(*) FROM ReportData rd
            JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
            WHERE rdd.VariableName LIKE '%Unmet%Heating%' AND rd.VariableValue > 0
        """,
        'peak_cooling_load': """
            SELECT MAX(rd.VariableValue) FROM ReportData rd
            JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
            WHERE rdd.VariableName LIKE '%Cooling Load%'
        """
    }

    metrics = {}
    for name, query in queries.items():
        result = conn.execute(query).fetchone()
        metrics[name] = result[0] if result else 0

    conn.close()
    return metrics
```

## Error Handling

### Robust Error Handling

```python
from h2k_hpxml.api import convert_h2k_file
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def robust_conversion(h2k_files, output_dir):
    """Robust batch conversion with error handling."""

    results = {
        'successful': [],
        'failed': [],
        'errors': []
    }

    for h2k_file in h2k_files:
        try:
            # Attempt conversion
            output = convert_h2k_file(
                input_path=h2k_file,
                output_path=f"{output_dir}/{Path(h2k_file).stem}.xml",
                simulate=True
            )

            results['successful'].append({
                'input': h2k_file,
                'output': output
            })

            logger.info(f"Successfully converted: {h2k_file}")

        except FileNotFoundError as e:
            error_msg = f"File not found: {h2k_file} - {str(e)}"
            results['failed'].append(h2k_file)
            results['errors'].append(error_msg)
            logger.error(error_msg)

        except Exception as e:
            error_msg = f"Conversion failed for {h2k_file}: {str(e)}"
            results['failed'].append(h2k_file)
            results['errors'].append(error_msg)
            logger.error(error_msg)

    # Generate error report
    if results['failed']:
        with open(f"{output_dir}/error_report.txt", 'w') as f:
            f.write("Conversion Error Report\n")
            f.write("=" * 30 + "\n\n")
            for error in results['errors']:
                f.write(f"{error}\n")

    return results

# Usage
h2k_files = glob.glob('input/*.h2k')
results = robust_conversion(h2k_files, 'output/')
print(f"Success rate: {len(results['successful'])} / {len(h2k_files)}")
```

## Performance Optimization

### Memory-Efficient Processing

```python
import gc
from pathlib import Path

def memory_efficient_batch_processing(input_dir, output_dir, batch_size=10):
    """Process large batches with memory management."""

    h2k_files = list(Path(input_dir).glob('*.h2k'))
    total_files = len(h2k_files)

    results = []

    for i in range(0, total_files, batch_size):
        batch = h2k_files[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(total_files-1)//batch_size + 1}")

        batch_results = []

        for h2k_file in batch:
            try:
                # Process single file
                output = convert_h2k_file(
                    input_path=str(h2k_file),
                    output_path=f"{output_dir}/{h2k_file.stem}.xml",
                    simulate=False  # Skip simulation for memory efficiency
                )
                batch_results.append(output)

            except Exception as e:
                print(f"Failed: {h2k_file} - {e}")

        results.extend(batch_results)

        # Force garbage collection between batches
        gc.collect()

        print(f"Batch completed. Total processed: {len(results)}")

    return results

# Process large dataset efficiently
results = memory_efficient_batch_processing('large_dataset/', 'results/', batch_size=5)
```

### Parallel Processing with Progress Tracking

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

def parallel_processing_with_progress(h2k_files, output_dir, max_workers=4):
    """Parallel processing with progress bar."""

    def process_single_file(h2k_file):
        """Process a single file."""
        try:
            output = convert_h2k_file(
                input_path=h2k_file,
                output_path=f"{output_dir}/{Path(h2k_file).stem}.xml",
                simulate=True
            )
            return {'status': 'success', 'input': h2k_file, 'output': output}
        except Exception as e:
            return {'status': 'failed', 'input': h2k_file, 'error': str(e)}

    results = []

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        futures = {executor.submit(process_single_file, h2k_file): h2k_file
                  for h2k_file in h2k_files}

        # Process completed jobs with progress bar
        with tqdm(total=len(h2k_files), desc="Converting H2K files") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                # Update progress bar
                status = "✅" if result['status'] == 'success' else "❌"
                pbar.set_postfix_str(f"Last: {status} {Path(result['input']).name}")
                pbar.update(1)

    # Summary
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    print(f"\nProcessing complete:")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

    return results

# Usage
h2k_files = glob.glob('input/*.h2k')
results = parallel_processing_with_progress(h2k_files, 'output/', max_workers=4)
```

## Examples and Use Cases

### Research Workflow Example

```python
#!/usr/bin/env python3
"""
Research workflow for Canadian housing archetypes analysis.
Processes H2K files, runs simulations, and generates analysis reports.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

from h2k_hpxml.api import batch_convert_h2k_files, validate_dependencies

def canadian_archetypes_analysis():
    """Complete analysis workflow for Canadian housing archetypes."""

    # 1. Setup and validation
    print("🔍 Validating dependencies...")
    deps = validate_dependencies()
    if not deps['valid']:
        raise RuntimeError("Dependencies not configured. Run h2k-deps --setup")

    # 2. Process archetypes
    print("🏠 Processing housing archetypes...")
    archetype_files = list(Path('archetypes/').glob('**/*.h2k'))

    results = batch_convert_h2k_files(
        input_files=[str(f) for f in archetype_files],
        output_directory='analysis_results/',
        simulate=True,
        max_workers=6
    )

    print(f"✅ Processed {len(results['successful'])} archetypes")

    # 3. Data extraction and analysis
    print("📊 Extracting energy data...")
    energy_data = extract_energy_metrics('analysis_results/')

    # 4. Generate research outputs
    print("📈 Generating analysis reports...")
    generate_research_reports(energy_data)

    return energy_data

def extract_energy_metrics(results_dir):
    """Extract comprehensive energy metrics from simulation results."""

    results_path = Path(results_dir)
    metrics = []

    for building_dir in results_path.iterdir():
        if not building_dir.is_dir():
            continue

        # Extract from annual energy JSON
        annual_file = building_dir / 'annual_energy.json'
        if annual_file.exists():
            with open(annual_file) as f:
                annual_data = json.load(f)

            # Extract from EnergyPlus SQL (hourly data)
            sql_file = building_dir / 'run' / 'eplusout.sql'
            hourly_data = {}
            if sql_file.exists():
                hourly_data = extract_hourly_metrics(sql_file)

            # Combine metrics
            building_metrics = {
                'building_name': building_dir.name,
                'archetype_type': extract_archetype_type(building_dir.name),
                'climate_zone': extract_climate_zone(building_dir.name),

                # Annual metrics
                'total_energy_kwh': annual_data.get('total_site_energy_kwh', 0),
                'heating_energy_kwh': annual_data.get('heating_energy_kwh', 0),
                'cooling_energy_kwh': annual_data.get('cooling_energy_kwh', 0),
                'dhw_energy_kwh': annual_data.get('dhw_energy_kwh', 0),
                'electricity_kwh': annual_data.get('electricity_total_kwh', 0),
                'natural_gas_kwh': annual_data.get('natural_gas_total_kwh', 0),

                # Derived metrics
                'energy_intensity_kwh_m2': annual_data.get('total_site_energy_kwh', 0) /
                                          annual_data.get('conditioned_floor_area_m2', 1),
                'electrification_ratio': annual_data.get('electricity_total_kwh', 0) /
                                       max(annual_data.get('total_site_energy_kwh', 1), 1),

                # Hourly-based metrics
                **hourly_data
            }

            metrics.append(building_metrics)

    return pd.DataFrame(metrics)

def extract_hourly_metrics(sql_file):
    """Extract key metrics from hourly EnergyPlus data."""

    import sqlite3

    conn = sqlite3.connect(sql_file)

    # Peak demand
    peak_query = """
    SELECT MAX(rd.VariableValue) FROM ReportData rd
    JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
    WHERE rdd.VariableName LIKE '%Electricity:Facility%'
    """

    peak_demand = conn.execute(peak_query).fetchone()[0] or 0

    # Load factor calculation
    avg_query = """
    SELECT AVG(rd.VariableValue) FROM ReportData rd
    JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex
    WHERE rdd.VariableName LIKE '%Electricity:Facility%'
    """

    avg_demand = conn.execute(avg_query).fetchone()[0] or 0
    load_factor = avg_demand / peak_demand if peak_demand > 0 else 0

    conn.close()

    return {
        'peak_demand_kw': peak_demand,
        'average_demand_kw': avg_demand,
        'load_factor': load_factor
    }

def generate_research_reports(energy_data):
    """Generate comprehensive research reports and visualizations."""

    # 1. Summary statistics
    summary_stats = energy_data.describe()
    summary_stats.to_csv('analysis_results/summary_statistics.csv')

    # 2. Energy intensity by archetype type
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 3, 1)
    energy_by_type = energy_data.groupby('archetype_type')['energy_intensity_kwh_m2'].mean()
    energy_by_type.plot(kind='bar')
    plt.title('Energy Intensity by Archetype Type')
    plt.ylabel('kWh/m²/year')
    plt.xticks(rotation=45)

    # 3. Electrification analysis
    plt.subplot(2, 3, 2)
    plt.scatter(energy_data['total_energy_kwh'], energy_data['electrification_ratio'], alpha=0.6)
    plt.xlabel('Total Energy (kWh/year)')
    plt.ylabel('Electrification Ratio')
    plt.title('Electrification vs Total Energy')

    # 4. Climate zone comparison
    plt.subplot(2, 3, 3)
    climate_energy = energy_data.groupby('climate_zone')['energy_intensity_kwh_m2'].mean()
    climate_energy.plot(kind='bar')
    plt.title('Energy Intensity by Climate Zone')
    plt.ylabel('kWh/m²/year')

    # 5. Load factor distribution
    plt.subplot(2, 3, 4)
    plt.hist(energy_data['load_factor'], bins=30, alpha=0.7)
    plt.xlabel('Load Factor')
    plt.ylabel('Frequency')
    plt.title('Load Factor Distribution')

    # 6. Heating vs Cooling energy
    plt.subplot(2, 3, 5)
    plt.scatter(energy_data['heating_energy_kwh'], energy_data['cooling_energy_kwh'], alpha=0.6)
    plt.xlabel('Heating Energy (kWh/year)')
    plt.ylabel('Cooling Energy (kWh/year)')
    plt.title('Heating vs Cooling Energy')

    # 7. Peak demand analysis
    plt.subplot(2, 3, 6)
    plt.scatter(energy_data['total_energy_kwh'], energy_data['peak_demand_kw'], alpha=0.6)
    plt.xlabel('Total Energy (kWh/year)')
    plt.ylabel('Peak Demand (kW)')
    plt.title('Peak Demand vs Total Energy')

    plt.tight_layout()
    plt.savefig('analysis_results/research_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # 8. Generate detailed CSV reports
    energy_data.to_csv('analysis_results/detailed_results.csv', index=False)

    # 9. Create summary report
    with open('analysis_results/analysis_summary.txt', 'w') as f:
        f.write("Canadian Housing Archetypes Energy Analysis\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total buildings analyzed: {len(energy_data)}\n")
        f.write(f"Average energy intensity: {energy_data['energy_intensity_kwh_m2'].mean():.1f} kWh/m²/year\n")
        f.write(f"Average electrification ratio: {energy_data['electrification_ratio'].mean():.2f}\n")
        f.write(f"Average load factor: {energy_data['load_factor'].mean():.2f}\n\n")

        f.write("Energy Intensity by Archetype Type:\n")
        for archetype, intensity in energy_data.groupby('archetype_type')['energy_intensity_kwh_m2'].mean().items():
            f.write(f"  {archetype}: {intensity:.1f} kWh/m²/year\n")

def extract_archetype_type(building_name):
    """Extract archetype type from building name."""
    if 'detached' in building_name.lower():
        return 'Single Detached'
    elif 'townhouse' in building_name.lower():
        return 'Townhouse'
    elif 'apartment' in building_name.lower():
        return 'Apartment'
    else:
        return 'Other'

def extract_climate_zone(building_name):
    """Extract climate zone from building name."""
    # Simplified extraction - customize based on your naming convention
    if 'zone1' in building_name.lower() or 'vancouver' in building_name.lower():
        return 'Zone 1'
    elif 'zone2' in building_name.lower() or 'toronto' in building_name.lower():
        return 'Zone 2'
    elif 'zone3' in building_name.lower() or 'winnipeg' in building_name.lower():
        return 'Zone 3'
    else:
        return 'Unknown'

if __name__ == "__main__":
    # Run complete analysis
    data = canadian_archetypes_analysis()
    print("✅ Analysis complete! Check analysis_results/ directory for outputs.")
```

### Integration with Jupyter Notebooks

```python
# Jupyter notebook example for interactive analysis
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from h2k_hpxml.api import convert_h2k_file
import ipywidgets as widgets
from IPython.display import display

# Interactive conversion widget
def create_conversion_widget():
    """Create interactive widget for H2K conversion."""

    file_input = widgets.Text(
        value='',
        placeholder='Enter H2K file path',
        description='H2K File:',
        style={'description_width': 'initial'}
    )

    simulate_checkbox = widgets.Checkbox(
        value=True,
        description='Run EnergyPlus simulation'
    )

    mode_dropdown = widgets.Dropdown(
        options=['SOC', 'ASHRAE140'],
        value='SOC',
        description='Translation mode:'
    )

    convert_button = widgets.Button(
        description='Convert',
        button_style='success'
    )

    output_area = widgets.Output()

    def on_convert_clicked(b):
        with output_area:
            output_area.clear_output()
            try:
                print(f"Converting {file_input.value}...")
                result = convert_h2k_file(
                    input_path=file_input.value,
                    simulate=simulate_checkbox.value,
                    mode=mode_dropdown.value
                )
                print(f"✅ Conversion complete: {result}")
            except Exception as e:
                print(f"❌ Conversion failed: {e}")

    convert_button.on_click(on_convert_clicked)

    return widgets.VBox([
        file_input,
        simulate_checkbox,
        mode_dropdown,
        convert_button,
        output_area
    ])

# Display widget in notebook
conversion_widget = create_conversion_widget()
display(conversion_widget)
```

This comprehensive library guide provides energy modellers and data scientists with everything they need to integrate H2K-HPXML into their research workflows, from basic conversions to advanced parallel processing and data analysis pipelines.