#!/usr/bin/env python3
"""
H2K to HPXML Conversion CLI Tool

Convert H2K files to HPXML format and run OpenStudio simulations.
"""

import concurrent.futures
import os
import pathlib
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import traceback

import click
import pyfiglet
from colorama import Fore
from colorama import Style

from h2k_hpxml.config import ConfigManager
from h2k_hpxml.core.translator import h2ktohpxml
from h2k_hpxml.utils.dependencies import DependencyManager
from h2k_hpxml.utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def get_openstudio_binary_path() -> str:
    """Get the OpenStudio binary path for the current platform."""
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


# Constants
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_ENCODING = "utf-8"
SIMULATION_PAUSE_SECONDS = 3
OUTPUT_FOLDER_NAME = "output"


def _build_simulation_flags(
    add_component_loads,
    debug,
    skip_validation,
    output_format,
    timestep,
    daily,
    hourly,
    monthly,
    add_stochastic_schedules,
    add_timeseries_output_variable,
):
    """
    Build simulation flags string for OpenStudio command.

    Args:
        add_component_loads (bool): Add component loads flag
        debug (bool): Debug mode flag
        skip_validation (bool): Skip validation flag
        output_format (str): Output format option
        timestep (tuple): Timestep output options
        daily (tuple): Daily output options
        hourly (tuple): Hourly output options
        monthly (tuple): Monthly output options
        add_stochastic_schedules (bool): Stochastic schedules flag
        add_timeseries_output_variable (tuple): Timeseries variables

    Returns:
        str: Formatted flags string for simulation command
    """
    flag_options = {
        "--add-component-loads": add_component_loads,
        "--debug": debug,
        "--skip-validation": skip_validation,
        "--output-format": output_format,
    }
    flags = " ".join(
        f"{key} {value}" if value else key for key, value in flag_options.items() if value
    )

    # Add options that can be repeated
    repeated_options = [
        ("--timestep", timestep),
        ("--hourly", hourly),
        ("--monthly", monthly),
        ("--daily", daily),
    ]
    for option, values in repeated_options:
        flags += " " + " ".join(f"{option} {v}" for v in values)

    if add_stochastic_schedules:
        flags += " --add-stochastic-schedules"
    if add_timeseries_output_variable:
        flags += " " + " ".join(
            f"--add-timeseries-output-variable {v}" for v in add_timeseries_output_variable
        )

    return flags


def _detect_xml_encoding(filepath):
    """
    Detect XML encoding from file header.

    Args:
        filepath (str): Path to XML file

    Returns:
        str: Detected encoding or 'utf-8' as fallback
    """
    with open(filepath, "rb") as f:
        first_line = f.readline()
        match = re.search(rb'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
        if match:
            return match.group(1).decode("ascii")
    return DEFAULT_ENCODING  # fallback


def _convert_h2k_to_hpxml(filepath, dest_hpxml_path):
    """
    Convert H2K file to HPXML format.

    Args:
        filepath (str): Path to H2K file
        dest_hpxml_path (str): Destination directory for HPXML files

    Returns:
        str: Path to created HPXML file

    Raises:
        Exception: If conversion fails
    """
    logger.info(f"Processing file: {filepath}")

    # Detect encoding from XML declaration
    encoding = _detect_xml_encoding(filepath)
    logger.info(f"Detected encoding for {filepath}: {encoding}")

    # Read the content of the H2K file with detected encoding
    with open(filepath, encoding=encoding) as f:
        h2k_string = f.read()

    # Convert the H2K content to HPXML format
    hpxml_string = h2ktohpxml(h2k_string)

    # Define the output path for the converted HPXML file
    file_stem = pathlib.Path(filepath).stem
    hpxml_path = os.path.join(dest_hpxml_path, file_stem, f"{file_stem}.xml")

    # If the destination path exists, delete the folder
    if os.path.exists(hpxml_path):
        shutil.rmtree(os.path.dirname(hpxml_path))
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(hpxml_path), exist_ok=True)

    logger.info(f"Saving converted file to: {hpxml_path}")

    # Write the converted HPXML content to the output file
    with open(hpxml_path, "w") as f:
        f.write(hpxml_string)

    return hpxml_path


