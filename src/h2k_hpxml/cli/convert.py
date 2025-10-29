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
import subprocess
import sys
import time
import traceback
from datetime import datetime

import click
import pyfiglet
from colorama import Fore
from colorama import Style

from h2k_hpxml.api import _build_simulation_flags
from h2k_hpxml.api import _convert_h2k_file_to_hpxml
from h2k_hpxml.api import _handle_conversion_error
from h2k_hpxml.api import _run_hpxml_simulation
from h2k_hpxml.config import ConfigManager
from h2k_hpxml.utils.dependencies import DependencyManager
from h2k_hpxml.utils.logging import get_logger
from h2k_hpxml.utils.results_database import ResultsDatabase

# Get logger for this module
logger = get_logger(__name__)


def get_openstudio_binary_path() -> str:
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


# Constants
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_ENCODING = "utf-8"
SIMULATION_PAUSE_SECONDS = 3
OUTPUT_FOLDER_NAME = "output"


def show_credits():
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


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="h2k-hpxml")
@click.argument("input", required=False, type=click.Path())
@click.option(
    "--output",
    "-o",
    help=(
        "Path to output hpxml files. By default it is the same as the "
        "input path with a folder named output created inside it."
    ),
)
@click.option("--credits", is_flag=True, help="Show credits for the H2K to HPXML team.")
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
    help=("Output format for the simulation results (csv, json, msgpack, csv_dview)"),
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
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    default=False,
    help="Recursively search subdirectories for .h2k files",
)
@click.option("--demo", is_flag=True, help="Run interactive demo / Exécuter la démo interactive")
def cli(
    input,
    output,
    credits,
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
    recursive,
    demo,
):
    """
    H2K to HPXML conversion and simulation tool.

    INPUT: H2K file or directory containing H2K files to process

    Convert H2K files to HPXML format and optionally run OpenStudio simulations.
    This tool can process single files or entire directories of H2K files.
    Use --recursive to search subdirectories for .h2k files.

    Examples:
        h2k-hpxml input.h2k
        h2k-hpxml /path/to/h2k/files/
        h2k-hpxml /path/to/h2k/files/ --recursive
        h2k-hpxml input.h2k --output output.xml --debug
        h2k-hpxml --credits
    """

    # Prevent auto-install when running h2k-hpxml CLI
    os.environ["H2K_SKIP_AUTO_INSTALL"] = "1"

    # Check dependencies and provide helpful message if missing
    if not credits and not demo:  # Skip dependency check for credits and demo
        dep_manager = DependencyManager()
        if not dep_manager.check_only():
            click.echo("❌ Missing required dependencies!")
            click.echo("Run 'os-setup --install-quiet' to install them.")
            sys.exit(1)

    # Handle credits flag
    if credits:
        show_credits()
        return

    # Handle demo flag
    if demo:
        from .demo import run_interactive_demo

        run_interactive_demo()
        return

    # Show help if no input provided
    if not input:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return

    # Use input as input_path and output as output_path for compatibility with existing code
    input_path = input
    output_path = output

    # Ensure only one of hourly, monthly or timeseries options is provided
    if sum(bool(x) for x in [hourly, monthly, timestep]) > 1:
        raise ValueError(
            "Only one of the options --hourly, --monthly, or --timestep can be provided at a time."
        )

    # Build simulation flags using API function
    flags = _build_simulation_flags(
        add_component_loads=add_component_loads,
        debug=debug,
        skip_validation=skip_validation,
        output_format=output_format,
        timestep=timestep,
        daily=daily,
        hourly=hourly,
        monthly=monthly,
        add_stochastic_schedules=add_stochastic_schedules,
        add_timeseries_output_variable=add_timeseries_output_variable,
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

    # Initialize results database
    db_path = os.path.join(dest_hpxml_path, "processing_results.db")
    results_db = ResultsDatabase(db_path)
    logger.info(f"Initialized results database at: {db_path}")

    # Determine if the source path is a single file or directory of files
    if os.path.isfile(source_h2k_path) and source_h2k_path.lower().endswith(".h2k"):
        h2k_files = [source_h2k_path]
    elif os.path.isdir(source_h2k_path):
        if recursive:
            # Recursively search subdirectories for .h2k files
            source_path = pathlib.Path(source_h2k_path)
            h2k_files = [
                str(f) for f in source_path.rglob("*.[hH]2[kK]")
            ]
        else:
            # Only search top-level directory
            h2k_files = [
                os.path.join(source_h2k_path, f)
                for f in os.listdir(source_h2k_path)
                if f.lower().endswith(".h2k")
            ]
        if not h2k_files:
            search_type = "recursively" if recursive else ""
            print(f"No .h2k files found {search_type} in directory {source_h2k_path}.")
            sys.exit(1)
    else:
        print(f"The source path {source_h2k_path} is neither a .h2k file nor a directory.")
        sys.exit(1)

    # Determine output mode based on file count
    batch_mode = len(h2k_files) > 1
    if batch_mode:
        # Suppress verbose logging for batch processing
        import logging
        logging.getLogger('h2k_hpxml').setLevel(logging.WARNING)
        logger.info(f"Batch mode enabled: Processing {len(h2k_files)} files with progress bar")

    def categorize_error_for_display(error_message: str) -> str:
        """Extract brief error category for display in progress output."""
        if not error_message:
            return "Unknown error"

        if "must be greater than '0'" in error_message or "must be greater than 0" in error_message:
            if "Area" in error_message:
                return "Area validation"
            if "AssemblyEffectiveRValue" in error_message:
                return "R-value validation"
            if "EnergyFactor" in error_message:
                return "Energy factor validation"
            if "TankVolume" in error_message:
                return "Tank volume validation"
            if "SensibleRecoveryEfficiency" in error_message:
                return "Ventilation efficiency"
            return "Value validation"

        if "Switchover temperature" in error_message:
            return "Heat pump config"
        if "ERV/HRV" in error_message:
            return "Ventilation effectiveness"
        if "Multiple heating systems" in error_message:
            return "HVAC config"
        if "location is specified" in error_message and "but no surfaces" in error_message:
            return "Location mismatch"
        if "floor or slab adjacent to conditioned space" in error_message:
            return "Missing floor/slab"
        if "UsedForWholeBuildingVentilation" in error_message:
            return "Ventilation config"
        if "weather" in error_message.lower():
            return "Weather file"

        return "Translation error"

    def process_file(filepath):
        """Process a single H2K file to HPXML and optionally simulate."""
        start_time = datetime.now()
        hpxml_path = None

        try:
            # Only print separator in verbose (single-file) mode
            if not batch_mode:
                print("=" * 48)
            # Convert H2K to HPXML using API function
            hpxml_path = _convert_h2k_file_to_hpxml(filepath, dest_hpxml_path)

            if not do_not_sim:
                # Pause briefly before simulation
                time.sleep(SIMULATION_PAUSE_SECONDS)

                # Run simulation using API function
                status, error_msg = _run_hpxml_simulation(
                    hpxml_path=hpxml_path,
                    ruby_hpxml_path=ruby_hpxml_path,
                    hpxml_os_path=hpxml_os_path,
                    flags=flags,
                )

                if status == "Success":
                    # Record success to database
                    results_db.record_success(
                        filepath=filepath,
                        hpxml_output_path=hpxml_path,
                        start_time=start_time
                    )
                    return (filepath, "Success", "")
                else:
                    # Handle simulation error using API function
                    tb = traceback.format_exc()
                    error_details = _handle_conversion_error(
                        filepath=filepath,
                        dest_hpxml_path=dest_hpxml_path,
                        error=subprocess.CalledProcessError(1, "simulation", error_msg),
                        traceback_str=tb,
                    )
                    # Record failure to database
                    results_db.record_failure(
                        filepath=filepath,
                        error_message=error_details,
                        start_time=start_time
                    )
                    return (filepath, "Failure", error_details)
            else:
                # Conversion-only mode (no simulation)
                results_db.record_success(
                    filepath=filepath,
                    hpxml_output_path=hpxml_path,
                    start_time=start_time
                )
                return (filepath, "Success", "")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during processing: {tb}")

            # Handle processing error using API function
            error_details = _handle_conversion_error(
                filepath=filepath, dest_hpxml_path=dest_hpxml_path, error=e, traceback_str=tb
            )
            # Record failure to database
            results_db.record_failure(
                filepath=filepath,
                error_message=error_details,
                start_time=start_time
            )
            return (filepath, "Failure", error_details)

    # Use ThreadPoolExecutor to process files concurrently with a limited number of threads
    max_workers = max(1, os.cpu_count() - 1)
    logger.info(f"Processing files with {max_workers} threads...")

    if batch_mode:
        # Use tqdm progress bar for batch processing
        from tqdm import tqdm

        with tqdm(
            total=len(h2k_files),
            desc="Processing H2K files",
            unit="file",
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        ) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(process_file, f): f for f in h2k_files}
                results = []
                failures = 0

                for future in concurrent.futures.as_completed(future_to_file):
                    result = future.result()
                    results.append(result)

                    if result[1] == "Failure":
                        failures += 1
                        # Show failure notification above progress bar
                        filepath, status, error = result
                        error_type = categorize_error_for_display(error)
                        filename = pathlib.Path(filepath).name
                        tqdm.write(f"❌ Failed: {filename} ({error_type})")

                    # Update progress bar with failure count
                    pbar.set_postfix({'failures': failures}, refresh=False)
                    pbar.update(1)
    else:
        # Single file - use current verbose output
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

    # Print summary from database
    summary = results_db.get_summary()
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {summary['total']}")
    print(f"Successes: {summary['successes']} ({summary['success_rate']:.1f}%)")
    print(f"Failures: {summary['failures']} ({100 - summary['success_rate']:.1f}%)")

    if summary['error_categories']:
        print("\nTop Error Categories:")
        for category, count in summary['error_categories']:
            print(f"  - {category}: {count}")

    if summary['top_error_types']:
        print("\nTop 10 Error Types:")
        for error_type, count in summary['top_error_types'][:10]:
            print(f"  - {error_type}: {count}")

    print(f"\nResults saved to:")
    print(f"  - Database: {db_path}")
    print(f"  - Markdown: {markdown_path}")
    print("=" * 80)

    # Close database connection
    results_db.close()


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


def main() -> None:
    """Entry point for the h2k-hpxml command."""
    cli()


if __name__ == "__main__":
    main()
