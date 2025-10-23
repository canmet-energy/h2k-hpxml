"""
High-level API for H2K to HPXML conversion.

This module provides a clean, user-friendly interface for the most common
use cases while hiding internal implementation details.
"""

import concurrent.futures
import os
import pathlib
import re
import shutil
import subprocess
import time
import traceback
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .config.manager import ConfigManager
from .core.translator import h2ktohpxml as _h2ktohpxml
from .utils.dependencies import get_openstudio_path
from .utils.dependencies import validate_dependencies as _validate_dependencies
from .utils.logging import get_logger

# Public API exports
__all__ = [
    "convert_h2k_string",
    "convert_h2k_file",
    "run_full_workflow",
    "batch_convert_h2k_files",
    "validate_dependencies",
]

# Constants
DEFAULT_ENCODING = "utf-8"

logger = get_logger(__name__)


# ============================================================================
# Helper Functions (Moved from CLI)
# ============================================================================


def _build_simulation_flags(
    add_component_loads: bool = True,
    debug: bool = False,
    skip_validation: bool = False,
    output_format: str = "csv",
    timestep: tuple = (),
    daily: tuple = (),
    hourly: tuple = (),
    monthly: tuple = (),
    add_stochastic_schedules: bool = False,
    add_timeseries_output_variable: tuple = (),
) -> str:
    """
    Build simulation flags string for OpenStudio command (internal).

    This is an internal helper function used by CLI and batch processing.
    For public API usage, use run_full_workflow() or batch_convert_h2k_files().

    Args:
        add_component_loads: Add component loads flag
        debug: Debug mode flag
        skip_validation: Skip validation flag
        output_format: Output format option
        timestep: Timestep output options
        daily: Daily output options
        hourly: Hourly output options
        monthly: Monthly output options
        add_stochastic_schedules: Stochastic schedules flag
        add_timeseries_output_variable: Timeseries variables

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
        # Safety check: ensure values is iterable and not None
        if values is None:
            continue
        # Convert single values or non-iterables to tuples
        if not hasattr(values, "__iter__") or isinstance(values, str):
            values = (values,) if values else ()
        # Only add flags if values is not empty
        if values:
            flags += " " + " ".join(f"{option} {v}" for v in values)

    if add_stochastic_schedules:
        flags += " --add-stochastic-schedules"

    # Safety check for add_timeseries_output_variable
    if add_timeseries_output_variable:
        # Ensure it's iterable and not None
        if not hasattr(add_timeseries_output_variable, "__iter__") or isinstance(
            add_timeseries_output_variable, str
        ):
            add_timeseries_output_variable = (add_timeseries_output_variable,)
        flags += " " + " ".join(
            f"--add-timeseries-output-variable {v}" for v in add_timeseries_output_variable
        )

    return flags


def _run_hpxml_simulation(
    hpxml_path: str, ruby_hpxml_path: str, hpxml_os_path: str, flags: str
) -> Tuple[str, str]:
    """
    Run OpenStudio simulation on HPXML file (internal).

    This is an internal helper function used by CLI and batch processing.
    For public API usage, use run_full_workflow() or batch_convert_h2k_files().

    Args:
        hpxml_path: Path to HPXML file
        ruby_hpxml_path: Path to Ruby simulation script
        hpxml_os_path: OpenStudio HPXML path
        flags: Simulation flags string

    Returns:
        Tuple of (success_status, error_message)
            - success_status: "Success" or "Failure"
            - error_message: Error details if failed, empty string if successful
    """
    # Get OpenStudio binary path
    openstudio_binary = get_openstudio_path()
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


def _handle_conversion_error(
    filepath: str, dest_hpxml_path: str, error: Exception, traceback_str: str
) -> str:
    """
    Handle errors during file processing by saving error information (internal).

    This is an internal helper function used by CLI and batch processing.
    For public API usage, use run_full_workflow() or batch_convert_h2k_files().

    Args:
        filepath: Path to file that failed
        dest_hpxml_path: Destination directory
        error: The error that occurred
        traceback_str: Formatted traceback string

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


