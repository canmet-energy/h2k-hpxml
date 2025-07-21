#!/usr/bin/env python3
"""
H2K to HPXML Conversion CLI Tool

Convert H2K files to HPXML format and run OpenStudio simulations.
"""

import pathlib
import os
import sys
import configparser
import subprocess
import click
from colorama import Fore, Style
import pyfiglet
import random
import traceback
import re
import shutil
import csv
import concurrent.futures
import time

from h2k_hpxml.core.translator import h2ktohpxml


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.7.0.1.1')
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
        'Chris Kirney\n',
        'Phylroy Lopex\n',
        'Julia Purdy\n'
    ]:
        print(random.choice(colors) + pyfiglet.figlet_format(name) + Fore.RESET)


@cli.command(help="Convert and Simulate H2K file to OS/E+.")
@click.option('--input_path', '-i', default=os.path.join('/shared'), 
              help='h2k file or folder containing h2k files.')
@click.option('--output_path', '-o', 
              help='Path to output hpxml files. By default it is the same as the input path with a folder named output created inside it.')
@click.option('--timestep', multiple=True, default=[], 
              help='Request timestep output type (ALL, total, fuels, enduses, systemuses, emissions, emissionfuels, emissionenduses, hotwater, loads, componentloads, unmethours, temperatures, airflows, weather, resilience); can be called multiple times')
@click.option('--daily', multiple=True, default=[], 
              help='Request daily output type (ALL, total, fuels, enduses, systemuses, emissions, emissionfuels, emissionenduses, hotwater, loads, componentloads, unmethours, temperatures, airflows, weather, resilience); can be called multiple times')
@click.option('--hourly', multiple=True, default=[], 
              help='Request hourly output type (ALL, total, fuels, enduses, systemuses, emissions, emissionfuels, emissionenduses, hotwater, loads, componentloads, unmethours, temperatures, airflows, weather, resilience); can be called multiple times')
@click.option('--monthly', multiple=True, default=[], 
              help='Request monthly output type (ALL, total, fuels, enduses, systemuses, emissions, emissionfuels, emissionenduses, hotwater, loads, componentloads, unmethours, temperatures, airflows, weather, resilience); can be called multiple times')
@click.option('--add-component-loads', '-l', is_flag=True, default=True, 
              help='Add component loads.')
@click.option('--debug', '-d', is_flag=True, default=False, 
              help='Enable debug mode and all extra file outputs.')
@click.option('--skip-validation', '-s', is_flag=True, default=False, 
              help='Skip Schema/Schematron validation for faster performance')
@click.option('--output-format', '-f', default='csv', 
              help='Output format for the simulation results (csv, json, msgpack, csv_dview)')
@click.option('--add-stochastic-schedules', is_flag=True, default=False, 
              help='Add detailed stochastic occupancy schedules')
@click.option('--add-timeseries-output-variable', multiple=True, default=[], 
              help='Add timeseries output variable; can be called multiple times')
@click.option('--do-not-sim', is_flag=True, default=False, 
              help='Convert only, do not run simulation')
