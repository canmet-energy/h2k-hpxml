#!/usr/bin/env python3
"""
Resilience CLI Tool

A command-line interface tool that analyzes building resiliency scenarios by examining 
clothing factors and HVAC performance during power outages and extreme weather conditions.
"""

import pathlib
import os
import sys
import traceback
import yaml
from datetime import datetime, timedelta
import tempfile
import shutil
import subprocess
import configparser

# Avoid having to add PYTHONPATH to env.
PROJECT_ROOT = str(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)

import click
from h2ktohpxml.h2ktohpxml import h2ktohpxml
from h2ktohpxml.utils import weather as weather_utils
import pandas as pd
import numpy as np

# Check for OpenStudio Python bindings
try:
    import openstudio
    OPENSTUDIO_AVAILABLE = True
except ImportError:
    OPENSTUDIO_AVAILABLE = False

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('h2k_path', type=click.Path(exists=True, dir_okay=False))
@click.option('--outage-days', default=7, type=click.IntRange(0, 365), 
              help='Number of days for power outage analysis (default: 7, range: 0-365)')
@click.option('--output-path', type=click.Path(), 
              help='Output folder path (default: same directory as H2K input file)')
@click.option('--clothing-factor-summer', default=0.5, type=click.FloatRange(0.0, 2.0),
              help='Summer clothing insulation factor (default: 0.5, range: 0.0-2.0)')
@click.option('--clothing-factor-winter', default=1.0, type=click.FloatRange(0.0, 2.0),
              help='Winter clothing insulation factor (default: 1.0, range: 0.0-2.0)')
@click.option('--run-simulation', is_flag=True, default=False,
              help='Run the OpenStudio simulations for all scenarios (default: False)')
@click.version_option(version='1.0.0')
def resilience(h2k_path, outage_days, output_path, clothing_factor_summer, clothing_factor_winter, run_simulation):
    """
    Analyze building resiliency scenarios using H2K file input.
    
    This tool converts H2K files to OpenStudio models and creates four scenarios:
    - outage_typical_year: Power outage during typical weather (CWEC)
    - outage_extreme_year: Power outage during extreme weather (EWY)  
    - thermal_autonomy_typical_year: No cooling/heating during typical weather
    - thermal_autonomy_extreme_year: No cooling/heating during extreme weather
    """
    try:
        # Check for OpenStudio availability
        if not OPENSTUDIO_AVAILABLE:
            click.echo("Error: OpenStudio Python bindings are not available.", err=True)
            click.echo("Please ensure OpenStudio is properly installed with Python bindings.", err=True)
            sys.exit(1)
        
        # Validate inputs
        h2k_path = os.path.abspath(h2k_path)
        if not os.path.exists(h2k_path):
            click.echo(f"Error: H2K file not found: {h2k_path}", err=True)
            sys.exit(1)
        
        # Set output path
        if output_path is None:
            output_path = os.path.dirname(h2k_path)
        output_path = os.path.abspath(output_path)
        
        click.echo(f"Processing H2K file: {h2k_path}")
        click.echo(f"Output directory: {output_path}")
        click.echo(f"Outage duration: {outage_days} days")
        click.echo(f"Clothing factors - Summer: {clothing_factor_summer}, Winter: {clothing_factor_winter}")
        click.echo(f"Run simulations: {run_simulation}")
        
        # Initialize processor
        processor = ResilienceProcessor(
            h2k_path=h2k_path,
            output_path=output_path,
            outage_days=outage_days,
            clothing_factor_summer=clothing_factor_summer,
            clothing_factor_winter=clothing_factor_winter,
            run_simulation=run_simulation
        )
        
        # Run the complete workflow
        processor.run()
        
        click.echo("Resilience analysis completed successfully!")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo(f"Traceback: {traceback.format_exc()}", err=True)
        sys.exit(1)