def _detect_xml_encoding(filepath: str) -> str:
    """
    Detect XML encoding from file header.

    Args:
        filepath: Path to XML file

    Returns:
        str: Detected encoding or 'utf-8' as fallback
    """
    with open(filepath, "rb") as f:
        first_line = f.readline()
        match = re.search(rb'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
        if match:
            return match.group(1).decode("ascii")
    return DEFAULT_ENCODING  # fallback


def _convert_h2k_file_to_hpxml(filepath: str, dest_hpxml_path: str) -> str:
    """
    Convert H2K file to HPXML format and save to destination directory (internal).

    This is an internal helper function used by CLI, demo, and batch processing.
    It creates a subdirectory structure for each converted file.

    For public API usage, use convert_h2k_file() instead.

    Args:
        filepath: Path to H2K file
        dest_hpxml_path: Destination directory for HPXML files

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
    hpxml_string = _h2ktohpxml(h2k_string)

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


# ============================================================================
# Public API Functions
# ============================================================================


def convert_h2k_string(h2k_string: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Convert H2K XML string to HPXML format.

    This is the core conversion function that takes H2K data as a string
    and returns HPXML data as a string.

    Args:
        h2k_string: H2K file content as XML string
        config: Optional configuration dictionary for translation options.
               If None, uses default configuration from conversionconfig.ini

    Returns:
        str: HPXML formatted string

    Raises:
        H2KParsingError: If H2K input cannot be parsed
        HPXMLGenerationError: If HPXML generation fails
        ConfigurationError: If configuration is invalid

    Example:
        >>> with open('house.h2k', 'r') as f:
        ...     h2k_content = f.read()
        >>> hpxml_result = convert_h2k_string(h2k_content)
    """
    return _h2ktohpxml(h2k_string, config)


def convert_h2k_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Convert H2K file to HPXML format.

    Convenience function that handles file I/O for H2K to HPXML conversion.

    Args:
        input_path: Path to input H2K file
        output_path: Path for output HPXML file. If None, uses input filename
                    with .xml extension in same directory
        config: Optional configuration dictionary for translation options

    Returns:
        str: Path to the created HPXML file

    Raises:
        FileNotFoundError: If input file doesn't exist
        PermissionError: If output location is not writable
        H2KParsingError: If H2K input cannot be parsed
        HPXMLGenerationError: If HPXML generation fails

    Example:
        >>> output_file = convert_h2k_file('house.h2k', 'house.xml')
        >>> print(f"Conversion complete: {output_file}")
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix(".xml")
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read H2K file
    try:
        with open(input_path, encoding="utf-8") as f:
            h2k_content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings if UTF-8 fails
        with open(input_path, encoding="iso-8859-1") as f:
            h2k_content = f.read()

    # Convert to HPXML
    hpxml_content = convert_h2k_string(h2k_content, config)

    # Write HPXML file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(hpxml_content)

    return str(output_path)


def run_full_workflow(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    simulate: bool = True,
    output_format: str = "csv",
    add_component_loads: bool = True,
    debug: bool = False,
    skip_validation: bool = False,
    add_stochastic_schedules: bool = False,
    add_timeseries_output_variable: Optional[List[str]] = None,
    hourly_outputs: Optional[List[str]] = None,
    daily_outputs: Optional[List[str]] = None,
    monthly_outputs: Optional[List[str]] = None,
    timestep_outputs: Optional[List[str]] = None,
    max_workers: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Run the complete H2K to HPXML conversion and simulation workflow.

    This function replicates the functionality of the CLI 'run' command,
    providing the full conversion and simulation pipeline programmatically.

    Args:
        input_path: Path to input H2K file or directory containing H2K files
        output_path: Path for output files. If None, creates 'output' folder
                    in same directory as input
        simulate: Whether to run EnergyPlus simulation after conversion
        output_format: Output format for results ("csv", "json", "msgpack")
        add_component_loads: Whether to include component loads in output
        debug: Enable debug mode with extra outputs
        skip_validation: Skip Schema/Schematron validation for speed
        add_stochastic_schedules: Add detailed stochastic occupancy schedules
        add_timeseries_output_variable: Additional timeseries output variables
        hourly_outputs: List of hourly output categories (e.g., ['total', 'fuels'])
        daily_outputs: List of daily output categories (e.g., ['total', 'fuels'])
        monthly_outputs: List of monthly output categories (e.g., ['total', 'fuels'])
        timestep_outputs: List of timestep output categories (e.g., ['total', 'fuels'])
        max_workers: Number of concurrent workers (default: CPU count - 1)
        **kwargs: Additional options passed to the workflow

    Returns:
        Dict containing workflow results:
        - 'converted_files': List of HPXML files created
        - 'successful_conversions': Number of successful conversions
        - 'failed_conversions': Number of failed conversions
        - 'simulation_results': Simulation output paths (if simulate=True)
        - 'errors': List of errors encountered during processing
        - 'results_file': Path to markdown results file

    Raises:
        FileNotFoundError: If input path doesn't exist
        DependencyError: If required dependencies are missing
        SimulationError: If simulation fails (when simulate=True)

    Example:
        >>> results = run_full_workflow(
        ...     'house.h2k',
        ...     simulate=True,
        ...     output_format='csv',
        ...     hourly_outputs=['total', 'fuels']  # Request hourly total and fuel outputs
        ... )
        >>> print(f"Converted: {results['successful_conversions']} files")
    """
    logger = get_logger(__name__)

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    # Set defaults for optional parameters
    if add_timeseries_output_variable is None:
        add_timeseries_output_variable = []
    if hourly_outputs is None:
        hourly_outputs = []
    if daily_outputs is None:
        daily_outputs = []
    if monthly_outputs is None:
        monthly_outputs = []
    if timestep_outputs is None:
        timestep_outputs = []

    # Build simulation flags
    flags = _build_simulation_flags(
        add_component_loads=add_component_loads,
        debug=debug,
        skip_validation=skip_validation,
        output_format=output_format,
        timestep=tuple(timestep_outputs),
        daily=tuple(daily_outputs),
        hourly=tuple(hourly_outputs),
        monthly=tuple(monthly_outputs),
        add_stochastic_schedules=add_stochastic_schedules,
        add_timeseries_output_variable=tuple(add_timeseries_output_variable),
    )

    # Load configuration
    config_manager = ConfigManager()
    hpxml_os_path = str(config_manager.hpxml_os_path)
    ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

    # Determine output path
    if output_path:
        dest_hpxml_path = str(output_path)
    else:
        # Default to creating an output folder in the same directory as input
        if input_path.is_file():
            dest_hpxml_path = os.path.join(input_path.parent, "output")
        else:
            dest_hpxml_path = os.path.join(input_path, "output")

    # Create destination folder
    os.makedirs(dest_hpxml_path, exist_ok=True)

    # Find H2K files
    if input_path.is_file() and input_path.suffix.lower() == ".h2k":
        h2k_files = [str(input_path)]
    elif input_path.is_dir():
        h2k_files = [str(f) for f in input_path.glob("*.h2k") if f.suffix.lower() == ".h2k"]
        if not h2k_files:
            raise FileNotFoundError(f"No .h2k files found in directory {input_path}")
    else:
        raise ValueError(f"Input path must be a .h2k file or directory: {input_path}")

    def process_file(filepath: str) -> Tuple[str, str, str]:
        """Process a single H2K file to HPXML and optionally simulate."""
        try:
            # Convert H2K to HPXML
            hpxml_path = _convert_h2k_file_to_hpxml(filepath, dest_hpxml_path)

            if simulate:
                # Brief pause before simulation
                time.sleep(3)

                # Run simulation
                status, error_msg = _run_hpxml_simulation(
                    hpxml_path, ruby_hpxml_path, hpxml_os_path, flags
                )

                if status == "Success":
                    return (filepath, "Success", "")
                else:
                    # Handle simulation error
                    tb = traceback.format_exc()
                    error_details = _handle_conversion_error(
                        filepath,
                        dest_hpxml_path,
                        Exception(error_msg),
                        tb,
                    )
                    return (filepath, "Failure", error_details)
            else:
                return (filepath, "Success", "")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during processing {filepath}: {tb}")

            error_details = _handle_conversion_error(filepath, dest_hpxml_path, e, tb)
            return (filepath, "Failure", error_details)

    # Process files concurrently
    if max_workers is None:
        max_workers = max(1, os.cpu_count() - 1)

    logger.info(f"Processing {len(h2k_files)} files with {max_workers} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, h2k_files))

    # Analyze results
    successful_results = [r for r in results if r[1] == "Success"]
    failed_results = [r for r in results if r[1] == "Failure"]

    # Write results to markdown file
    results_file = os.path.join(dest_hpxml_path, "processing_results.md")
    with open(results_file, "w") as mdfile:
        mdfile.write("# H2K to HPXML Processing Results\n\n")
        mdfile.write(f"**Total Files**: {len(h2k_files)}\n")
        mdfile.write(f"**Successful**: {len(successful_results)}\n")
        mdfile.write(f"**Failed**: {len(failed_results)}\n\n")

        if failed_results:
            mdfile.write("## Failed Conversions\n\n")
            mdfile.write("| Filepath | Status | Error |\n")
            mdfile.write("|----------|--------|-------|\n")
            for result in failed_results:
                mdfile.write(f"| {result[0]} | {result[1]} | {result[2]} |\n")

    # Build return data
    converted_files = [
        os.path.join(dest_hpxml_path, Path(r[0]).stem + ".xml") for r in successful_results
    ]

    return {
        "converted_files": converted_files,
        "successful_conversions": len(successful_results),
        "failed_conversions": len(failed_results),
        "simulation_results": dest_hpxml_path if simulate else None,
        "errors": [r[2] for r in failed_results],
        "results_file": results_file,
    }


def batch_convert_h2k_files(
    input_files: List[str],
    output_directory: str,
    simulate: bool = True,
    mode: str = "SOC",
    max_workers: Optional[int] = None,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Efficiently convert multiple H2K files with progress tracking.

    Args:
        input_files: List of H2K file paths to convert
        output_directory: Directory for output files
        simulate: Run EnergyPlus simulation. Default: True
        mode: Translation mode. Default: 'SOC'
        max_workers: Number of parallel workers. Auto-detected if None
        progress_callback: Function called with (completed, total) for progress tracking

    Returns:
        Dict containing detailed conversion results:
        - 'converted_files': List of successfully converted file paths
        - 'successful_conversions': Number of successful conversions
        - 'failed_conversions': Number of failed conversions
        - 'simulation_results': Path to simulation results if simulate=True
        - 'errors': List of error messages for failed conversions
        - 'results_file': Path to results markdown file

    Example:
        >>> from h2k_hpxml.api import batch_convert_h2k_files
        >>> import glob
        >>>
        >>> def progress_tracker(completed, total):
        ...     percentage = (completed / total) * 100
        ...     print(f"Progress: {completed}/{total} ({percentage:.1f}%)")
        >>>
        >>> h2k_files = glob.glob('*.h2k')
        >>> results = batch_convert_h2k_files(
        ...     input_files=h2k_files,
        ...     output_directory='output/',
        ...     progress_callback=progress_tracker
        ... )
    """
    # Validate inputs
    if not input_files:
        raise ValueError("input_files list cannot be empty")

    # Ensure all files exist and are .h2k files
    for filepath in input_files:
        if not Path(filepath).exists():
            raise FileNotFoundError(f"H2K file not found: {filepath}")
        if not filepath.lower().endswith(".h2k"):
            raise ValueError(f"File must have .h2k extension: {filepath}")

    # Create output directory
    os.makedirs(output_directory, exist_ok=True)

    # Determine number of workers
    if max_workers is None:
        max_workers = max(1, os.cpu_count() - 1)

    # Load configuration
    config_manager = ConfigManager()
    hpxml_os_path = str(config_manager.hpxml_os_path)
    ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

    # Get OpenStudio binary
    openstudio_binary = get_openstudio_path()
    if not openstudio_binary or not Path(openstudio_binary).exists():
        # Fall back to finding it
        from .cli.convert import get_openstudio_binary_path

        openstudio_binary = get_openstudio_binary_path()

    # Build simulation flags (using defaults for batch processing)
    flags = _build_simulation_flags()

    # Track progress
    completed = 0
    total = len(input_files)

    def process_file_with_progress(filepath: str) -> Tuple[str, str, str]:
        """Process file and update progress."""
        nonlocal completed

        try:
            # Convert H2K to HPXML
            hpxml_path = _convert_h2k_file_to_hpxml(filepath, output_directory)

            if simulate:
                # Run simulation
                time.sleep(3)  # Brief pause before simulation
                status, error_msg = _run_hpxml_simulation(
                    hpxml_path=hpxml_path,
                    ruby_hpxml_path=ruby_hpxml_path,
                    hpxml_os_path=hpxml_os_path,
                    flags=flags,
                )

                if status == "Success":
                    result = (filepath, "Success", "")
                else:
                    # Handle simulation error
                    tb = traceback.format_exc()
                    error_details = _handle_conversion_error(
                        filepath=filepath,
                        dest_hpxml_path=output_directory,
                        error=subprocess.CalledProcessError(1, "simulation", error_msg),
                        traceback_str=tb,
                    )
                    result = (filepath, "Failure", error_details)
            else:
                result = (filepath, "Success", "")
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during processing: {tb}")
            error_details = _handle_conversion_error(
                filepath=filepath,
                dest_hpxml_path=output_directory,
                error=e,
                traceback_str=tb,
            )
            result = (filepath, "Failure", error_details)

        # Update progress
        completed += 1
        if progress_callback:
            progress_callback(completed, total)

        return result

    # Process files in parallel
    logger.info(f"Processing {total} files with {max_workers} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file_with_progress, input_files))

    # Separate successful and failed results
    successful_results = [r for r in results if r[1] == "Success"]
    failed_results = [r for r in results if r[1] == "Failure"]

    # Write results to markdown file
    results_file = os.path.join(output_directory, "processing_results.md")
    with open(results_file, "w") as mdfile:
        mdfile.write("| Filepath | Status | Error |\n")
        mdfile.write("|----------|--------|-------|\n")
        for result in failed_results:
            mdfile.write(f"| {result[0]} | {result[1]} | {result[2]} |\n")

    return {
        "converted_files": [r[0] for r in successful_results],
        "successful_conversions": len(successful_results),
        "failed_conversions": len(failed_results),
        "simulation_results": output_directory if simulate else None,
        "errors": [r[2] for r in failed_results],
        "results_file": results_file,
    }


def validate_dependencies() -> Dict[str, Any]:
    """
    Validate that all required dependencies are available.

    Checks for OpenStudio, OpenStudio-HPXML, and other required dependencies.

    Returns:
        Dict containing validation results:
        - 'valid': Boolean indicating if all dependencies are available
        - 'openstudio': OpenStudio status and version
        - 'hpxml': OpenStudio-HPXML status and version
        - 'missing': List of missing dependencies
        - 'recommendations': Installation recommendations

    Example:
        >>> status = validate_dependencies()
        >>> if not status['valid']:
        ...     print("Missing dependencies:", status['missing'])
    """
    try:
        # Use existing validation logic - check only mode
        result = _validate_dependencies(interactive=False, check_only=True, skip_deps=False)

        # The existing function returns a boolean, so we need to create
        # a more detailed response for the API
        if result:
            return {
                "valid": True,
                "openstudio": "Available",
                "hpxml": "Available",
                "missing": [],
                "recommendations": [],
            }
        else:
            return {
                "valid": False,
                "openstudio": "Unknown",
                "hpxml": "Unknown",
                "missing": ["Dependency validation failed"],
                "recommendations": [
                    "Run os-setup --setup to configure dependencies",
                    "Run os-setup --install-quiet to install missing dependencies",
                ],
            }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "openstudio": "Error",
            "hpxml": "Error",
            "missing": ["Unable to determine dependency status"],
            "recommendations": [
                "Run os-setup --setup to configure dependencies",
                "Check logs for detailed error information",
            ],
        }


# Backward compatibility alias
h2ktohpxml = convert_h2k_string
