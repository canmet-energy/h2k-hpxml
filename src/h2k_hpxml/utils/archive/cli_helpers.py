"""Common utility functions for CLI tools and file processing."""

import concurrent.futures
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from ..config import ConfigManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class FileProcessingUtilities:
    """Utilities for processing files in CLI tools."""

    @staticmethod
    def detect_xml_encoding(filepath):
        """
        Detect XML encoding from file header.

        Args:
            filepath: Path to XML file

        Returns:
            Detected encoding or 'utf-8' as fallback
        """
        try:
            with open(filepath, "rb") as f:
                first_line = f.readline()
                match = re.search(rb'encoding=[\'"]([A-Za-z0-9_\-]+)[\'"]', first_line)
                if match:
                    return match.group(1).decode("ascii")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not detect encoding for {filepath}: {e}")

        return "utf-8"  # fallback

    @staticmethod
    def read_file_with_encoding_detection(filepath):
        """
        Read file content with automatic encoding detection.

        Args:
            filepath: Path to file to read

        Returns:
            File content as string

        Raises:
            OSError: If file cannot be read
        """
        encoding = FileProcessingUtilities.detect_xml_encoding(filepath)
        logger.debug(f"Reading {filepath} with encoding: {encoding}")

        try:
            with open(filepath, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            logger.warning(
                f"Failed to read {filepath} with {encoding}, trying utf-8 with error handling"
            )
            with open(filepath, encoding="utf-8", errors="replace") as f:
                return f.read()

    @staticmethod
    def ensure_output_directory(
        base_path: Path, filename: str, clean_existing: bool = False
    ) -> Path:
        """
        Ensure output directory exists for a given filename.

        Args:
            base_path: Base output directory
            filename: Name of file (used to create subdirectory)
            clean_existing: Whether to clean existing directory

        Returns:
            Path to output directory
        """
        file_stem = Path(filename).stem
        output_dir = base_path / file_stem

        if clean_existing and output_dir.exists():
            shutil.rmtree(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @staticmethod
    def find_files_by_extension(directory, extension):
        """
        Find all files with specific extension in directory.

        Args:
            directory: Directory to search
            extension: File extension (with or without dot)

        Returns:
            List of matching file paths
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        if not directory.is_dir():
            return []

        return [f for f in directory.iterdir() if f.suffix.lower() == extension.lower()]

    @staticmethod
    def save_processing_error(
        filepath: Path, dest_path: Path, error: Exception, traceback_str: str
    ) -> str:
        """
        Save processing error information to file.

        Args:
            filepath: Path to file that failed
            dest_path: Destination directory for error files
            error: The error that occurred
            traceback_str: Formatted traceback string

        Returns:
            Error message for reporting
        """
        error_dir = FileProcessingUtilities.ensure_output_directory(dest_path, filepath.name)
        error_file_path = error_dir / "error.txt"

        try:
            with open(error_file_path, "w", encoding="utf-8") as error_file:
                error_file.write(f"Error: {str(error)}\n")
                error_file.write(f"File: {filepath}\n")
                error_file.write(f"Timestamp: {time.ctime()}\n")
                error_file.write(f"\nTraceback:\n{traceback_str}")

            logger.info(f"Error details saved to: {error_file_path}")
        except OSError as e:
            logger.error(f"Failed to save error file: {e}")

        # Check for specific error patterns
        error_str = str(error)
        if "returned non-zero exit status 1." in error_str:
            run_log_path = error_dir / "run" / "run.log"
            if run_log_path.exists():
                try:
                    with open(run_log_path) as run_log_file:
                        return "**OS-HPXML ERROR**: " + run_log_file.read()
                except OSError:
                    pass

        return error_str


class SimulationUtilities:
    """Utilities for running OpenStudio simulations."""

    @staticmethod
    def build_simulation_flags(**kwargs):
        """
        Build simulation flags string for OpenStudio command.

        Args:
            **kwargs: Simulation options (add_component_loads, debug, etc.)

        Returns:
            Formatted flags string for simulation command
        """
        flag_mapping = {
            "add_component_loads": "--add-component-loads",
            "debug": "--debug",
            "skip_validation": "--skip-validation",
            "output_format": "--output-format",
            "add_stochastic_schedules": "--add-stochastic-schedules",
        }

        flags = []

        # Handle simple boolean and value flags
        for key, flag in flag_mapping.items():
            value = kwargs.get(key)
            if value:
                if isinstance(value, bool):
                    flags.append(flag)
                else:
                    flags.append(f"{flag} {value}")

        # Handle repeated options
        repeated_options = [
            ("timestep", "--timestep"),
            ("hourly", "--hourly"),
            ("monthly", "--monthly"),
            ("daily", "--daily"),
            ("add_timeseries_output_variable", "--add-timeseries-output-variable"),
        ]

        for key, flag in repeated_options:
            values = kwargs.get(key, [])
            for value in values:
                flags.append(f"{flag} {value}")

        return " ".join(flags)

    @staticmethod
    def get_openstudio_binary_path():
        """
        Get the OpenStudio binary path using dependency manager.

        Returns:
            Path to OpenStudio binary
        """
        try:
            from ..utils.dependencies import DependencyManager

            dep_manager = DependencyManager()

            # Try to find OpenStudio binary in common locations
            for openstudio_path in dep_manager._get_openstudio_paths():
                if dep_manager._test_binary_path(openstudio_path):
                    return openstudio_path

            # Try the command in PATH
            if dep_manager._test_openstudio_command():
                return "openstudio"  # Found in PATH

        except ImportError:
            logger.warning("DependencyManager not available, using fallback paths")

        # Fallback to platform-specific defaults
        import platform

        if platform.system() == "Windows":
            return "C:\\openstudio\\bin\\openstudio.exe"
        else:
            return "/usr/local/bin/openstudio"

    @staticmethod
    def run_openstudio_simulation(
        hpxml_path: Path,
        hpxml_os_path: Path,
        flags: str,
        ruby_script: str = "workflow/run_simulation.rb",
    ) -> Tuple[bool, str]:
        """
        Run OpenStudio simulation on HPXML file.

        Args:
            hpxml_path: Path to HPXML file
            hpxml_os_path: OpenStudio HPXML installation path
            flags: Simulation flags string
            ruby_script: Ruby simulation script path

        Returns:
            Tuple of (success_status, error_message)
        """
        openstudio_binary = SimulationUtilities.get_openstudio_binary_path()
        ruby_hpxml_path = hpxml_os_path / ruby_script

        command = [openstudio_binary, str(ruby_hpxml_path), "-x", str(hpxml_path.absolute())]

        # Add flags
        if flags:
            command.extend(flags.split())

        try:
            logger.info(f"Running simulation for: {hpxml_path}")
            logger.debug(f"Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                cwd=str(hpxml_os_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per simulation
            )

            logger.debug(f"Simulation stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Simulation stderr: {result.stderr}")

            return True, ""

        except subprocess.CalledProcessError as e:
            error_msg = f"Simulation failed with exit code {e.returncode}: {e.stderr}"
            logger.error(error_msg)
            return False, e.stderr

        except subprocess.TimeoutExpired:
            error_msg = "Simulation timed out after 5 minutes"
            logger.error(error_msg)
            return False, error_msg


class ConcurrentProcessing:
    """Utilities for concurrent file processing."""

    @staticmethod
    def get_optimal_worker_count():
        """Get optimal number of worker threads based on CPU count."""
        return max(1, os.cpu_count() - 1)

    @staticmethod
    def process_files_concurrently(
        files: List[Path], processor_func: callable, max_workers: Optional[int] = None
    ) -> List[Tuple[Path, str, str]]:
        """
        Process files concurrently with ThreadPoolExecutor.

        Args:
            files: List of file paths to process
            processor_func: Function to process each file
            max_workers: Maximum number of worker threads

        Returns:
            List of (filepath, status, error_message) tuples
        """
        if max_workers is None:
            max_workers = ConcurrentProcessing.get_optimal_worker_count()

        logger.info(f"Processing {len(files)} files with {max_workers} threads")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(processor_func, files))

        return results

    @staticmethod
    def create_processing_report(
        results: List[Tuple[Path, str, str]],
        output_path: Path,
        report_name: str = "processing_results.md",
    ) -> Path:
        """
        Create markdown processing report from results.

        Args:
            results: List of (filepath, status, error_message) tuples
            output_path: Directory to save report
            report_name: Name of report file

        Returns:
            Path to created report file
        """
        report_path = output_path / report_name

        # Separate successful and failed results
        successful = [r for r in results if r[1] == "Success"]
        failed = [r for r in results if r[1] != "Success"]

        try:
            with open(report_path, "w", encoding="utf-8") as mdfile:
                mdfile.write("# Processing Results Report\n\n")
                mdfile.write(f"**Total Files**: {len(results)}\n")
                mdfile.write(f"**Successful**: {len(successful)}\n")
                mdfile.write(f"**Failed**: {len(failed)}\n\n")

                if failed:
                    mdfile.write("## Failed Files\n\n")
                    mdfile.write("| Filepath | Status | Error |\n")
                    mdfile.write("|----------|--------|-------|\n")
                    for filepath, status, error in failed:
                        # Escape markdown special characters in error message
                        error_escaped = error.replace("|", "\\|").replace("\n", " ")
                        mdfile.write(f"| {filepath} | {status} | {error_escaped} |\n")
                    mdfile.write("\n")

                if successful:
                    mdfile.write("## Successful Files\n\n")
                    for filepath, _, _ in successful:
                        mdfile.write(f"- {filepath}\n")

            logger.info(f"Processing report saved to: {report_path}")
            return report_path

        except OSError as e:
            logger.error(f"Failed to create processing report: {e}")
            raise


class ProjectUtilities:
    """Utilities for project-level operations."""

    @staticmethod
    def find_project_root(start_path=None):
        """
        Find project root directory containing conversionconfig.ini.

        Args:
            start_path: Starting directory for search (defaults to current file location)

        Returns:
            Path to project root directory or current working directory as fallback
        """
        if start_path is None:
            start_path = Path(__file__).parent

        current_dir = Path(start_path).resolve()

        for parent in [current_dir] + list(current_dir.parents):
            config_file = parent / "conversionconfig.ini"
            if config_file.exists():
                logger.debug(f"Found project root at: {parent}")
                return parent

        # Fallback to current working directory
        fallback = Path.cwd()
        logger.warning(f"Could not find project root, using fallback: {fallback}")
        return fallback

    @staticmethod
    def setup_paths_from_config():
        """
        Setup common paths from configuration.

        Returns:
            Dictionary of configured paths
        """
        try:
            config = ConfigManager()

            paths = {
                "source_h2k_path": config.source_h2k_path,
                "hpxml_os_path": config.hpxml_os_path,
                "dest_hpxml_path": config.dest_hpxml_path,
            }

            logger.debug(f"Configured paths: {paths}")
            return paths

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    @staticmethod
    def validate_required_paths(paths):
        """
        Validate that required paths exist.

        Args:
            paths: Dictionary of paths to validate

        Returns:
            List of validation error messages
        """
        errors = []

        for name, path in paths.items():
            if name == "dest_hpxml_path":
                # Output paths can be created
                continue

            if not path.exists():
                errors.append(f"Required path does not exist: {name} = {path}")
            elif name == "hpxml_os_path" and not path.is_dir():
                errors.append(f"Path must be a directory: {name} = {path}")

        return errors


# Convenience functions combining multiple utilities
def setup_file_processing(
    input_path: str, output_path: Optional[str] = None, extension: str = ".h2k"
) -> Tuple[List[Path], Path]:
    """
    Setup file list and output path for processing.

    Args:
        input_path: Input file or directory path
        output_path: Output directory path (optional)
        extension: File extension to search for

    Returns:
        Tuple of (file_list, output_directory)

    Raises:
        ValueError: If no files found or invalid input
    """
    input_path_obj = Path(input_path)

    # Determine file list
    if input_path_obj.is_file() and input_path_obj.suffix.lower() == extension.lower():
        files = [input_path_obj]
        default_output = input_path_obj.parent / "output"
    elif input_path_obj.is_dir():
        files = FileProcessingUtilities.find_files_by_extension(input_path_obj, extension)
        if not files:
            raise ValueError(f"No {extension} files found in directory {input_path_obj}")
        default_output = input_path_obj / "output"
    else:
        raise ValueError(f"Invalid input path: {input_path_obj}")

    # Determine output path
    if output_path:
        output_dir = Path(output_path)
    else:
        output_dir = default_output

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Found {len(files)} files to process")
    logger.info(f"Output directory: {output_dir}")

    return files, output_dir