def _run_simulation(hpxml_path, ruby_hpxml_path, hpxml_os_path, flags):
    """
    Run OpenStudio simulation on HPXML file.

    Args:
        hpxml_path (str): Path to HPXML file
        ruby_hpxml_path (str): Path to Ruby simulation script
        hpxml_os_path (str): OpenStudio HPXML path
        flags (str): Simulation flags

    Returns:
        tuple: (success_status, error_message)
    """
    # Run the OpenStudio simulation
    openstudio_binary = get_openstudio_binary_path()
    command = [openstudio_binary, ruby_hpxml_path, "-x", os.path.abspath(hpxml_path)]

    # Convert flags to a list of strings
    flags_list = flags.split()
    command.extend(flags_list)

    try:
        logger.info(f"Running simulation for file: {hpxml_path}")
        result = subprocess.run(
            command, cwd=hpxml_os_path, check=True, capture_output=True, text=True
        )
        logger.info(f"Simulation result: {result}")
        return "Success", ""
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during simulation: {e.stderr}")
        return "Failure", e.stderr


def _handle_processing_error(filepath, dest_hpxml_path, error, traceback_str):
    """
    Handle errors during file processing by saving error information.

    Args:
        filepath (str): Path to file that failed
        dest_hpxml_path (str): Destination directory
        error (Exception): The error that occurred
        traceback_str (str): Formatted traceback string

    Returns:
        str: Error message for reporting
    """
    # Save traceback to a separate error.txt file
    error_dir = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem)
    os.makedirs(error_dir, exist_ok=True)
    error_file_path = os.path.join(error_dir, "error.txt")
    with open(error_file_path, "w") as error_file:
        error_file.write(f"{str(error)}\n{traceback_str}")

    # Check for specific exception text and handle run.log
    if "returned non-zero exit status 1." in str(error):
        run_log_path = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem, "run", "run.log")
        if os.path.exists(run_log_path):
            with open(run_log_path) as run_log_file:
                run_log_content = "**OS-HPXML ERROR**: " + run_log_file.read()
                return run_log_content

    # Default behavior for other exceptions
    return str(error)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version="1.7.0.1.1")
def cli():
    """H2K to HPXML conversion and simulation tool."""
    pass


@cli.command(help="People that worked on this.")
def credits():
    """Display credits for the H2K to HPXML team."""
    print(Fore.GREEN + "H2K to HPXML Team" + Style.RESET_ALL)
    colors = [Fore.RED, Fore.GREEN, Fore.MAGENTA, Fore.CYAN, Fore.YELLOW, Fore.BLUE]

    for name in [
        "Aidan Brookson\n",
        "Leigh St. Hilaire\n",
        "Chris Kirney\n",
        "Phylroy Lopex\n",
        "Julia Purdy\n",
    ]:
        print(random.choice(colors) + pyfiglet.figlet_format(name) + Fore.RESET)