class ResilienceProcessor:
    """Main processor class for resilience analysis."""
    
    def __init__(self, h2k_path, output_path, outage_days, clothing_factor_summer, clothing_factor_winter, run_simulation=False):
        self.h2k_path = h2k_path
        self.output_path = output_path
        self.outage_days = outage_days
        self.clothing_factor_summer = clothing_factor_summer
        self.clothing_factor_winter = clothing_factor_winter
        self.run_simulation = run_simulation
        
        # Create output directory structure
        os.makedirs(output_path, exist_ok=True)
        self.baseline_path = os.path.join(output_path, "baseline")
        os.makedirs(self.baseline_path, exist_ok=True)
        
        # Scenario paths
        self.scenario_paths = {
            'outage_typical_year': os.path.join(output_path, 'outage_typical_year'),
            'outage_extreme_year': os.path.join(output_path, 'outage_extreme_year'),
            'thermal_autonomy_typical_year': os.path.join(output_path, 'thermal_autonomy_typical_year'),
            'thermal_autonomy_extreme_year': os.path.join(output_path, 'thermal_autonomy_extreme_year')
        }
        
        for path in self.scenario_paths.values():
            os.makedirs(path, exist_ok=True)
    
    def run(self):
        """Execute the complete resilience analysis workflow."""
        click.echo("Step 1: Converting H2K to HPXML/OSM...")
        self.convert_h2k_to_osm()
        
        click.echo("Step 2: Processing weather files...")
        self.process_weather_files()
        
        click.echo("Step 3: Determining seasons...")
        self.determine_seasons()
        
        click.echo("Step 4: Generating scenarios...")
        self.generate_scenarios()
        
        if self.run_simulation:
            click.echo("Step 5: Running simulations...")
            self.run_simulations()
        
        click.echo("Resilience analysis workflow completed!")
    
    def add_output_variables(self, model):
        """Add required output variables to the model with hourly reporting frequency."""
        try:
            # Define the required output variables
            output_variables = [
                'Site Outdoor Air Relative Humidity',
                'Zone Air Temperature', 
                'Zone Air Relative Humidity',
                'Zone Mean Radiant Temperature',
                'Zone Operative Temperature',
                'Zone People Occupant Count'
            ]
            
            # Add each output variable with hourly frequency
            for var_name in output_variables:
                output_var = openstudio.model.OutputVariable(var_name, model)
                output_var.setReportingFrequency("Hourly")
                
                # For zone-specific variables, apply to all zones
                if var_name.startswith('Zone'):
                    output_var.setKeyValue("*")  # Apply to all zones
                    
        except Exception as e:
            raise Exception(f"Failed to add output variables: {str(e)}")
    
    def convert_h2k_to_osm(self):
        """Convert H2K file to OSM format using h2ktohpxml converter."""
        try:
            # Read H2K file with proper encoding detection
            encoding = self.detect_xml_encoding(self.h2k_path)
            with open(self.h2k_path, "r", encoding=encoding) as f:
                h2k_string = f.read()
            
            # Convert to HPXML
            click.echo("Converting H2K to HPXML...")
            hpxml_string = h2ktohpxml(h2k_string)
            
            # Save HPXML file
            hpxml_path = os.path.join(self.baseline_path, "baseline.xml")
            with open(hpxml_path, "w", encoding="utf-8") as f:
                f.write(hpxml_string)
            
            # Convert HPXML to OSM using OpenStudio
            click.echo("Converting HPXML to OSM...")
            self.convert_hpxml_to_osm(hpxml_path)
            
        except Exception as e:
            raise Exception(f"Failed to convert H2K to OSM: {str(e)}")
    
    def detect_xml_encoding(self, filepath):
        """Detect encoding from XML declaration."""
        import re
        with open(filepath, "rb") as f:
            first_line = f.readline()
            match = re.search(br'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
            if match:
                return match.group(1).decode("ascii")
        return "utf-8"  # fallback
    
    def convert_hpxml_to_osm(self, hpxml_path):
        """Convert HPXML to OSM using OpenStudio-HPXML workflow."""
        try:
            # Use the OpenStudio-HPXML workflow to convert HPXML to OSM
            import configparser
            import time
            
            # Read the conversion config to get paths
            config_path = os.path.join(PROJECT_ROOT, 'conversionconfig.ini')
            config = configparser.ConfigParser()
            config.read(config_path)
            
            hpxml_os_path = config.get("paths", "hpxml_os_path")
            ruby_hpxml_path = os.path.join(hpxml_os_path, 'workflow', 'run_simulation.rb')
            
            # Check if OpenStudio-HPXML is available
            if not os.path.exists(hpxml_os_path):
                click.echo(f"Warning: OpenStudio-HPXML not found at {hpxml_os_path}")
                click.echo("Falling back to simple model creation...")
                return self._create_simple_model()
            
            if not os.path.exists(ruby_hpxml_path):
                click.echo(f"Warning: HPXML workflow not found at {ruby_hpxml_path}")
                click.echo("Falling back to simple model creation...")
                return self._create_simple_model()
            
            # Run the HPXML to OSM conversion
            output_dir = os.path.join(self.baseline_path, "hpxml_run")
            os.makedirs(output_dir, exist_ok=True)
            
            command = [
                "/usr/local/bin/openstudio",
                ruby_hpxml_path,
                "-x", hpxml_path,
                "-o", output_dir,
                "--skip-simulation",  # We only want the OSM, not the full simulation
                "-d"  # Debug mode to get more files
            ]
            
            click.echo("Converting HPXML to OSM using OpenStudio-HPXML workflow...")
            result = subprocess.run(
                command,
                cwd=hpxml_os_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                click.echo(f"Warning: HPXML conversion failed: {result.stderr}")
                click.echo("Falling back to simple model creation...")
                return self._create_simple_model()
            
            # Look for the generated OSM file
            # The OpenStudio-HPXML workflow creates files in the specified output directory
            potential_osm_files = [
                os.path.join(output_dir, "run", "in.osm"),  # Most likely location
                os.path.join(output_dir, "in.osm"),
                os.path.join(output_dir, "run.osm"),
                os.path.join(output_dir, "resources", "in.osm")
            ]
            
            source_osm_path = None
            for osm_file in potential_osm_files:
                if os.path.exists(osm_file):
                    source_osm_path = osm_file
                    break
            
            if source_osm_path is None:
                click.echo("Warning: Could not find generated OSM file")
                click.echo("Falling back to simple model creation...")
                return self._create_simple_model()
            
            # Copy the generated OSM to our baseline directory
            osm_path = os.path.join(self.baseline_path, "baseline.osm")
            shutil.copy2(source_osm_path, osm_path)
            
            # Load the model to get the OpenStudio model object
            optional_model = openstudio.model.Model.load(osm_path)
            if not optional_model.is_initialized():
                click.echo("Warning: Could not load generated OSM file")
                click.echo("Falling back to simple model creation...")
                return self._create_simple_model()
            
            model = optional_model.get()
            
            # Add our required output variables
            self.add_output_variables(model)
            
            # Save the updated model
            model.save(osm_path, True)
            self.baseline_model = model
            self.baseline_osm_path = osm_path
            
            click.echo(f"Baseline OSM created from HPXML: {osm_path}")
            
        except subprocess.TimeoutExpired:
            click.echo("Warning: HPXML conversion timed out")
            click.echo("Falling back to simple model creation...")
            return self._create_simple_model()
        except Exception as e:
            click.echo(f"Warning: HPXML conversion failed: {str(e)}")
            click.echo("Falling back to simple model creation...")
            return self._create_simple_model()
    
    def _create_simple_model(self):
        """Create a simple baseline model as fallback."""
        # Create a basic OpenStudio model
        model = openstudio.model.Model()
        
        # Add output variables to baseline model
        self.add_output_variables(model)
        
        # Save the model as baseline OSM
        osm_path = os.path.join(self.baseline_path, "baseline.osm")
        model.save(osm_path, True)
        self.baseline_model = model
        self.baseline_osm_path = osm_path
        
        click.echo(f"Simple baseline OSM created: {osm_path}")
        click.echo("Note: This is a simplified model. For full building geometry and systems, ensure OpenStudio-HPXML is properly installed.")
    
    def process_weather_files(self):
        """Process weather files to find extreme periods."""
        try:
            # Get weather information from the model
            weather_info = self.get_weather_info_from_model()
            
            # Get weather file paths
            cwec_file, ewy_file = self.get_weather_file_paths(weather_info)
            
            # Store weather file paths for simulation use
            self.cwec_epw_path = cwec_file
            self.ewy_epw_path = ewy_file
            
            # Process both weather files
            cwec_extreme = self.find_extreme_period(cwec_file, self.outage_days)
            ewy_extreme = self.find_extreme_period(ewy_file, self.outage_days)
            
            # Save extreme periods
            extreme_periods = {
                'cwec_outage_start_date': cwec_extreme.strftime('%Y-%m-%d'),
                'ewy_outage_start_date': ewy_extreme.strftime('%Y-%m-%d')
            }
            
            extreme_periods_path = os.path.join(self.output_path, 'extreme_periods.yml')
            with open(extreme_periods_path, 'w') as f:
                yaml.dump(extreme_periods, f)
            
            self.extreme_periods = extreme_periods
            click.echo(f"Extreme periods saved: {extreme_periods_path}")
            
        except Exception as e:
            raise Exception(f"Failed to process weather files: {str(e)}")
    
    def get_weather_info_from_model(self):
        """Extract weather information from the OpenStudio model."""
        # Since we're using a simplified model, fallback to extracting from H2K file
        return self.extract_weather_from_h2k()
    
    def extract_weather_from_h2k(self):
        """Extract weather information directly from H2K file."""
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(self.h2k_path)
        root = tree.getroot()
        
        # Find weather region and location info
        region_elem = root.find('.//Region/English')
        location_elem = root.find('.//Location/English')
        
        if region_elem is not None and location_elem is not None:
            region = region_elem.text.strip() if region_elem.text else ""
            location = location_elem.text.strip() if location_elem.text else ""
            
            # Map H2K location names to CSV names
            if "OTTAWA" in location.upper():
                location = "OTTAWA INTL"
            
            return {'city': location.upper(), 'state': region.upper()}
        
        raise Exception("Could not extract weather information from H2K file")
    
    def get_weather_file_paths(self, weather_info):
        """Get CWEC and EWY weather file paths."""
        import csv
        
        # Read weather database
        weather_csv_path = os.path.join(
            PROJECT_ROOT, 'h2ktohpxml', 'resources', 'weather', 'h2k_weather_names.csv'
        )
        
        with open(weather_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['cities_english'].upper() == weather_info['city'].upper() and 
                    row['provinces_english'].upper() == weather_info['state'].upper()):
                    
                    cwec_filename = row['CWEC2020.zip']
                    ewy_filename = row['EWY2020.zip']
                    
                    # Download weather files if needed
                    cwec_path = self.download_weather_file(cwec_filename)
                    ewy_path = self.download_weather_file(ewy_filename)
                    
                    return cwec_path, ewy_path
        
        raise Exception(f"Could not find weather files for {weather_info['city']}, {weather_info['state']}")
    
    def download_weather_file(self, filename):
        """Download and extract weather file if it doesn't exist."""
        import zipfile
        
        weather_folder = os.path.join(PROJECT_ROOT, 'h2ktohpxml', 'utils')
        epw_filename = filename.replace('.zip', '.epw')
        epw_path = os.path.join(weather_folder, epw_filename)
        
        if os.path.exists(epw_path):
            return epw_path
        
        # Check if zip file exists and extract it
        zip_path = os.path.join(weather_folder, filename)
        if os.path.exists(zip_path):
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract EPW file
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('.epw'):
                            zip_ref.extract(file_info, weather_folder)
                            # Rename to expected filename
                            extracted_path = os.path.join(weather_folder, file_info.filename)
                            if extracted_path != epw_path:
                                os.rename(extracted_path, epw_path)
                            return epw_path
                raise Exception(f"No EPW file found in {zip_path}")
            except Exception as e:
                raise Exception(f"Failed to extract weather file {zip_path}: {str(e)}")
        
        # If EWY file, use CWEC for now
        if 'EWY2020' in filename:
            cwec_filename = filename.replace('EWY2020', 'CWEC2020')
            return self.download_weather_file(cwec_filename)
        
        # Weather file not found
        raise Exception(f"Weather file not found: {epw_path}")
    
    def find_extreme_period(self, weather_file_path, days):
        """Find the hottest consecutive period in the weather file."""
        try:
            # Read EPW file and extract temperature data
            temperatures = []
            dates = []
            
            with open(weather_file_path, 'r') as f:
                lines = f.readlines()
                
                # Skip header lines (first 8 lines in EPW format)
                for line in lines[8:]:
                    parts = line.strip().split(',')
                    if len(parts) > 6:
                        try:
                            month = int(parts[1])
                            day = int(parts[2])
                            hour = int(parts[3])
                            temp = float(parts[6])  # Dry bulb temperature
                            
                            # Only use hour 12 (noon) for daily analysis
                            if hour == 12:
                                date = datetime(2023, month, day)  # Use a non-leap year
                                dates.append(date)
                                temperatures.append(temp)
                        except (ValueError, IndexError):
                            continue
            
            # Find hottest consecutive period
            max_avg_temp = -999
            best_start_date = None
            
            for i in range(len(temperatures) - days + 1):
                period_temps = temperatures[i:i+days]
                avg_temp = sum(period_temps) / len(period_temps)
                
                if avg_temp > max_avg_temp:
                    max_avg_temp = avg_temp
                    best_start_date = dates[i]
            
            if best_start_date is None:
                raise Exception("Could not find extreme period in weather file")
            
            return best_start_date
            
        except Exception as e:
            raise Exception(f"Failed to analyze weather file {weather_file_path}: {str(e)}")
    
    def determine_seasons(self):
        """Analyze weather files to determine summer/winter periods."""
        try:
            # Get weather information and both weather files
            weather_info = self.get_weather_info_from_model()
            cwec_file, ewy_file = self.get_weather_file_paths(weather_info)
            
            # Analyze both weather files separately
            cwec_summer = self.analyze_summer_period(cwec_file, "CWEC")
            ewy_summer = self.analyze_summer_period(ewy_file, "EWY")
            
            summer_periods = {
                'cwec_summer_start': cwec_summer['start'].strftime('%m-%d'),
                'cwec_summer_end': cwec_summer['end'].strftime('%m-%d'),
                'ewy_summer_start': ewy_summer['start'].strftime('%m-%d'),
                'ewy_summer_end': ewy_summer['end'].strftime('%m-%d')
            }
            
            summer_periods_path = os.path.join(self.output_path, 'summer_period.yml')
            with open(summer_periods_path, 'w') as f:
                yaml.dump(summer_periods, f)
            
            self.summer_periods = summer_periods
            click.echo(f"Summer periods saved: {summer_periods_path}")
            click.echo(f"CWEC Summer: {summer_periods['cwec_summer_start']} to {summer_periods['cwec_summer_end']}")
            click.echo(f"EWY Summer: {summer_periods['ewy_summer_start']} to {summer_periods['ewy_summer_end']}")
            
        except Exception as e:
            raise Exception(f"Failed to determine seasons: {str(e)}")
    
    def analyze_summer_period(self, weather_file_path, weather_type):
        """Analyze a single weather file to determine summer period."""
        try:
            # Read daily temperatures
            daily_temps = []
            dates = []
            
            with open(weather_file_path, 'r') as f:
                lines = f.readlines()
                
                current_temps = []
                current_date = None
                
                for line in lines[8:]:
                    parts = line.strip().split(',')
                    if len(parts) > 6:
                        try:
                            month = int(parts[1])
                            day = int(parts[2])
                            hour = int(parts[3])
                            temp = float(parts[6])
                            
                            date = datetime(2023, month, day)
                            
                            if current_date != date:
                                # Process previous day
                                if current_temps:
                                    daily_avg = sum(current_temps) / len(current_temps)
                                    daily_temps.append(daily_avg)
                                    dates.append(current_date)
                                
                                # Start new day
                                current_date = date
                                current_temps = [temp]
                            else:
                                current_temps.append(temp)
                        except (ValueError, IndexError):
                            continue
            
            # Find summer period (average daily temp > 15°C)
            # Use a more robust approach: find the longest consecutive period above 15°C
            # or use months-based approach for more realistic seasons
            
            # Method 1: Find typical summer months (June-August) and extend based on temperature
            summer_candidates = []
            current_start = None
            current_count = 0
            
            for i, temp in enumerate(daily_temps):
                if temp > 15.0:
                    if current_start is None:
                        current_start = i
                    current_count += 1
                else:
                    if current_start is not None and current_count >= 7:  # At least 7 consecutive days
                        summer_candidates.append((current_start, current_start + current_count - 1, current_count))
                    current_start = None
                    current_count = 0
            
            # Add final period if it was ongoing
            if current_start is not None and current_count >= 7:
                summer_candidates.append((current_start, current_start + current_count - 1, current_count))
            
            # Find the longest summer period
            if summer_candidates:
                # Sort by length and take the longest period
                summer_candidates.sort(key=lambda x: x[2], reverse=True)
                start_idx, end_idx, days_count = summer_candidates[0]
                summer_start = dates[start_idx]
                summer_end = dates[end_idx]
                click.echo(f"{weather_type}: Found {len(summer_candidates)} summer periods, longest: {days_count} days ({summer_start.strftime('%m-%d')} to {summer_end.strftime('%m-%d')})")
            else:
                # Fallback: use meteorological summer (June-August) based on calendar
                summer_start = None
                summer_end = None
                
                # Find June 1st and August 31st equivalent
                for i, date in enumerate(dates):
                    if summer_start is None and date.month >= 6:
                        summer_start = date
                    if date.month <= 8:
                        summer_end = date
                
                # If still not found, use defaults
                if summer_start is None:
                    summer_start = datetime(2023, 6, 1)
                if summer_end is None:
                    summer_end = datetime(2023, 8, 31)
                
                click.echo(f"{weather_type}: Used fallback meteorological summer")
            
            return {'start': summer_start, 'end': summer_end}
            
        except Exception as e:
            raise Exception(f"Failed to analyze {weather_type} summer period: {str(e)}")
    
    def generate_scenarios(self):
        """Generate all four resilience scenarios."""
        scenarios = [
            {
                'name': 'outage_typical_year',
                'weather_file': 'CWEC',
                'clothing_schedule': True,
                'mechanical_cooling_available': True,
                'power_failure_schedule': True
            },
            {
                'name': 'outage_extreme_year', 
                'weather_file': 'EWY',
                'clothing_schedule': True,
                'mechanical_cooling_available': True,
                'power_failure_schedule': True
            },
            {
                'name': 'thermal_autonomy_typical_year',
                'weather_file': 'CWEC',
                'clothing_schedule': True,
                'mechanical_cooling_available': False,
                'power_failure_schedule': False
            },
            {
                'name': 'thermal_autonomy_extreme_year',
                'weather_file': 'EWY',
                'clothing_schedule': True,
                'mechanical_cooling_available': False,
                'power_failure_schedule': False
            }
        ]
        
        for scenario in scenarios:
            click.echo(f"Generating scenario: {scenario['name']}")
            self.generate_single_scenario(scenario)
    
    def generate_single_scenario(self, scenario):
        """Generate a single scenario OSM file."""
        try:
            # Create a copy of the baseline model
            model = openstudio.model.Model(self.baseline_model)
            
            # Apply weather file
            self.apply_weather_file(model, scenario['weather_file'])
            
            # Apply clothing schedule
            if scenario['clothing_schedule']:
                self.apply_clothing_schedule(model, scenario['weather_file'])
            
            # Apply mechanical cooling settings
            if not scenario['mechanical_cooling_available']:
                self.disable_cooling_systems(model)
            
            # Apply power failure schedule
            if scenario['power_failure_schedule']:
                self.apply_power_failure_schedule(model, scenario['weather_file'])
            
            # Add output variables
            self.add_output_variables(model)
            
            # Save the modified model
            scenario_path = self.scenario_paths[scenario['name']]
            osm_path = os.path.join(scenario_path, f"{scenario['name']}.osm")
            model.save(osm_path, True)
            
            click.echo(f"Scenario saved: {osm_path}")
            
        except Exception as e:
            raise Exception(f"Failed to generate scenario {scenario['name']}: {str(e)}")
    
    def apply_weather_file(self, model, weather_type):
        """Apply the specified weather file to the model."""
        # For now, this is a placeholder since both CWEC and EWY use same files
        # In the future, this will switch between different weather files
        pass
    
    def apply_clothing_schedule(self, model, weather_type):
        """Apply seasonal clothing schedule to all people definitions."""
        try:
            # Create new seasonal clothing schedule
            clothing_schedule = openstudio.model.ScheduleRuleset(model)
            clothing_schedule.setName("Seasonal Clothing Schedule")
            
            # Set winter default value
            default_day = clothing_schedule.defaultDaySchedule()
            default_day.addValue(openstudio.Time(1, 0), self.clothing_factor_winter)
            
            # Add summer rule using the appropriate weather type
            summer_rule = openstudio.model.ScheduleRule(clothing_schedule)
            summer_rule.setName("Summer Clothing Rule")
            
            # Set summer dates from summer_period.yml based on weather type
            if weather_type == 'CWEC':
                summer_start = self.summer_periods['cwec_summer_start']
                summer_end = self.summer_periods['cwec_summer_end']
            else:  # EWY
                summer_start = self.summer_periods['ewy_summer_start']
                summer_end = self.summer_periods['ewy_summer_end']
            
            start_month, start_day = map(int, summer_start.split('-'))
            end_month, end_day = map(int, summer_end.split('-'))
            
            summer_rule.setStartDate(openstudio.Date(openstudio.MonthOfYear(start_month), start_day))
            summer_rule.setEndDate(openstudio.Date(openstudio.MonthOfYear(end_month), end_day))
            
            # Set summer clothing value
            summer_day = summer_rule.daySchedule()
            summer_day.addValue(openstudio.Time(1, 0), self.clothing_factor_summer)
            
            # Apply clothing schedule to all people definitions
            for people_def in model.getPeopleDefinitions():
                try:
                    people_def.setClothingInsulationSchedule(clothing_schedule)
                except Exception:
                    # If setting clothing schedule fails, continue with other people definitions
                    pass
                
        except Exception as e:
            raise Exception(f"Failed to apply clothing schedule: {str(e)}")
    
    def disable_cooling_systems(self, model):
        """Disable all cooling equipment and remove cooling setpoints."""
        try:
            # Disable cooling equipment
            for cooling_coil in model.getCoilCoolingDXSingleSpeeds():
                cooling_coil.remove()
            
            for cooling_coil in model.getCoilCoolingDXTwoSpeeds():
                cooling_coil.remove()
                
            for cooling_coil in model.getCoilCoolingDXVariableSpeeds():
                cooling_coil.remove()
            
            # Remove cooling setpoints from thermostats
            for thermostat in model.getThermostatSetpointDualSetpoints():
                if thermostat.coolingSetpointTemperatureSchedule().is_initialized():
                    thermostat.resetCoolingSetpointTemperatureSchedule()
                    
        except Exception as e:
            raise Exception(f"Failed to disable cooling systems: {str(e)}")
    
    def apply_power_failure_schedule(self, model, weather_type):
        """Apply power failure schedule during outage period."""
        try:
            # Get outage start date based on weather type
            if weather_type == 'CWEC':
                outage_start = self.extreme_periods['cwec_outage_start_date']
            else:  # EWY
                outage_start = self.extreme_periods['ewy_outage_start_date']
            
            # Create power failure schedule
            power_schedule = openstudio.model.ScheduleRuleset(model)
            power_schedule.setName("Power Failure Schedule")
            
            # Default is normal operation (1.0)
            default_day = power_schedule.defaultDaySchedule()
            default_day.addValue(openstudio.Time(1, 0), 1.0)
            
            # Add outage rule (0.0 for no power)
            outage_rule = openstudio.model.ScheduleRule(power_schedule)
            outage_rule.setName("Power Outage Rule")
            
            # Set outage dates
            start_date = datetime.strptime(outage_start, '%Y-%m-%d')
            end_date = start_date + timedelta(days=self.outage_days - 1)
            
            outage_rule.setStartDate(openstudio.Date(
                openstudio.MonthOfYear(start_date.month), start_date.day))
            outage_rule.setEndDate(openstudio.Date(
                openstudio.MonthOfYear(end_date.month), end_date.day))
            
            # Set power failure value (0.0 = no power)
            outage_day = outage_rule.daySchedule()
            outage_day.addValue(openstudio.Time(1, 0), 0.0)
            
            # Apply power failure schedule to all electrical equipment
            self.apply_power_schedule_to_equipment(model, power_schedule)
            
        except Exception as e:
            raise Exception(f"Failed to apply power failure schedule: {str(e)}")
    
    def apply_power_schedule_to_equipment(self, model, power_schedule):
        """Apply power failure schedule to all electrical equipment."""
        try:
            # Apply to HVAC equipment
            for fan in model.getFanConstantVolumes():
                fan.setAvailabilitySchedule(power_schedule)
            
            for fan in model.getFanVariableVolumes():
                fan.setAvailabilitySchedule(power_schedule)
            
            # Apply to heating equipment
            for furnace in model.getAirLoopHVACUnitaryHeatPumpAirToAirs():
                furnace.setAvailabilitySchedule(power_schedule)
            
            # Apply to other electrical loads
            for electric_equipment in model.getElectricEquipments():
                electric_equipment.setSchedule(power_schedule)
            
            for lights in model.getLightss():
                lights.setSchedule(power_schedule)
                
        except Exception as e:
            raise Exception(f"Failed to apply power schedule to equipment: {str(e)}")

    def run_simulations(self):
        """Run OpenStudio simulations for all scenarios."""
        import subprocess
        
        # Define scenarios and their associated weather files
        scenarios = {
            'baseline': {
                'path': self.baseline_path,
                'weather_file': self.cwec_epw_path,
                'name': 'baseline'
            },
            'outage_typical_year': {
                'path': self.scenario_paths['outage_typical_year'],
                'weather_file': self.cwec_epw_path,
                'name': 'outage_typical_year'
            },
            'outage_extreme_year': {
                'path': self.scenario_paths['outage_extreme_year'],
                'weather_file': self.ewy_epw_path,
                'name': 'outage_extreme_year'
            },
            'thermal_autonomy_typical_year': {
                'path': self.scenario_paths['thermal_autonomy_typical_year'],
                'weather_file': self.cwec_epw_path,
                'name': 'thermal_autonomy_typical_year'
            },
            'thermal_autonomy_extreme_year': {
                'path': self.scenario_paths['thermal_autonomy_extreme_year'],
                'weather_file': self.ewy_epw_path,
                'name': 'thermal_autonomy_extreme_year'
            }
        }
        
        for scenario_name, scenario_info in scenarios.items():
            click.echo(f"  Running simulation for {scenario_name}...")
            success = self._run_single_simulation(
                scenario_info['path'],
                scenario_info['weather_file'],
                scenario_info['name']
            )
            if success:
                click.echo(f"    ✓ {scenario_name} simulation completed successfully")
            else:
                click.echo(f"    ✗ {scenario_name} simulation failed")

    def _run_single_simulation(self, scenario_path, weather_file, scenario_name):
        """Run a single OpenStudio simulation with proper error handling."""
        import subprocess
        
        osm_path = os.path.join(scenario_path, f"{scenario_name}.osm")
        log_path = os.path.join(scenario_path, "log.txt")
        
        # Check if OSM file exists
        if not os.path.exists(osm_path):
            with open(log_path, 'w') as log_file:
                log_file.write(f"ERROR: OSM file not found: {osm_path}\n")
            return False
        
        # Check if weather file exists
        if not os.path.exists(weather_file):
            with open(log_path, 'w') as log_file:
                log_file.write(f"ERROR: Weather file not found: {weather_file}\n")
            return False
        
        try:
            # Change to scenario directory to ensure outputs are written there
            original_dir = os.getcwd()
            os.chdir(scenario_path)
            
            with open(log_path, 'w') as log_file:
                log_file.write(f"Running simulation for {scenario_name}\n")
                log_file.write(f"OSM file: {osm_path}\n")
                log_file.write(f"Weather file: {weather_file}\n")
                log_file.write("=" * 50 + "\n")
                
                # Step 1: Convert OSM to IDF using OpenStudio forward translator
                log_file.write("Step 1: Converting OSM to IDF...\n")
                log_file.flush()
                
                # Use OpenStudio Python API to convert OSM to IDF
                try:
                    optional_model = openstudio.model.Model.load(osm_path)
                    if not optional_model.is_initialized():
                        raise Exception("Failed to load OSM model")
                    
                    model = optional_model.get()
                    
                    # Set up forward translator
                    ft = openstudio.energyplus.ForwardTranslator()
                    workspace = ft.translateModel(model)
                    
                    # Save IDF file
                    idf_path = os.path.join(scenario_path, "in.idf")
                    workspace.save(idf_path, True)
                    
                    log_file.write(f"Successfully converted OSM to IDF: {idf_path}\n")
                    
                except Exception as e:
                    log_file.write(f"ERROR: Failed to convert OSM to IDF: {str(e)}\n")
                    os.chdir(original_dir)
                    return False
                
                # Step 2: Run EnergyPlus simulation
                log_file.write("Step 2: Running EnergyPlus simulation...\n")
                log_file.flush()
                
                cmd = [
                    'energyplus',
                    '--weather', weather_file,
                    '--output-directory', scenario_path,
                    'in.idf'
                ]
                
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write("=" * 50 + "\n")
                
                # Run the simulation
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                
                # Log stdout and stderr
                log_file.write("STDOUT:\n")
                log_file.write(result.stdout)
                log_file.write("\nSTDERR:\n")
                log_file.write(result.stderr)
                log_file.write(f"\nReturn code: {result.returncode}\n")
            
            # Change back to original directory
            os.chdir(original_dir)
            
            # Check if simulation was successful
            success = self._check_simulation_success(scenario_path, log_path)
            return success
            
        except subprocess.TimeoutExpired:
            os.chdir(original_dir)
            with open(log_path, 'a') as log_file:
                log_file.write("\nERROR: Simulation timed out after 1 hour\n")
            return False
        except Exception as e:
            os.chdir(original_dir)
            with open(log_path, 'a') as log_file:
                log_file.write(f"\nERROR: Exception during simulation: {str(e)}\n")
            return False

    def _check_simulation_success(self, scenario_path, log_path):
        """Check if the simulation completed successfully."""
        success = True
        
        with open(log_path, 'a') as log_file:
            log_file.write("\n" + "=" * 50 + "\n")
            log_file.write("POST-SIMULATION CHECKS:\n")
            
            # Check if eplusout.sql exists
            sql_path = os.path.join(scenario_path, "eplusout.sql")
            if os.path.exists(sql_path):
                log_file.write("✓ eplusout.sql file created successfully\n")
            else:
                log_file.write("✗ eplusout.sql file was not created - simulation may have failed\n")
                success = False
            
            # Check eplusout.err for fatal or severe errors
            err_path = os.path.join(scenario_path, "eplusout.err")
            if os.path.exists(err_path):
                try:
                    with open(err_path, 'r') as err_file:
                        err_content = err_file.read()
                        
                    fatal_errors = []
                    severe_errors = []
                    
                    for line in err_content.split('\n'):
                        line_lower = line.lower()
                        if '** fatal **' in line_lower:
                            fatal_errors.append(line.strip())
                        elif '**  severe  **' in line_lower:
                            severe_errors.append(line.strip())
                    
                    if fatal_errors:
                        log_file.write(f"✗ Found {len(fatal_errors)} fatal error(s) in eplusout.err:\n")
                        for error in fatal_errors:
                            log_file.write(f"  {error}\n")
                        success = False
                    
                    if severe_errors:
                        log_file.write(f"✗ Found {len(severe_errors)} severe error(s) in eplusout.err:\n")
                        for error in severe_errors:
                            log_file.write(f"  {error}\n")
                        success = False
                    
                    if not fatal_errors and not severe_errors:
                        log_file.write("✓ No fatal or severe errors found in eplusout.err\n")
                        
                except Exception as e:
                    log_file.write(f"✗ Error reading eplusout.err: {str(e)}\n")
                    success = False
            else:
                log_file.write("✗ eplusout.err file not found\n")
                success = False
            
            # Check if required output variables are present in eplusout.sql
            if os.path.exists(sql_path):
                output_vars_success = self._check_output_variables(sql_path, log_file)
                if not output_vars_success:
                    success = False
            
            if success:
                log_file.write("✓ Simulation completed successfully\n")
            else:
                log_file.write("✗ Simulation failed or completed with errors\n")
        
        return success

    def _check_output_variables(self, sql_path, log_file):
        """Check if the required output variables are present in the SQL file."""
        try:
            import sqlite3
            
            # Required output variables (as they appear in the SQL database)
            required_variables = [
                'Site Outdoor Air Relative Humidity',
                'Zone Air Temperature', 
                'Zone Air Relative Humidity',
                'Zone Mean Radiant Temperature',
                'Zone Operative Temperature',
                'Zone People Occupant Count'
            ]
            
            # Connect to the SQL database
            conn = sqlite3.connect(sql_path)
            cursor = conn.cursor()
            
            # Query the ReportDataDictionary table to see what variables are available
            cursor.execute("""
                SELECT DISTINCT Name, ReportingFrequency 
                FROM ReportDataDictionary
                WHERE ReportingFrequency = 'Hourly'
            """)
            
            available_variables = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            
            # Check each required variable
            missing_variables = []
            found_variables = []
            
            for var in required_variables:
                if var in available_variables:
                    found_variables.append(var)
                    log_file.write(f"✓ Found hourly output variable: {var}\n")
                else:
                    missing_variables.append(var)
                    log_file.write(f"✗ Missing hourly output variable: {var}\n")
            
            if missing_variables:
                log_file.write(f"✗ {len(missing_variables)} required output variables are missing\n")
                return False
            else:
                log_file.write(f"✓ All {len(required_variables)} required output variables found with hourly frequency\n")
                return True
                
        except Exception as e:
            log_file.write(f"✗ Error checking output variables in SQL file: {str(e)}\n")
            return False


if __name__ == '__main__':
    resilience()
