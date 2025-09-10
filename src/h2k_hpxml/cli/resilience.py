#!/usr/bin/env python3
"""
Resilience CLI Tool

A command-line interface tool that analyzes building resiliency scenarios by examining
clothing factors and HVAC performance during power outages and extreme weather conditions.
"""

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from datetime import timedelta

import click
import yaml

from h2k_hpxml.config import ConfigManager
from h2k_hpxml.core.translator import h2ktohpxml
from h2k_hpxml.utils.dependencies import DependencyManager
from h2k_hpxml.utils.dependencies import safe_echo


def get_openstudio_binary_path():
    """Get the OpenStudio binary path for the current platform."""
    # First try to get from installer (bundled dependencies)
    try:
        from ..utils.dependencies import get_openstudio_path

        bundled_path = get_openstudio_path()
        if bundled_path and os.path.exists(bundled_path):
            return bundled_path
    except ImportError:
        pass

    # Then try DependencyManager for backward compatibility
    dep_manager = DependencyManager()

    # Try to find OpenStudio binary in common locations
    for openstudio_path in dep_manager._get_openstudio_paths():
        if dep_manager._test_binary_path(openstudio_path):
            return openstudio_path

    # Try the command in PATH
    if dep_manager._test_openstudio_command():
        return "openstudio"  # Found in PATH

    # Fallback to platform-specific defaults
    if platform.system() == "Windows":
        return "C:\\openstudio\\bin\\openstudio.exe"
    else:
        return "/usr/local/bin/openstudio"


def safe_log_write(log_file, message):
    """Write message to log file with Unicode character replacement for cross-platform compatibility."""
    # Replace Unicode characters with ASCII equivalents for log files
    replacements = {
        "✓": "[OK]",
        "✗": "[ERROR]",
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "⚠": "[WARNING]",
        "🔄": "[PROCESSING]",
    }
    for unicode_char, ascii_equiv in replacements.items():
        message = message.replace(unicode_char, ascii_equiv)
    log_file.write(message)


# Check for OpenStudio Python bindings
try:
    import openstudio

    OPENSTUDIO_AVAILABLE = True
except ImportError:
    OPENSTUDIO_AVAILABLE = False

# Constants
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_ENCODING = "utf-8"
DEFAULT_OUTAGE_DAYS = 7
DEFAULT_SUMMER_CLOTHING = 0.5
DEFAULT_WINTER_CLOTHING = 1.0
CONVERSION_TIMEOUT_SECONDS = 300
EPW_HEADER_LINES = 8
NOON_HOUR = 12
DEFAULT_YEAR = 2023  # Non-leap year for date calculations
SUMMER_START_DEFAULT = (6, 1)  # June 1st
SUMMER_END_DEFAULT = (8, 31)  # August 31st


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("h2k_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--outage-days",
    default=DEFAULT_OUTAGE_DAYS,
    type=click.IntRange(0, 365),
    help=("Number of days for power outage analysis (default: 7, range: 0-365)"),
)
@click.option(
    "--output-path",
    type=click.Path(),
    help=("Output folder path (default: same directory as H2K input file)"),
)
@click.option(
    "--clothing-factor-summer",
    default=DEFAULT_SUMMER_CLOTHING,
    type=click.FloatRange(0.0, 2.0),
    help=("Summer clothing insulation factor (default: 0.5, range: 0.0-2.0)"),
)
@click.option(
    "--clothing-factor-winter",
    default=DEFAULT_WINTER_CLOTHING,
    type=click.FloatRange(0.0, 2.0),
    help=("Winter clothing insulation factor (default: 1.0, range: 0.0-2.0)"),
)
@click.option(
    "--run-simulation",
    is_flag=True,
    default=False,
    help="Run the OpenStudio simulations for all scenarios (default: False)",
)
@click.version_option(version="1.0.0")
def resilience(
    h2k_path,
    outage_days,
    output_path,
    clothing_factor_summer,
    clothing_factor_winter,
    run_simulation,
):
    """
    Analyze building resiliency scenarios using H2K file input.

    This tool converts H2K files to OpenStudio models and creates four scenarios:

    - outage_typical_year: Power outage during typical weather (CWEC)
    - outage_extreme_year: Power outage during extreme weather (EWY)
    - thermal_autonomy_typical_year: No cooling/heating during typical weather
    - thermal_autonomy_extreme_year: No cooling/heating during extreme weather

    Args:
        h2k_path (str): Path to H2K input file
        outage_days (int): Number of days for power outage analysis
        output_path (str): Output folder path for results
        clothing_factor_summer (float): Summer clothing insulation factor
        clothing_factor_winter (float): Winter clothing insulation factor
        run_simulation (bool): Whether to run OpenStudio simulations
    """
    try:
        # Check for OpenStudio availability
        if not OPENSTUDIO_AVAILABLE:
            click.echo("Error: OpenStudio Python bindings are not available.", err=True)
            click.echo(
                "Please ensure OpenStudio is properly installed with Python bindings.", err=True
            )
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
        click.echo(
            f"Clothing factors - Summer: {clothing_factor_summer}, Winter: {clothing_factor_winter}"
        )
        click.echo(f"Run simulations: {run_simulation}")

        # Initialize processor
        processor = ResilienceProcessor(
            h2k_path=h2k_path,
            output_path=output_path,
            outage_days=outage_days,
            clothing_factor_summer=clothing_factor_summer,
            clothing_factor_winter=clothing_factor_winter,
            run_simulation=run_simulation,
        )

        # Run the complete workflow
        processor.run()

        click.echo("Resilience analysis completed successfully!")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo(f"Traceback: {traceback.format_exc()}", err=True)
        sys.exit(1)


