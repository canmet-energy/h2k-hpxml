"""
High-level API for H2K to HPXML conversion.

This module provides a clean, user-friendly interface for the most common
use cases while hiding internal implementation details.
"""

import os
import pathlib
import sys
import time
import traceback
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple

from .core.translator import h2ktohpxml as _h2ktohpxml
from .config.manager import ConfigManager
from .utils.dependencies import validate_dependencies as _validate_dependencies
from .exceptions import H2KHPXMLError, ConfigurationError, DependencyError, SimulationError
from .utils.logging import get_logger

# Import CLI helper functions
from .cli.convert import (
    _build_simulation_flags,
    _convert_h2k_to_hpxml, 
    _run_simulation,
    _handle_processing_error
)


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
    config: Optional[Dict[str, Any]] = None
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
        output_path = input_path.with_suffix('.xml')
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read H2K file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            h2k_content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings if UTF-8 fails
        with open(input_path, 'r', encoding='iso-8859-1') as f:
            h2k_content = f.read()
    
    # Convert to HPXML
    hpxml_content = convert_h2k_string(h2k_content, config)
    
    # Write HPXML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(hpxml_content)
    
    return str(output_path)


def run_full_workflow(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    simulate: bool = True,
    timestep: int = 10,
    output_format: str = "csv",
    add_component_loads: bool = True,
    debug: bool = False,
    skip_validation: bool = False,
    add_stochastic_schedules: bool = False,
    add_timeseries_output_variable: Optional[List[str]] = None,
    max_workers: Optional[int] = None,
    **kwargs
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
        timestep: Simulation timestep in minutes (default: 10)
        output_format: Output format for results ("csv", "json", "msgpack")
        add_component_loads: Whether to include component loads in output
        debug: Enable debug mode with extra outputs
        skip_validation: Skip Schema/Schematron validation for speed
        add_stochastic_schedules: Add detailed stochastic occupancy schedules
        add_timeseries_output_variable: Additional timeseries output variables
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
        ...     output_format='csv'
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
    
    # Build simulation flags
    flags = _build_simulation_flags(
        add_component_loads=add_component_loads,
        debug=debug,
        skip_validation=skip_validation,
        output_format=output_format,
        timestep=timestep if timestep != 10 else None,  # Only pass if not default
        daily=(),  # Not exposed in API for simplicity
        hourly=(),  # Not exposed in API for simplicity  
        monthly=(), # Not exposed in API for simplicity
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
    if input_path.is_file() and input_path.suffix.lower() == '.h2k':
        h2k_files = [str(input_path)]
    elif input_path.is_dir():
        h2k_files = [
            str(f) for f in input_path.glob("*.h2k") 
            if f.suffix.lower() == '.h2k'
        ]
        if not h2k_files:
            raise FileNotFoundError(f"No .h2k files found in directory {input_path}")
    else:
        raise ValueError(f"Input path must be a .h2k file or directory: {input_path}")
    
    def process_file(filepath: str) -> Tuple[str, str, str]:
        """Process a single H2K file to HPXML and optionally simulate."""
        try:
            # Convert H2K to HPXML
            hpxml_path = _convert_h2k_to_hpxml(filepath, dest_hpxml_path)
            
            if simulate:
                # Brief pause before simulation
                time.sleep(3)
                
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
                        Exception(error_msg),
                        tb,
                    )
                    return (filepath, "Failure", error_details)
            else:
                return (filepath, "Success", "")
                
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during processing {filepath}: {tb}")
            
            error_details = _handle_processing_error(filepath, dest_hpxml_path, e, tb)
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
        os.path.join(dest_hpxml_path, Path(r[0]).stem + ".xml") 
        for r in successful_results
    ]
    
    return {
        'converted_files': converted_files,
        'successful_conversions': len(successful_results),
        'failed_conversions': len(failed_results),
        'simulation_results': dest_hpxml_path if simulate else None,
        'errors': [r[2] for r in failed_results],
        'results_file': results_file
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
        result = _validate_dependencies(
            interactive=False,
            check_only=True,
            skip_deps=False
        )
        
        # The existing function returns a boolean, so we need to create
        # a more detailed response for the API
        if result:
            return {
                'valid': True,
                'openstudio': 'Available',
                'hpxml': 'Available', 
                'missing': [],
                'recommendations': []
            }
        else:
            return {
                'valid': False,
                'openstudio': 'Unknown',
                'hpxml': 'Unknown',
                'missing': ['Dependency validation failed'],
                'recommendations': [
                    'Run h2k-deps --setup to configure dependencies',
                    'Run h2k-deps --auto-install to install missing dependencies'
                ]
            }
            
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'openstudio': 'Error',
            'hpxml': 'Error', 
            'missing': ['Unable to determine dependency status'],
            'recommendations': [
                'Run h2k-deps --setup to configure dependencies',
                'Check logs for detailed error information'
            ]
        }


# Backward compatibility alias
h2ktohpxml = convert_h2k_string