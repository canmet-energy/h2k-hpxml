import os
import subprocess
import sys
import configparser
from configparser import NoOptionError, NoSectionError
from pathlib import Path

from h2k_hpxml.analysis import annual
from h2k_hpxml.utils.dependencies import DependencyManager


def get_config_with_dependency_paths():
    """Get configuration with dependency paths."""
    config = configparser.ConfigParser()
    config.read("conversionconfig.ini")
    
    # Get paths from config file (maintained by dependencies.py)
    try:
        source_h2k_path = config.get("paths", "source_h2k_path")
        hpxml_os_path = config.get("paths", "hpxml_os_path")
        openstudio_binary = config.get("paths", "openstudio_binary")
        dest_hpxml_path = config.get("paths", "dest_hpxml_path")
    except (NoOptionError, NoSectionError) as e:
        print(f"❌ Configuration file missing required sections: {e}")
        print("Run 'h2k-deps' to set up dependencies and configuration")
        sys.exit(1)
    
    # Override with environment variables if set
    hpxml_os_path = os.environ.get('OPENSTUDIO_HPXML_PATH', hpxml_os_path)
    openstudio_binary = os.environ.get('OPENSTUDIO_PATH', openstudio_binary)
    
    # If paths are empty or missing, update config with current detections
    if not openstudio_binary.strip() or not hpxml_os_path.strip():
        print("🔄 Configuration incomplete - updating with detected paths...")
        from h2k_hpxml.utils.dependencies import DependencyManager
        
        dep_manager = DependencyManager(interactive=False)
        if not dep_manager.validate_all(check_only=True):
            print("❌ Required dependencies not found. Run 'h2k-deps --auto-install' to install.")
            sys.exit(1)
        
        # Re-read updated config
        config.read("conversionconfig.ini")
        openstudio_binary = config.get("paths", "openstudio_binary", fallback="")
        hpxml_os_path = config.get("paths", "hpxml_os_path", fallback="")
    
    # Final validation
    if not openstudio_binary or not Path(openstudio_binary).exists():
        print(f"❌ OpenStudio binary not found: {openstudio_binary}")
        print("Please run 'h2k-deps --update-config' to detect OpenStudio")
        sys.exit(1)
    
    if not hpxml_os_path or not Path(hpxml_os_path).exists():
        print(f"❌ OpenStudio-HPXML path not found: {hpxml_os_path}")
        print("Please run 'h2k-deps --update-config' to detect OpenStudio-HPXML")
        sys.exit(1)
    
    # Get simulation flags
    try:
        flags = config.get("simulation", "flags")
    except (NoOptionError, NoSectionError):
        flags = ""
    
    return {
        'source_h2k_path': source_h2k_path,
        'hpxml_os_path': hpxml_os_path,
        'openstudio_binary': openstudio_binary,
        'dest_hpxml_path': dest_hpxml_path,
        'flags': flags
    }


# Get configuration with dynamic paths
config_data = get_config_with_dependency_paths()
source_h2k_path = config_data['source_h2k_path']
hpxml_os_path = config_data['hpxml_os_path']
openstudio_binary = config_data['openstudio_binary']
dest_hpxml_path = config_data['dest_hpxml_path']
flags = config_data['flags']

print(f"Using OpenStudio-HPXML path: {hpxml_os_path}")
print(f"Using OpenStudio binary: {openstudio_binary}")
print(f"Simulation flags: {flags}")


def run_hpxml_os(file="", path=""):
    """
    Run HPXML simulation using OpenStudio.

    Args:
        file: HPXML filename to simulate
        path: Relative path within OpenStudio-HPXML directory
    """
    path_to_log = f"{hpxml_os_path}/{path}/run"
    success = False
    result = {}

    # Validate that OpenStudio-HPXML path exists
    hpxml_path = Path(hpxml_os_path)
    if not hpxml_path.exists():
        print(f"Error: OpenStudio-HPXML path not found: {hpxml_os_path}")
        print("Run 'h2k-deps --check-only' to diagnose dependency issues.")
        return {"result": None, "success": False, "path_to_log": path_to_log, "error": "Missing OpenStudio-HPXML"}

    # Check if simulation file exists
    sim_file_path = hpxml_path / path / file
    if not sim_file_path.exists():
        print(f"Error: Simulation file not found: {sim_file_path}")
        return {"result": None, "success": False, "path_to_log": path_to_log, "error": "Missing simulation file"}

    # Validate OpenStudio binary exists
    if not Path(openstudio_binary).exists():
        print(f"Error: OpenStudio binary not found: {openstudio_binary}")
        print("Please check openstudio_binary setting in conversionconfig.ini")
        return {"result": None, "success": False, "path_to_log": path_to_log, "error": "Missing OpenStudio binary"}

    try:
        # Run OpenStudio simulation using configured binary path
        cmd = f'"{openstudio_binary}" workflow/run_simulation.rb -x {path}/{file} {flags}'.strip()
        print(f"Running command: {cmd}")
        print(f"Working directory: {hpxml_os_path}")
        print(f"OpenStudio binary: {openstudio_binary}")

        result = subprocess.run(
            cmd,
            cwd=hpxml_os_path,
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        success = True
        print("Simulation completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"Error in simulation: {e}")
        print(f"Return code: {e.returncode}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"stdout: {e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"stderr: {e.stderr}")
        print("Check simulation logs for details")
        result = e

    except FileNotFoundError as e:
        print(f"Error: OpenStudio command not found: {e}")
        print(f"Tried to execute: {openstudio_binary}")
        print("Make sure OpenStudio is properly installed and path is correct in conversionconfig.ini")
        result = e

    finally:
        return {
            "result": result,
            "success": success,
            "path_to_log": path_to_log,
            "hpxml_path": hpxml_os_path,
            "openstudio_binary": openstudio_binary
        }


if __name__ == "__main__":
    # Example usage
    filename = "SimpleBoxModel-USpec.xml"
    result = run_hpxml_os(filename, "workflow/translated_h2ks")

    if result["success"]:
        print(f"✅ Simulation successful for {filename}")
        print(f"📁 Logs available at: {result['path_to_log']}")
    else:
        print(f"❌ Simulation failed for {filename}")
        if "error" in result:
            print(f"Error details: {result['error']}")