@cli.command(help="Convert and Simulate H2K file to OS/E+.")
@click.option(
    "--input_path",
    "-i",
    default=os.path.join("/shared"),
    help="h2k file or folder containing h2k files.",
)
@click.option(
    "--output_path",
    "-o",
    help=(
        "Path to output hpxml files. By default it is the same as the "
        "input path with a folder named output created inside it."
    ),
)
@click.option(
    "--timestep",
    multiple=True,
    default=[],
    help=(
        "Request timestep output type (ALL, total, fuels, enduses, "
        "systemuses, emissions, emissionfuels, emissionenduses, hotwater, "
        "loads, componentloads, unmethours, temperatures, airflows, "
        "weather, resilience); can be called multiple times"
    ),
)
@click.option(
    "--daily",
    multiple=True,
    default=[],
    help=(
        "Request daily output type (ALL, total, fuels, enduses, "
        "systemuses, emissions, emissionfuels, emissionenduses, hotwater, "
        "loads, componentloads, unmethours, temperatures, airflows, "
        "weather, resilience); can be called multiple times"
    ),
)
@click.option(
    "--hourly",
    multiple=True,
    default=[],
    help=(
        "Request hourly output type (ALL, total, fuels, enduses, "
        "systemuses, emissions, emissionfuels, emissionenduses, hotwater, "
        "loads, componentloads, unmethours, temperatures, airflows, "
        "weather, resilience); can be called multiple times"
    ),
)
@click.option(
    "--monthly",
    multiple=True,
    default=[],
    help=(
        "Request monthly output type (ALL, total, fuels, enduses, "
        "systemuses, emissions, emissionfuels, emissionenduses, hotwater, "
        "loads, componentloads, unmethours, temperatures, airflows, "
        "weather, resilience); can be called multiple times"
    ),
)
@click.option(
    "--add-component-loads", "-l", is_flag=True, default=True, help="Add component loads."
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    help="Enable debug mode and all extra file outputs.",
)
@click.option(
    "--skip-validation",
    "-s",
    is_flag=True,
    default=False,
    help="Skip Schema/Schematron validation for faster performance",
)
@click.option(
    "--output-format",
    "-f",
    default="csv",
    help=("Output format for the simulation results " "(csv, json, msgpack, csv_dview)"),
)
@click.option(
    "--add-stochastic-schedules",
    is_flag=True,
    default=False,
    help="Add detailed stochastic occupancy schedules",
)
@click.option(
    "--add-timeseries-output-variable",
    multiple=True,
    default=[],
    help="Add timeseries output variable; can be called multiple times",
)
@click.option(
    "--do-not-sim", is_flag=True, default=False, help="Convert only, do not run simulation"
)
def run(
    input_path,
    output_path,
    timestep,
    daily,
    hourly,
    monthly,
    add_component_loads,
    debug,
    skip_validation,
    output_format,
    add_stochastic_schedules,
    add_timeseries_output_variable,
    do_not_sim,
):
    """
    Convert H2K files to HPXML format and optionally run OpenStudio simulations.

    This function processes single H2K files or directories containing multiple
    H2K files. It converts them to HPXML format using the h2ktohpxml translator,
    then optionally runs OpenStudio simulations with configurable output options.

    Processing is done concurrently using ThreadPoolExecutor for improved
    performance. Results and errors are logged to markdown files for review.

    Args:
        input_path (str): Path to H2K file or directory containing H2K files
        output_path (str): Path to output HPXML files. If None, creates 'output'
            folder in same directory as input
        timestep (tuple): Timestep output types to request from simulation
        daily (tuple): Daily output types to request from simulation
        hourly (tuple): Hourly output types to request from simulation
        monthly (tuple): Monthly output types to request from simulation
        add_component_loads (bool): Whether to add component loads to simulation
        debug (bool): Enable debug mode with extra file outputs
        skip_validation (bool): Skip Schema/Schematron validation for speed
        output_format (str): Result format - 'csv', 'json', 'msgpack', 'csv_dview'
        add_stochastic_schedules (bool): Add detailed stochastic occupancy schedules
        add_timeseries_output_variable (tuple): Additional timeseries output variables
        do_not_sim (bool): If True, only convert to HPXML without running simulation

    Raises:
        ValueError: If multiple output frequency options are provided simultaneously
        SystemExit: If no H2K files found or invalid input path provided

    Notes:
        - Only one of hourly, monthly, or timestep output options can be used
        - Requires OpenStudio to be installed for simulations
        - Configuration read from conversionconfig.ini file
        - Results written to processing_results.md in output directory
    """

    # Ensure only one of hourly, monthly or timeseries options is provided
    if sum(bool(x) for x in [hourly, monthly, timestep]) > 1:
        raise ValueError(
            "Only one of the options --hourly, --monthly, or --timestep "
            "can be provided at a time."
        )

    # Build simulation flags
    flags = _build_simulation_flags(
        add_component_loads,
        debug,
        skip_validation,
        output_format,
        timestep,
        daily,
        hourly,
        monthly,
        add_stochastic_schedules,
        add_timeseries_output_variable,
    )

    # Load configuration using ConfigManager
    config_manager = ConfigManager()
    hpxml_os_path = str(config_manager.hpxml_os_path)
    ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

    # Get source and destination paths
    source_h2k_path = input_path
    if output_path:
        dest_hpxml_path = output_path
    else:
        # Default to creating an output folder in the same directory as the input
        if os.path.isfile(input_path):
            dest_hpxml_path = os.path.join(os.path.dirname(input_path), OUTPUT_FOLDER_NAME)
        else:
            dest_hpxml_path = os.path.join(input_path, OUTPUT_FOLDER_NAME)

    # Create the destination folder
    os.makedirs(dest_hpxml_path, exist_ok=True)

    # Determine if the source path is a single file or directory of files
    if os.path.isfile(source_h2k_path) and source_h2k_path.lower().endswith(".h2k"):
        h2k_files = [source_h2k_path]
    elif os.path.isdir(source_h2k_path):
        h2k_files = [
            os.path.join(source_h2k_path, f)
            for f in os.listdir(source_h2k_path)
            if f.lower().endswith(".h2k")
        ]
        if not h2k_files:
            print(f"No .h2k files found in directory {source_h2k_path}.")
            sys.exit(1)
    else:
        print(f"The source path {source_h2k_path} is neither a .h2k file " f"nor a directory.")
        sys.exit(1)

    def process_file(filepath):
        """Process a single H2K file to HPXML and optionally simulate."""
        try:
            print("=" * 48)
            # Convert H2K to HPXML
            hpxml_path = _convert_h2k_to_hpxml(filepath, dest_hpxml_path)

            if not do_not_sim:
                # Pause briefly before simulation
                time.sleep(SIMULATION_PAUSE_SECONDS)

                # Run simulation
                status, error_msg = _run_simulation(
                    hpxml_path, ruby_hpxml_path, hpxml_os_path, flags
                )

                if status == "Success":
                    return (filepath, "Success", "")
                else:
                    # Handle simulation error
                    tb = traceback.format_exc()
                    error_details = _handle_processing_error(
                        filepath,
                        dest_hpxml_path,
                        subprocess.CalledProcessError(1, "simulation", error_msg),
                        tb,
                    )
                    return (filepath, "Failure", error_details)
            else:
                return (filepath, "Success", "")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during processing: {tb}")

            # Handle processing error
            error_details = _handle_processing_error(filepath, dest_hpxml_path, e, tb)
            return (filepath, "Failure", error_details)

    # Use ThreadPoolExecutor to process files concurrently with a limited number of threads
    max_workers = max(1, os.cpu_count() - 1)
    logger.info(f"Processing files with {max_workers} threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, h2k_files))

    # Filter results for failures only
    failure_results = [result for result in results if result[1] == "Failure"]

    # Write failure results to a Markdown file
    markdown_path = os.path.join(dest_hpxml_path, "processing_results.md")
    with open(markdown_path, "w") as mdfile:
        mdfile.write("| Filepath | Status | Error |\n")
        mdfile.write("|----------|--------|-------|\n")
        for result in failure_results:
            mdfile.write(f"| {result[0]} | {result[1]} | {result[2]} |\n")


def _find_project_root():
    """
    Find the project root directory containing conversionconfig.ini.

    Searches upward from the current file location through parent directories
    until it finds a directory containing the required configuration file.

    Returns:
        str: Path to project root directory containing conversionconfig.ini,
             or current working directory as fallback
    """
    current_dir = pathlib.Path(__file__).parent
    for parent in [current_dir] + list(current_dir.parents):
        config_file = parent / "conversionconfig.ini"
        if config_file.exists():
            return str(parent)
    # Fallback to current working directory
    return os.getcwd()


def main():
    """Entry point for the h2k2hpxml command."""
    cli()


if __name__ == "__main__":
    main()