def run(input_path, output_path, timestep, daily, hourly, monthly, add_component_loads,
        debug, skip_validation, output_format, add_stochastic_schedules,
        add_timeseries_output_variable, do_not_sim):
    """
    Convert H2K files to HPXML format and optionally run simulations.

    Args:
        input_path (str): Path to h2k file or folder containing h2k files
        output_path (str): Path to output hpxml files
        timestep, daily, hourly, monthly: Output frequency options
        add_component_loads (bool): Add component loads
        debug (bool): Enable debug mode
        skip_validation (bool): Skip validation for faster performance
        output_format (str): Output format (csv, json, msgpack, csv_dview)
        add_stochastic_schedules (bool): Add stochastic schedules
        add_timeseries_output_variable (list): Additional output variables
        do_not_sim (bool): Convert only, don't simulate
    """
    
    # Ensure that only one of the hourly, monthly or timeseries options is provided
    if sum(bool(x) for x in [hourly, monthly, timestep]) > 1:
        raise ValueError("Only one of the options --hourly, --monthly, or --timestep can be provided at a time.")

    # Refactor flag-building logic
    flag_options = {
        "--add-component-loads": add_component_loads,
        "--debug": debug,
        "--skip-validation": skip_validation,
        "--output-format": output_format,
    }
    flags = " ".join(f"{key} {value}" if value else key for key, value in flag_options.items() if value)

    # Add options that can be repeated
    for option, values in [("--timestep", timestep), ("--hourly", hourly), ("--monthly", monthly), ("--daily", daily)]:
        flags += " " + " ".join(f"{option} {v}" for v in values)

    if add_stochastic_schedules:
        flags += " --add-stochastic-schedules"
    if add_timeseries_output_variable:
        flags += " " + " ".join(f"--add-timeseries-output-variable {v}" for v in add_timeseries_output_variable)

    # Find project root and read config
    project_root = _find_project_root()
    config = configparser.ConfigParser()
    config.read(os.path.join(project_root, 'conversionconfig.ini'))
    hpxml_os_path = config.get("paths", "hpxml_os_path")
    ruby_hpxml_path = os.path.join(hpxml_os_path, 'workflow', 'run_simulation.rb')
    
    # Get source and destination paths
    source_h2k_path = input_path
    if output_path:
        dest_hpxml_path = output_path
    else:
        # Default to creating an output folder in the same directory as the input
        if os.path.isfile(input_path):
            dest_hpxml_path = os.path.join(os.path.dirname(input_path), "output")
        else:
            dest_hpxml_path = os.path.join(input_path, "output")

    # Create the destination folder
    os.makedirs(dest_hpxml_path, exist_ok=True)

    # Determine if the source path is a single file or a directory of files
    if os.path.isfile(source_h2k_path) and source_h2k_path.lower().endswith(".h2k"):
        h2k_files = [source_h2k_path]
    elif os.path.isdir(source_h2k_path):
        h2k_files = [os.path.join(source_h2k_path, f) for f in os.listdir(source_h2k_path) if f.lower().endswith(".h2k")]
        if not h2k_files:
            print(f"No .h2k files found in the directory {source_h2k_path}.")
            sys.exit(1)
    else:
        print(f"The source path {source_h2k_path} is neither a .h2k file nor a directory.")
        sys.exit(1)

    def detect_xml_encoding(filepath):
        """Detect XML encoding from file header."""
        with open(filepath, "rb") as f:
            first_line = f.readline()
            match = re.search(br'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
            if match:
                return match.group(1).decode("ascii")
        return "utf-8"  # fallback

    def process_file(filepath):
        """Process a single H2K file to HPXML and optionally simulate."""
        try:
            print("================================================")
            print("Processing file:", filepath)

            # Detect encoding from XML declaration
            encoding = detect_xml_encoding(filepath)
            print(f"Detected encoding for {filepath}: {encoding}")

            # Read the content of the H2K file with detected encoding
            with open(filepath, "r", encoding=encoding) as f:
                h2k_string = f.read()
            
            # Convert the H2K content to HPXML format
            hpxml_string = h2ktohpxml(h2k_string)
            
            # Define the output path for the converted HPXML file
            hpxml_path = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem, pathlib.Path(filepath).stem + ".xml")

            # If the destination path exists, delete the folder
            if os.path.exists(hpxml_path):
                shutil.rmtree(os.path.dirname(hpxml_path))
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(hpxml_path), exist_ok=True)
            
            print("Saving converted file to:", hpxml_path)
            
            # Write the converted HPXML content to the output file
            with open(hpxml_path, "w") as f:
                f.write(hpxml_string)

            if not do_not_sim:
                # Pause 3 seconds
                time.sleep(3)

                # Run the OpenStudio simulation
                command = [
                    f"/usr/local/bin/openstudio",
                    ruby_hpxml_path,
                    "-x",
                    os.path.abspath(hpxml_path)
                ]
                
                # Convert flags to a list of strings
                flagslist = flags.split()
                command.extend(flagslist)
                
                try:
                    print("Running simulation for file:", hpxml_path)
                    result = subprocess.run(
                        command,
                        cwd=hpxml_os_path,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print("Simulation result:", result)
                    return (filepath, "Success", "")
                except subprocess.CalledProcessError as e:
                    print("Error during simulation:", e.stderr)
                    tb = traceback.format_exc()
                    print(tb)

                    # Save traceback to a separate error.txt file
                    error_dir = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem)
                    os.makedirs(error_dir, exist_ok=True)
                    error_file_path = os.path.join(error_dir, "error.txt")
                    with open(error_file_path, "w") as error_file:
                        error_file.write(f"{e.stderr}\n{tb}")

                    # Check for specific exception text and handle run.log
                    if "returned non-zero exit status 1." in str(e):
                        run_log_path = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem, "run", "run.log")
                        if os.path.exists(run_log_path):
                            with open(run_log_path, "r") as run_log_file:
                                run_log_content = "**OS-HPXML ERROR**: " + run_log_file.read()
                                return (filepath, "Failure", run_log_content)

                    # Default behavior for other exceptions
                    return (filepath, "Failure", str(e))
            else:
                return (filepath, "Success", "")
        except Exception as e:
            tb = traceback.format_exc()
            print("Exception during processing:", tb)

            # Save traceback to a separate error.txt file
            error_dir = os.path.join(dest_hpxml_path, pathlib.Path(filepath).stem)
            os.makedirs(error_dir, exist_ok=True)
            error_file_path = os.path.join(error_dir, "error.txt")
            with open(error_file_path, "w") as error_file:
                error_file.write(f"{str(e)}\n{tb}")

            # Return only the error summary for the CSV
            return (filepath, "Failure", str(e))

    # Use ThreadPoolExecutor to process files concurrently with a limited number of threads
    max_workers = max(1, os.cpu_count() - 1)
    print(f"Processing files with {max_workers} threads...")
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
    """Find the project root directory containing conversionconfig.ini."""
    current_dir = pathlib.Path(__file__).parent
    for parent in [current_dir] + list(current_dir.parents):
        config_file = parent / 'conversionconfig.ini'
        if config_file.exists():
            return str(parent)
    # Fallback to current working directory
    return os.getcwd()


def main():
    """Entry point for the h2k2hpxml command."""
    cli()


if __name__ == '__main__':
    main()