class ResilienceProcessor:
    """
    Main processor class for resilience analysis.

    Handles the complete workflow for analyzing building resilience scenarios
    including H2K to HPXML conversion, weather file processing, and simulation.
    """

    def __init__(
        self,
        h2k_path,
        output_path,
        outage_days,
        clothing_factor_summer,
        clothing_factor_winter,
        run_simulation=False,
    ):
        self.h2k_path = h2k_path
        self.outage_days = outage_days
        self.clothing_factor_summer = clothing_factor_summer
        self.clothing_factor_winter = clothing_factor_winter
        self.run_simulation = run_simulation

        # Create project folder structure based on H2K file basename
        h2k_basename = os.path.splitext(os.path.basename(h2k_path))[0]
        self.project_folder = os.path.join(output_path, h2k_basename)

        # Create project directory structure
        os.makedirs(self.project_folder, exist_ok=True)
        self.original_folder = os.path.join(self.project_folder, "original")
        os.makedirs(self.original_folder, exist_ok=True)

        # Copy original H2K file to project folder
        original_h2k_path = os.path.join(self.project_folder, "original.h2k")
        if not os.path.exists(original_h2k_path):
            shutil.copy2(h2k_path, original_h2k_path)
            click.echo(f"Copied original H2K file to: {original_h2k_path}")

        # Update paths to use new structure
        self.output_path = self.project_folder
        self.baseline_path = self.original_folder  # Use original folder instead of baseline

        # Scenario paths within project folder
        self.scenario_paths = {
            "outage_typical_year": os.path.join(self.project_folder, "outage_typical_year"),
            "outage_extreme_year": os.path.join(self.project_folder, "outage_extreme_year"),
            "thermal_autonomy_typical_year": os.path.join(
                self.project_folder, "thermal_autonomy_typical_year"
            ),
            "thermal_autonomy_extreme_year": os.path.join(
                self.project_folder, "thermal_autonomy_extreme_year"
            ),
        }

        for path in self.scenario_paths.values():
            os.makedirs(path, exist_ok=True)

    def run(self):
        """
        Execute the complete resilience analysis workflow.

        This method orchestrates the entire resilience analysis process:
        1. Validates OpenStudio-HPXML availability
        2. Converts H2K file to HPXML/OSM format
        3. Processes weather files to find extreme periods
        4. Determines seasonal boundaries
        5. Generates resilience scenarios
        6. Optionally runs simulations

        Raises:
            SystemExit: If any critical step fails or dependencies are missing
        """
        # Check OpenStudio-HPXML availability before starting any workflow
        self._validate_openstudio_hpxml()

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
        """
        Add required output variables to the OpenStudio model.

        Adds variables needed for resilience analysis including temperature,
        humidity, and occupancy data with hourly reporting frequency.

        Args:
            model: OpenStudio Model object to modify

        Raises:
            Exception: If adding output variables fails
        """
        try:
            # Define the required output variables
            output_variables = [
                "Site Outdoor Air Relative Humidity",
                "Zone Air Temperature",
                "Zone Air Relative Humidity",
                "Zone Mean Radiant Temperature",
                "Zone Operative Temperature",
                "Zone People Occupant Count",
            ]

            # Add each output variable with hourly frequency
            for var_name in output_variables:
                output_var = openstudio.model.OutputVariable(var_name, model)
                output_var.setReportingFrequency("Hourly")

                # For zone-specific variables, apply to all zones
                if var_name.startswith("Zone"):
                    output_var.setKeyValue("*")  # Apply to all zones

        except Exception as e:
            raise Exception(f"Failed to add output variables: {str(e)}")

    def convert_h2k_to_osm(self):
        """Convert H2K file to OSM format using h2ktohpxml converter."""
        try:
            # Read H2K file with proper encoding detection
            encoding = self.detect_xml_encoding(self.h2k_path)
            with open(self.h2k_path, encoding=encoding) as f:
                h2k_string = f.read()

            # Convert to HPXML
            click.echo("Converting H2K to HPXML...")
            hpxml_string = h2ktohpxml(h2k_string)

            # Save HPXML file
            hpxml_path = os.path.join(self.original_folder, "original.xml")
            with open(hpxml_path, "w", encoding=DEFAULT_ENCODING) as f:
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
            match = re.search(rb'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
            if match:
                return match.group(1).decode("ascii")
        return DEFAULT_ENCODING  # fallback

    def convert_hpxml_to_osm(self, hpxml_path):
        """Convert HPXML to OSM using OpenStudio-HPXML workflow."""
        try:
            # Use the OpenStudio-HPXML workflow to convert HPXML to OSM

            # Load configuration using ConfigManager
            config_manager = ConfigManager()
            hpxml_os_path = str(config_manager.hpxml_os_path)
            ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

            # Check if OpenStudio-HPXML is available
            if not os.path.exists(hpxml_os_path):
                click.echo(f"ERROR: OpenStudio-HPXML not found at {hpxml_os_path}", err=True)
                click.echo("OpenStudio-HPXML is required for resilience analysis.", err=True)
                click.echo(
                    "Please install OpenStudio-HPXML and ensure it is properly configured.",
                    err=True,
                )
                sys.exit(1)

            if not os.path.exists(ruby_hpxml_path):
                click.echo(f"ERROR: HPXML workflow not found at {ruby_hpxml_path}", err=True)
                click.echo(
                    "OpenStudio-HPXML workflow script is required for resilience analysis.",
                    err=True,
                )
                click.echo(
                    "Please install OpenStudio-HPXML and ensure it is properly configured.",
                    err=True,
                )
                sys.exit(1)

            # Run the HPXML to OSM conversion
            output_dir = os.path.join(self.original_folder, "hpxml_run")
            os.makedirs(output_dir, exist_ok=True)

            openstudio_binary = get_openstudio_binary_path()
            command = [
                openstudio_binary,
                ruby_hpxml_path,
                "-x",
                hpxml_path,
                "-o",
                output_dir,
                "--skip-simulation",  # We only want the OSM, not the full simulation
                "-d",  # Debug mode to get more files
            ]

            click.echo("Converting HPXML to OSM using OpenStudio-HPXML workflow...")
            result = subprocess.run(
                command,
                cwd=hpxml_os_path,
                capture_output=True,
                text=True,
                timeout=CONVERSION_TIMEOUT_SECONDS,  # 5 minute timeout
            )

            if result.returncode != 0:
                click.echo(f"ERROR: HPXML conversion failed: {result.stderr}", err=True)
                click.echo("OpenStudio-HPXML workflow execution failed.", err=True)
                click.echo(
                    "Please check the HPXML file and OpenStudio-HPXML installation.", err=True
                )
                sys.exit(1)

            # Look for the generated OSM file
            # The OpenStudio-HPXML workflow creates files in the specified output directory
            potential_osm_files = [
                os.path.join(output_dir, "run", "in.osm"),  # Most likely location
                os.path.join(output_dir, "in.osm"),
                os.path.join(output_dir, "run.osm"),
                os.path.join(output_dir, "resources", "in.osm"),
            ]

            source_osm_path = None
            for osm_file in potential_osm_files:
                if os.path.exists(osm_file):
                    source_osm_path = osm_file
                    break

            if source_osm_path is None:
                click.echo(
                    "ERROR: Could not find generated OSM file from OpenStudio-HPXML workflow",
                    err=True,
                )
                click.echo(
                    "The HPXML to OSM conversion did not produce the expected output files.",
                    err=True,
                )
                click.echo(
                    "Please check the HPXML file and OpenStudio-HPXML installation.", err=True
                )
                sys.exit(1)

            # Copy the generated OSM to our original directory
            osm_path = os.path.join(self.original_folder, "original.osm")
            shutil.copy2(source_osm_path, osm_path)

            # Load the model to get the OpenStudio model object
            optional_model = openstudio.model.Model.load(osm_path)
            if not optional_model.is_initialized():
                click.echo(
                    "ERROR: Could not load generated OSM file from OpenStudio-HPXML workflow",
                    err=True,
                )
                click.echo("The generated OSM file appears to be corrupted or invalid.", err=True)
                click.echo(
                    "Please check the HPXML file and OpenStudio-HPXML installation.", err=True
                )
                sys.exit(1)

            model = optional_model.get()

            # Add our required output variables
            self.add_output_variables(model)

            # Save the updated model
            model.save(osm_path, True)
            self.baseline_model = model
            self.baseline_osm_path = osm_path

            click.echo(f"Original OSM created from HPXML: {osm_path}")

        except subprocess.TimeoutExpired:
            click.echo("ERROR: HPXML conversion timed out after 5 minutes", err=True)
            click.echo("The OpenStudio-HPXML workflow is taking too long to complete.", err=True)
            click.echo(
                "Please check the HPXML file size and complexity, or system resources.", err=True
            )
            sys.exit(1)
        except Exception as e:
            click.echo(f"ERROR: HPXML conversion failed: {str(e)}", err=True)
            click.echo(
                "An unexpected error occurred during OpenStudio-HPXML workflow execution.", err=True
            )
            click.echo("Please check the HPXML file and OpenStudio-HPXML installation.", err=True)
            sys.exit(1)

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
                "cwec_outage_start_date": cwec_extreme.strftime("%Y-%m-%d"),
                "ewy_outage_start_date": ewy_extreme.strftime("%Y-%m-%d"),
            }

            extreme_periods_path = os.path.join(self.output_path, "extreme_periods.yml")
            with open(extreme_periods_path, "w") as f:
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
        region_elem = root.find(".//Region/English")
        location_elem = root.find(".//Location/English")

        if region_elem is not None and location_elem is not None:
            region = region_elem.text.strip() if region_elem.text else ""
            location = location_elem.text.strip() if location_elem.text else ""

            # Map H2K location names to CSV names
            if "OTTAWA" in location.upper():
                location = "OTTAWA INTL"

            return {"city": location.upper(), "state": region.upper()}

        raise Exception("Could not extract weather information from H2K file")

    def get_weather_file_paths(self, weather_info):
        """Get CWEC and EWY weather file paths using the weather utility."""
        import csv

        from h2k_hpxml.utils.weather import get_cwec_file

        # Get the standard weather resources folder path
        project_root = self._find_project_root()
        weather_folder = os.path.join(project_root, "src", "h2k_hpxml", "resources", "weather")

        try:
            # Use the get_cwec_file function to download/get CWEC file
            cwec_path_base = get_cwec_file(
                weather_region=weather_info["state"],
                weather_location=weather_info["city"],
                weather_folder=weather_folder,
                weather_vintage="CWEC2020",  # Explicit values since no config_manager
                weather_library="historic",
            )
            cwec_path = f"{cwec_path_base}.epw"

            # Validate that the CWEC file exists
            if not os.path.exists(cwec_path):
                raise Exception(f"CWEC weather file not found after download: {cwec_path}")

            click.echo(f"CWEC weather file located/downloaded: {cwec_path}")

            # For EWY files, we need to get the EWY filename from the CSV
            weather_csv_path = os.path.join(
                project_root, "src", "h2k_hpxml", "resources", "weather", "h2k_weather_names.csv"
            )

            ewy_filename = None
            with open(weather_csv_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (
                        row["cities_english"].upper() == weather_info["city"].upper()
                        and row["provinces_english"].upper() == weather_info["state"].upper()
                    ):
                        ewy_filename = row["EWY2020.zip"]
                        break

            if ewy_filename is None:
                click.echo(
                    f"Warning: No EWY file found for {weather_info['city']}, {weather_info['state']}. Using CWEC file for both scenarios."
                )
                return cwec_path, cwec_path

            # Try to get EWY file using modified get_cwec_file approach
            ewy_path = self.get_ewy_file(
                weather_region=weather_info["state"],
                weather_location=weather_info["city"],
                weather_folder=weather_folder,
                ewy_filename=ewy_filename,
            )

            # Validate that the EWY file exists
            if not os.path.exists(ewy_path):
                click.echo(
                    f"Warning: EWY weather file not found: {ewy_path}. Using CWEC file for extreme scenarios."
                )
                return cwec_path, cwec_path

            click.echo(f"EWY weather file located/downloaded: {ewy_path}")
            return cwec_path, ewy_path

        except Exception as e:
            raise Exception(f"Failed to get weather files: {str(e)}")

    def get_ewy_file(self, weather_region, weather_location, weather_folder, ewy_filename):
        """Download and extract EWY weather file similar to get_cwec_file."""
        import zipfile

        import requests
        from filelock import FileLock

        # Check if EPW file already exists
        epw_file = os.path.join(weather_folder, f"{ewy_filename[:-4]}.epw")
        if os.path.exists(epw_file):
            click.echo(f"EWY weather file already exists: {epw_file}")
            return epw_file

        # For now, use CWEC file as EWY placeholder (as mentioned in requirements)
        # This can be updated when real EWY files become available
        cwec_filename = ewy_filename.replace("EWY2020", "CWEC2020")
        cwec_epw = os.path.join(weather_folder, f"{cwec_filename[:-4]}.epw")

        if os.path.exists(cwec_epw):
            # Copy CWEC file as EWY placeholder
            import shutil

            shutil.copy2(cwec_epw, epw_file)
            click.echo(f"Using CWEC file as EWY placeholder: {epw_file}")
            return epw_file

        # If no CWEC file either, try to download the EWY file directly
        # (this would be updated when real EWY files are available)
        github_url = "https://github.com/canmet-energy/btap_weather/raw/refs/heads/main/historic/"
        file_url = f"{github_url}{ewy_filename}"
        local_zip = os.path.join(os.path.dirname(__file__), ewy_filename)

        lock_file = f"{local_zip}.lock"
        try:
            with FileLock(lock_file):
                # Try to download EWY file (will fail until real EWY files are available)
                response = requests.get(file_url, verify=False)
                if response.status_code == 200:
                    with open(local_zip, "wb") as f:
                        f.write(response.content)

                    # Extract EPW file
                    with zipfile.ZipFile(local_zip, "r") as zip_ref:
                        for file in zip_ref.namelist():
                            if file.endswith(".epw"):
                                zip_ref.extract(file, weather_folder)
                                extracted_path = os.path.join(weather_folder, file)
                                if extracted_path != epw_file:
                                    os.rename(extracted_path, epw_file)
                                return epw_file
                else:
                    # Fallback: use CWEC file with EWY name
                    if os.path.exists(cwec_epw):
                        import shutil

                        shutil.copy2(cwec_epw, epw_file)
                        click.echo(
                            f"EWY download failed (status {response.status_code}). Using CWEC as fallback: {epw_file}"
                        )
                        return epw_file
                    else:
                        raise Exception(
                            "Failed to download EWY file and no CWEC fallback available"
                        )
        except Exception as e:
            # Final fallback: try to find any CWEC file to copy
            if os.path.exists(cwec_epw):
                import shutil

                shutil.copy2(cwec_epw, epw_file)
                click.echo(f"EWY processing failed ({str(e)}). Using CWEC as fallback: {epw_file}")
                return epw_file
            else:
                raise Exception(f"Failed to get EWY file: {str(e)}")

    def find_extreme_period(self, weather_file_path, days):
        """Find the hottest consecutive period in the weather file."""
        try:
            # Read EPW file and extract temperature data
            temperatures = []
            dates = []

            with open(weather_file_path) as f:
                lines = f.readlines()

                # Skip header lines (EPW format)
                for line in lines[EPW_HEADER_LINES:]:
                    parts = line.strip().split(",")
                    if len(parts) > 6:
                        try:
                            month = int(parts[1])
                            day = int(parts[2])
                            hour = int(parts[3])
                            temp = float(parts[6])  # Dry bulb temperature

                            # Only use noon hour for daily analysis
                            if hour == NOON_HOUR:
                                date = datetime(DEFAULT_YEAR, month, day)
                                dates.append(date)
                                temperatures.append(temp)
                        except (ValueError, IndexError):
                            continue

            # Find hottest consecutive period
            max_avg_temp = -999
            best_start_date = None

            for i in range(len(temperatures) - days + 1):
                period_temps = temperatures[i : i + days]
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
                "cwec_summer_start": cwec_summer["start"].strftime("%m-%d"),
                "cwec_summer_end": cwec_summer["end"].strftime("%m-%d"),
                "ewy_summer_start": ewy_summer["start"].strftime("%m-%d"),
                "ewy_summer_end": ewy_summer["end"].strftime("%m-%d"),
            }

            summer_periods_path = os.path.join(self.output_path, "summer_period.yml")
            with open(summer_periods_path, "w") as f:
                yaml.dump(summer_periods, f)

            self.summer_periods = summer_periods
            click.echo(f"Summer periods saved: {summer_periods_path}")
            click.echo(
                f"CWEC Summer: {summer_periods['cwec_summer_start']} to {summer_periods['cwec_summer_end']}"
            )
            click.echo(
                f"EWY Summer: {summer_periods['ewy_summer_start']} to {summer_periods['ewy_summer_end']}"
            )

        except Exception as e:
            raise Exception(f"Failed to determine seasons: {str(e)}")

    # ... (continuing with rest of the methods - this file is getting quite long)
    # I'll include the remaining methods in the implementation

    def _find_project_root(self):
        """Find the project root directory containing conversionconfig.ini."""
        current_dir = pathlib.Path(__file__).parent
        for parent in [current_dir] + list(current_dir.parents):
            # Check for config file in new config/ directory structure first
            config_file = parent / "config" / "conversionconfig.ini"
            if config_file.exists():
                return str(parent)
            # Fallback to old structure for backward compatibility
            config_file = parent / "conversionconfig.ini"
            if config_file.exists():
                return str(parent)
        # Fallback to current working directory
        return os.getcwd()

    def _validate_openstudio_hpxml(self):
        """Validate that OpenStudio-HPXML is available before starting workflow."""
        try:
            # Use ConfigManager to get paths (it will find config in new structure)
            config_manager = ConfigManager()
            hpxml_os_path = str(config_manager.hpxml_os_path)
            ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

            # Check if OpenStudio-HPXML is available
            if not os.path.exists(hpxml_os_path):
                click.echo(f"ERROR: OpenStudio-HPXML not found at {hpxml_os_path}", err=True)
                click.echo("OpenStudio-HPXML is required for resilience analysis.", err=True)
                click.echo(
                    "Please install OpenStudio-HPXML and ensure it is properly configured in conversionconfig.ini.",
                    err=True,
                )
                sys.exit(1)

            if not os.path.exists(ruby_hpxml_path):
                click.echo(f"ERROR: HPXML workflow not found at {ruby_hpxml_path}", err=True)
                click.echo(
                    "OpenStudio-HPXML workflow script is required for resilience analysis.",
                    err=True,
                )
                click.echo(
                    "Please install OpenStudio-HPXML and ensure it is properly configured.",
                    err=True,
                )
                sys.exit(1)

            safe_echo(f"✓ OpenStudio-HPXML validated at: {hpxml_os_path}")

        except Exception as e:
            click.echo(f"ERROR: Failed to validate OpenStudio-HPXML: {str(e)}", err=True)
            click.echo(
                "Please ensure OpenStudio-HPXML is properly installed and configured.", err=True
            )
            sys.exit(1)

    # Add placeholder methods for remaining functionality
    def analyze_summer_period(self, weather_file_path, weather_type):
        """
        Analyze a single weather file to determine summer period.

        Args:
            weather_file_path (str): Path to EPW weather file
            weather_type (str): Weather type identifier (CWEC or EWY)

        Returns:
            dict: Dictionary with 'start' and 'end' datetime objects
        """
        try:
            # Read daily temperature data from EPW file
            daily_temps = []
            dates = []

            with open(weather_file_path) as f:
                lines = f.readlines()

                current_day_temps = []
                current_date = None

                # Skip header lines (EPW format)
                for line in lines[EPW_HEADER_LINES:]:
                    parts = line.strip().split(",")
                    if len(parts) > 6:
                        try:
                            month = int(parts[1])
                            day = int(parts[2])
                            int(parts[3])
                            temp = float(parts[6])  # Dry bulb temperature

                            date = datetime(DEFAULT_YEAR, month, day)

                            # New day
                            if current_date != date:
                                # Process previous day
                                if current_day_temps and current_date:
                                    daily_avg = sum(current_day_temps) / len(current_day_temps)
                                    daily_temps.append(daily_avg)
                                    dates.append(current_date)

                                # Start new day
                                current_date = date
                                current_day_temps = [temp]
                            else:
                                current_day_temps.append(temp)

                        except (ValueError, IndexError):
                            continue

                # Process final day
                if current_day_temps and current_date:
                    daily_avg = sum(current_day_temps) / len(current_day_temps)
                    daily_temps.append(daily_avg)
                    dates.append(current_date)

            # Find all consecutive periods ≥7 days where temp > 15°C
            summer_periods = []
            current_start = None
            current_length = 0

            for i, temp in enumerate(daily_temps):
                if temp > 15.0:
                    if current_start is None:
                        current_start = i
                        current_length = 1
                    else:
                        current_length += 1
                else:
                    # End of hot period
                    if current_start is not None and current_length >= 7:
                        summer_periods.append(
                            {
                                "start": dates[current_start],
                                "end": dates[current_start + current_length - 1],
                                "length": current_length,
                            }
                        )
                    current_start = None
                    current_length = 0

            # Check final period
            if current_start is not None and current_length >= 7:
                summer_periods.append(
                    {
                        "start": dates[current_start],
                        "end": dates[current_start + current_length - 1],
                        "length": current_length,
                    }
                )

            # Choose longest period as summer
            if summer_periods:
                longest_period = max(summer_periods, key=lambda x: x["length"])
                return {"start": longest_period["start"], "end": longest_period["end"]}
            else:
                # Fallback to meteorological summer
                click.echo(
                    f"Warning: No clear summer period found in {weather_type}, using meteorological summer"
                )
                return {
                    "start": datetime(DEFAULT_YEAR, *SUMMER_START_DEFAULT),
                    "end": datetime(DEFAULT_YEAR, *SUMMER_END_DEFAULT),
                }

        except Exception as e:
            # Fallback to default summer period on error
            click.echo(f"Warning: Failed to analyze {weather_type} weather file: {str(e)}")
            return {
                "start": datetime(DEFAULT_YEAR, *SUMMER_START_DEFAULT),
                "end": datetime(DEFAULT_YEAR, *SUMMER_END_DEFAULT),
            }

    def _apply_weather_file(self, model, weather_type):
        """
        Apply the appropriate weather file to the model.

        Args:
            model: OpenStudio Model object
            weather_type: 'CWEC' for typical year or 'EWY' for extreme year
        """
        try:
            # Get the appropriate weather file path
            if weather_type == "CWEC":
                epw_path = self.cwec_epw_path
            else:  # EWY
                epw_path = self.ewy_epw_path

            # Set weather file using proper OpenStudio API
            epw_file = openstudio.EpwFile(openstudio.toPath(epw_path))
            weather_file_optional = openstudio.model.WeatherFile.setWeatherFile(model, epw_file)
            if weather_file_optional.is_initialized():
                click.echo(f"    Applied {weather_type} weather file: {os.path.basename(epw_path)}")
            else:
                raise Exception(f"Failed to set weather file: {epw_path}")

        except Exception as e:
            raise Exception(f"Failed to apply weather file: {str(e)}")

    def _create_clothing_schedule(self, model):
        """
        Create seasonal clothing schedule and apply to all people definitions.

        Args:
            model: OpenStudio Model object
        """
        try:
            # Remove existing clothing schedules from all people definitions
            for people_def in model.getPeopleDefinitions():
                # Try different method names for clothing schedule access
                if hasattr(people_def, "clothingInsulationSchedule"):
                    if people_def.clothingInsulationSchedule().is_initialized():
                        people_def.resetClothingInsulationSchedule()
                elif hasattr(people_def, "getClothingInsulationSchedule"):
                    if people_def.getClothingInsulationSchedule().is_initialized():
                        people_def.resetClothingInsulationSchedule()

            # Remove orphaned clothing schedules
            for schedule in model.getScheduleRulesets():
                if "clothing" in schedule.name().get().lower():
                    schedule.remove()

            # Create new seasonal clothing schedule
            clothing_schedule = openstudio.model.ScheduleRuleset(model)
            clothing_schedule.setName("Seasonal Clothing Schedule")

            # Set default value (winter clothing)
            default_day = clothing_schedule.defaultDaySchedule()
            default_day.addValue(openstudio.Time(0, 24, 0, 0), self.clothing_factor_winter)

            # Add summer rule using summer periods
            summer_rule = openstudio.model.ScheduleRule(clothing_schedule)
            summer_rule.setName("Summer Clothing Rule")

            # Apply summer rule during summer period
            if hasattr(self, "summer_periods"):
                # Use CWEC summer period (both should be similar)
                summer_start = datetime.strptime(self.summer_periods["cwec_summer_start"], "%m-%d")
                summer_end = datetime.strptime(self.summer_periods["cwec_summer_end"], "%m-%d")

                summer_rule.setStartDate(
                    openstudio.Date(openstudio.MonthOfYear(summer_start.month), summer_start.day)
                )
                summer_rule.setEndDate(
                    openstudio.Date(openstudio.MonthOfYear(summer_end.month), summer_end.day)
                )
            else:
                # Fallback to default summer period
                summer_rule.setStartDate(
                    openstudio.Date(
                        openstudio.MonthOfYear(SUMMER_START_DEFAULT[0]), SUMMER_START_DEFAULT[1]
                    )
                )
                summer_rule.setEndDate(
                    openstudio.Date(
                        openstudio.MonthOfYear(SUMMER_END_DEFAULT[0]), SUMMER_END_DEFAULT[1]
                    )
                )

            # Set summer clothing value
            summer_day = summer_rule.daySchedule()
            summer_day.addValue(openstudio.Time(0, 24, 0, 0), self.clothing_factor_summer)

            # Apply clothing schedule to all people definitions
            for people_def in model.getPeopleDefinitions():
                if hasattr(people_def, "setClothingInsulationSchedule"):
                    people_def.setClothingInsulationSchedule(clothing_schedule)
                else:
                    # Skip clothing schedule if API not available
                    click.echo(
                        "    Warning: Clothing insulation schedule API not available in this OpenStudio version"
                    )

            click.echo(
                f"    Created seasonal clothing schedule (Summer: {self.clothing_factor_summer}, Winter: {self.clothing_factor_winter})"
            )

        except Exception as e:
            raise Exception(f"Failed to create clothing schedule: {str(e)}")

    def _ensure_cooling_enabled(self, model):
        """
        Ensure cooling systems are enabled in the model.

        Args:
            model: OpenStudio Model object
        """
        try:
            # For most HPXML models, cooling should already be present
            # Just ensure thermostats have cooling setpoints
            for zone in model.getThermalZones():
                thermostat = zone.thermostatSetpointDualSetpoint()
                if thermostat.is_initialized():
                    tstat = thermostat.get()
                    if not tstat.coolingSetpointTemperatureSchedule().is_initialized():
                        # Add default cooling schedule if missing
                        cooling_schedule = openstudio.model.ScheduleConstant(model)
                        cooling_schedule.setName("Default Cooling Schedule")
                        cooling_schedule.setValue(26.0)  # 26°C cooling setpoint
                        tstat.setCoolingSetpointTemperatureSchedule(cooling_schedule)

            click.echo("    Ensured cooling systems are enabled")

        except Exception as e:
            raise Exception(f"Failed to ensure cooling enabled: {str(e)}")

    def _disable_cooling_systems(self, model):
        """
        Disable all cooling systems in the model for thermal autonomy scenarios.

        Args:
            model: OpenStudio Model object
        """
        try:
            # Remove cooling setpoints from all thermostats
            for zone in model.getThermalZones():
                thermostat = zone.thermostatSetpointDualSetpoint()
                if thermostat.is_initialized():
                    tstat = thermostat.get()
                    tstat.resetCoolingSetpointTemperatureSchedule()

            # Disable cooling coils
            for cooling_coil in model.getCoilCoolingDXSingleSpeeds():
                # Set very low efficiency to effectively disable
                cooling_coil.setRatedCOP(0.1)

            for cooling_coil in model.getCoilCoolingDXTwoSpeeds():
                cooling_coil.setRatedHighSpeedCOP(0.1)
                cooling_coil.setRatedLowSpeedCOP(0.1)

            click.echo("    Disabled all cooling systems")

        except Exception as e:
            raise Exception(f"Failed to disable cooling systems: {str(e)}")

    def _create_power_failure_schedule(self, model, weather_type):
        """
        Create power failure schedule for outage scenarios.

        Args:
            model: OpenStudio Model object
            weather_type: 'CWEC' or 'EWY' to determine outage period
        """
        try:
            # Get outage start date
            if weather_type == "CWEC":
                outage_start = datetime.strptime(
                    self.extreme_periods["cwec_outage_start_date"], "%Y-%m-%d"
                )
            else:  # EWY
                outage_start = datetime.strptime(
                    self.extreme_periods["ewy_outage_start_date"], "%Y-%m-%d"
                )

            # Create power failure schedule
            power_schedule = openstudio.model.ScheduleRuleset(model)
            power_schedule.setName("Power Failure Schedule")

            # Default: power available (1.0)
            default_day = power_schedule.defaultDaySchedule()
            default_day.addValue(openstudio.Time(0, 24, 0, 0), 1.0)

            # Create outage rule: power unavailable (0.0)
            outage_rule = openstudio.model.ScheduleRule(power_schedule)
            outage_rule.setName("Power Outage Rule")

            # Set outage period dates
            outage_end = outage_start + timedelta(days=self.outage_days - 1)
            outage_rule.setStartDate(
                openstudio.Date(openstudio.MonthOfYear(outage_start.month), outage_start.day)
            )
            outage_rule.setEndDate(
                openstudio.Date(openstudio.MonthOfYear(outage_end.month), outage_end.day)
            )

            # Set power failure value
            outage_day = outage_rule.daySchedule()
            outage_day.addValue(openstudio.Time(0, 24, 0, 0), 0.0)

            # Apply power failure schedule to heating/cooling equipment
            self._apply_power_failure_to_equipment(model, power_schedule)

            click.echo(
                f"    Created power failure schedule: {outage_start.strftime('%Y-%m-%d')} to {outage_end.strftime('%Y-%m-%d')}"
            )

        except Exception as e:
            raise Exception(f"Failed to create power failure schedule: {str(e)}")

    def _apply_power_failure_to_equipment(self, model, power_schedule):
        """
        Apply power failure schedule to all electrical equipment.

        Args:
            model: OpenStudio Model object
            power_schedule: Schedule representing power availability
        """
        try:
            # Apply to HVAC equipment
            for heating_coil in model.getCoilHeatingDXSingleSpeeds():
                heating_coil.setAvailabilitySchedule(power_schedule)

            for cooling_coil in model.getCoilCoolingDXSingleSpeeds():
                cooling_coil.setAvailabilitySchedule(power_schedule)

            for fan in model.getFanConstantVolumes():
                fan.setAvailabilitySchedule(power_schedule)

            for fan in model.getFanVariableVolumes():
                fan.setAvailabilitySchedule(power_schedule)

            # Apply to air loops
            for air_loop in model.getAirLoopHVACs():
                air_loop.setAvailabilitySchedule(power_schedule)

            # Apply to plant loops using availability manager
            for plant_loop in model.getPlantLoops():
                # Create and add availability manager with power schedule
                avail_mgr = openstudio.model.AvailabilityManagerScheduled(model)
                avail_mgr.setSchedule(power_schedule)
                plant_loop.addAvailabilityManager(avail_mgr)

            click.echo("    Applied power failure schedule to all electrical equipment")

        except Exception as e:
            raise Exception(f"Failed to apply power failure to equipment: {str(e)}")

    def generate_scenarios(self):
        """
        Generate all four resilience scenarios using OpenStudio model manipulation.

        Creates four distinct scenarios:
        1. outage_typical_year - Power outage during CWEC weather
        2. outage_extreme_year - Power outage during EWY weather
        3. thermal_autonomy_typical_year - No cooling during CWEC weather
        4. thermal_autonomy_extreme_year - No cooling during EWY weather

        Each scenario involves:
        - Weather file assignment (CWEC or EWY)
        - Clothing schedule creation with seasonal variations
        - Mechanical cooling control (enabled/disabled)
        - Power failure schedule creation (for outage scenarios)
        - Output variable addition for analysis
        """
        try:
            # Define scenario configurations
            scenarios = {
                "outage_typical_year": {
                    "weather_file": "CWEC",
                    "cooling_enabled": True,
                    "power_failure": True,
                    "description": "Power outage during typical weather",
                },
                "outage_extreme_year": {
                    "weather_file": "EWY",
                    "cooling_enabled": True,
                    "power_failure": True,
                    "description": "Power outage during extreme weather",
                },
                "thermal_autonomy_typical_year": {
                    "weather_file": "CWEC",
                    "cooling_enabled": False,
                    "power_failure": False,
                    "description": "No cooling during typical weather",
                },
                "thermal_autonomy_extreme_year": {
                    "weather_file": "EWY",
                    "cooling_enabled": False,
                    "power_failure": False,
                    "description": "No cooling during extreme weather",
                },
            }

            for scenario_name, config in scenarios.items():
                click.echo(f"  Creating scenario: {scenario_name} - {config['description']}")

                # Load baseline model
                scenario_model = openstudio.model.Model(self.baseline_model)

                # 1. Apply weather file
                self._apply_weather_file(scenario_model, config["weather_file"])

                # 2. Create and apply clothing schedule
                self._create_clothing_schedule(scenario_model)

                # 3. Control cooling systems
                if config["cooling_enabled"]:
                    self._ensure_cooling_enabled(scenario_model)
                else:
                    self._disable_cooling_systems(scenario_model)

                # 4. Apply power failure schedule if needed
                if config["power_failure"]:
                    self._create_power_failure_schedule(scenario_model, config["weather_file"])

                # 5. Add required output variables
                self.add_output_variables(scenario_model)

                # 6. Save scenario model
                scenario_path = os.path.join(
                    self.scenario_paths[scenario_name], f"{scenario_name}.osm"
                )
                success = scenario_model.save(scenario_path, True)
                if not success:
                    raise Exception(f"Failed to save scenario model: {scenario_path}")

                click.echo(f"    Saved scenario model: {scenario_path}")

            click.echo("All four scenarios generated successfully!")

        except Exception as e:
            raise Exception(f"Failed to generate scenarios: {str(e)}")

    def run_simulations(self):
        """
        Run EnergyPlus simulations for all scenarios.

        Executes complete simulation workflow:
        1. Converts OSM to IDF using OpenStudio ForwardTranslator
        2. Runs EnergyPlus with appropriate weather files
        3. Validates simulation outputs and logs results
        4. Checks for required output variables in results
        """
        try:
            # Include original scenario in simulation list
            all_scenarios = ["original"] + list(self.scenario_paths.keys())

            for scenario in all_scenarios:
                click.echo(f"  Running simulation: {scenario}")

                # Determine paths and weather file
                if scenario == "original":
                    scenario_folder = self.original_folder
                    osm_path = os.path.join(scenario_folder, "original.osm")
                    weather_file = self.cwec_epw_path  # Use CWEC for original
                    log_name = "original"
                else:
                    scenario_folder = self.scenario_paths[scenario]
                    osm_path = os.path.join(scenario_folder, f"{scenario}.osm")
                    # Determine weather file based on scenario
                    if "extreme" in scenario:
                        weather_file = self.ewy_epw_path
                    else:
                        weather_file = self.cwec_epw_path
                    log_name = scenario

                # Run simulation for this scenario
                success = self._run_single_simulation(
                    osm_path, scenario_folder, weather_file, log_name
                )

                if success:
                    safe_echo(f"    ✓ {scenario} simulation completed successfully")
                else:
                    click.echo(f"    ✗ {scenario} simulation failed (check log.txt)")

            click.echo("All simulations completed!")

        except Exception as e:
            raise Exception(f"Failed to run simulations: {str(e)}")

    def _run_single_simulation(self, osm_path, output_folder, weather_file, log_name):
        """
        Run a single EnergyPlus simulation.

        Args:
            osm_path (str): Path to OSM file
            output_folder (str): Output folder for results
            weather_file (str): Path to EPW weather file
            log_name (str): Name for log file

        Returns:
            bool: True if simulation succeeded, False otherwise
        """
        log_path = os.path.join(output_folder, "log.txt")

        try:
            with open(log_path, "w") as log_file:
                log_file.write(f"Resilience Simulation Log: {log_name}\n")
                log_file.write(f"Started: {datetime.now()}\n")
                log_file.write(f"OSM File: {osm_path}\n")
                log_file.write(f"Weather File: {weather_file}\n\n")

                # Step 1: Convert OSM to IDF
                log_file.write("Step 1: Converting OSM to IDF...\n")
                log_file.flush()

                # Load OpenStudio model
                optional_model = openstudio.model.Model.load(osm_path)
                if not optional_model.is_initialized():
                    log_file.write("ERROR: Could not load OSM file\n")
                    return False

                model = optional_model.get()

                # Create forward translator
                forward_translator = openstudio.energyplus.ForwardTranslator()
                workspace = forward_translator.translateModel(model)

                # Save IDF file
                idf_path = os.path.join(output_folder, "in.idf")
                success = workspace.save(idf_path, True)
                if not success:
                    log_file.write("ERROR: Could not save IDF file\n")
                    return False

                log_file.write(f"IDF saved: {idf_path}\n")

                # Step 2: Run EnergyPlus
                log_file.write("Step 2: Running EnergyPlus...\n")
                log_file.flush()

                # Copy weather file to simulation folder
                epw_path = os.path.join(output_folder, "in.epw")
                shutil.copy2(weather_file, epw_path)

                # Run EnergyPlus
                energyplus_cmd = ["energyplus", "-w", epw_path, "-d", output_folder, idf_path]

                result = subprocess.run(
                    energyplus_cmd,
                    cwd=output_folder,
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30 minute timeout
                )

                log_file.write(f"EnergyPlus return code: {result.returncode}\n")
                if result.stdout:
                    log_file.write(f"STDOUT:\n{result.stdout}\n")
                if result.stderr:
                    log_file.write(f"STDERR:\n{result.stderr}\n")

                # Step 3: Validate outputs
                log_file.write("Step 3: Validating outputs...\n")
                log_file.flush()

                # Check for eplusout.sql
                sql_path = os.path.join(output_folder, "eplusout.sql")
                if not os.path.exists(sql_path):
                    log_file.write("ERROR: eplusout.sql file not created\n")
                    return False

                safe_log_write(log_file, "✓ eplusout.sql file created\n")

                # Check for errors in eplusout.err
                err_path = os.path.join(output_folder, "eplusout.err")
                if os.path.exists(err_path):
                    with open(err_path) as err_file:
                        err_content = err_file.read()

                        # Parse the completion summary line for actual error counts
                        completion_line = None
                        for line in err_content.split("\n"):
                            if "EnergyPlus Completed" in line and "Severe Errors" in line:
                                completion_line = line
                                break

                        if completion_line:
                            # Extract severe error count from line like:
                            # "EnergyPlus Completed Successfully-- 14 Warning; 0 Severe Errors; Elapsed Time=..."
                            import re

                            severe_match = re.search(r"(\d+)\s+Severe\s+Errors?", completion_line)
                            if severe_match:
                                severe_count = int(severe_match.group(1))
                                if severe_count > 0:
                                    log_file.write(
                                        f"ERROR: {severe_count} severe errors in simulation\n"
                                    )
                                    # Also check for fatal errors in the content
                                    fatal_lines = [
                                        line
                                        for line in err_content.split("\n")
                                        if "** Fatal **" in line
                                    ]
                                    if fatal_lines:
                                        log_file.write("Fatal errors found:\n")
                                        for fatal_line in fatal_lines:
                                            log_file.write(f"  {fatal_line}\n")
                                    return False
                                else:
                                    safe_log_write(log_file, "✓ No fatal or severe errors found\n")
                            else:
                                log_file.write(
                                    "WARNING: Could not parse error summary from eplusout.err\n"
                                )
                        else:
                            # Fallback: Check for actual error markers in the content
                            actual_fatal = "** Fatal **" in err_content
                            actual_severe = "** Severe **" in err_content
                            if actual_fatal or actual_severe:
                                log_file.write(
                                    "ERROR: Fatal or severe errors found in simulation:\n"
                                )
                                error_lines = []
                                for line in err_content.split("\n"):
                                    if "** Fatal **" in line or "** Severe **" in line:
                                        error_lines.append(line)
                                for error_line in error_lines:
                                    log_file.write(f"  {error_line}\n")
                                return False
                            else:
                                safe_log_write(log_file, "✓ No fatal or severe errors found\n")

                # Step 4: Validate required output variables
                log_file.write("Step 4: Validating output variables...\n")
                log_file.flush()

                success = self._validate_output_variables(sql_path, log_file)
                if not success:
                    return False

                log_file.write(f"Completed: {datetime.now()}\n")
                log_file.write("SIMULATION SUCCESSFUL\n")
                return True

        except subprocess.TimeoutExpired:
            with open(log_path, "a") as log_file:
                log_file.write("ERROR: Simulation timed out after 30 minutes\n")
            return False
        except Exception as e:
            with open(log_path, "a") as log_file:
                log_file.write(f"ERROR: Simulation failed: {str(e)}\n")
            return False

    def _validate_output_variables(self, sql_path, log_file):
        """
        Validate that required output variables are present in simulation results.

        Args:
            sql_path (str): Path to eplusout.sql file
            log_file: Open file handle for logging

        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            import sqlite3

            # Required output variables
            required_vars = [
                "Site Outdoor Air Relative Humidity",
                "Zone Air Temperature",
                "Zone Air Relative Humidity",
                "Zone Mean Radiant Temperature",
                "Zone Operative Temperature",
                "Zone People Occupant Count",
            ]

            # Connect to SQL database
            conn = sqlite3.connect(sql_path)
            cursor = conn.cursor()

            # Query available variables
            cursor.execute(
                """
                SELECT VariableName, ReportingFrequency
                FROM ReportVariableDataDictionary
            """
            )

            available_vars = {}
            for row in cursor.fetchall():
                var_name = row[0]
                frequency = row[1]
                if var_name not in available_vars:
                    available_vars[var_name] = []
                available_vars[var_name].append(frequency)

            # Validate each required variable
            missing_vars = []
            for var in required_vars:
                if var not in available_vars:
                    missing_vars.append(var)
                    log_file.write(f"✗ Missing variable: {var}\n")
                else:
                    # Check for hourly frequency
                    if "Hourly" in available_vars[var]:
                        safe_log_write(log_file, f"✓ Found variable (Hourly): {var}\n")
                    else:
                        safe_log_write(
                            log_file,
                            f"⚠ Found variable but not hourly: {var} ({available_vars[var]})\n",
                        )

            conn.close()

            if missing_vars:
                log_file.write(f"ERROR: {len(missing_vars)} required variables missing\n")
                return False
            else:
                safe_log_write(log_file, "✓ All required output variables validated\n")
                return True

        except Exception as e:
            log_file.write(f"ERROR: Failed to validate output variables: {str(e)}\n")
            return False


def main() -> None:
    """Entry point for the h2k-resilience command."""
    resilience()


if __name__ == "__main__":
    main()
