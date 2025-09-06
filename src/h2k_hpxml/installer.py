"""
Automatic dependency installer for h2k-hpxml package.

This module handles downloading and installing OpenStudio and OpenStudio-HPXML
dependencies into the package directory for consistent, versioned installations.
"""

import os
import platform
import shutil
import zipfile
import tarfile
import tomllib
from pathlib import Path
from urllib.request import urlretrieve
import ssl
import urllib.error

# Package-relative paths
PACKAGE_DIR = Path(__file__).parent
DEPS_DIR = PACKAGE_DIR / "_deps"
OPENSTUDIO_HPXML_DIR = DEPS_DIR / "OpenStudio-HPXML"
OPENSTUDIO_DIR = DEPS_DIR / "openstudio"


def get_dependency_versions():
    """Read dependency versions from pyproject.toml."""
    # Find pyproject.toml (go up from src/h2k_hpxml/installer.py to project root)
    pyproject_path = PACKAGE_DIR.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path}. "
            "Dependency versions must be defined in [tool.h2k-hpxml.dependencies] section."
        )
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to parse pyproject.toml: {e}")
    
    dependencies = data.get("tool", {}).get("h2k-hpxml", {}).get("dependencies")
    if not dependencies:
        raise ValueError(
            "Missing [tool.h2k-hpxml.dependencies] section in pyproject.toml. "
            "Please add openstudio_version, openstudio_sha, and openstudio_hpxml_version."
        )
    
    # Validate required keys
    required_keys = ["openstudio_version", "openstudio_sha", "openstudio_hpxml_version"]
    missing_keys = [key for key in required_keys if key not in dependencies]
    if missing_keys:
        raise ValueError(
            f"Missing required dependency versions in pyproject.toml: {missing_keys}. "
            f"Required keys: {required_keys}"
        )
    
    return dependencies


def get_openstudio_hpxml_url():
    """Get OpenStudio-HPXML download URL with current version."""
    versions = get_dependency_versions()
    version = versions["openstudio_hpxml_version"]
    return f"https://github.com/NREL/OpenStudio-HPXML/releases/download/{version}/OpenStudio-HPXML-{version}.zip"


def get_openstudio_urls():
    """Get OpenStudio download URLs for all platforms with current version."""
    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]
    os_sha = versions["openstudio_sha"]
    
    return {
        "Windows": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Windows.exe",
        "Linux": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Ubuntu-22.04-x86_64.tar.gz",
        "Darwin": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Darwin-x86_64.tar.gz"
    }


def get_deps_status():
    """Check if dependencies are installed."""
    return {
        "openstudio_hpxml": OPENSTUDIO_HPXML_DIR.exists(),
        "openstudio": OPENSTUDIO_DIR.exists(),
        "deps_dir": DEPS_DIR.exists()
    }


def download_file(url, dest_path, desc=""):
    """Download file with progress indicator."""
    print(f"Downloading {desc or url}...")
    
    # Create SSL context that doesn't verify certificates (for corporate networks)
    # In production, you might want to make this configurable
    import ssl
    import urllib.request
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100) if total_size > 0 else 0
            print(f"  Progress: {percent:.1f}%", end='\r')
        
        # Create opener with SSL context
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)
        
        urlretrieve(url, dest_path, reporthook=download_progress)
        print(f"\n  ✓ Downloaded to {dest_path}")
        return True
    except urllib.error.URLError as e:
        print(f"\n  ✗ Download failed: {e}")
        return False


def install_openstudio_hpxml(force=False):
    """Install OpenStudio-HPXML to package directory."""
    if OPENSTUDIO_HPXML_DIR.exists() and not force:
        print("OpenStudio-HPXML already installed")
        return True
    
    print("Installing OpenStudio-HPXML...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download zip file
    versions = get_dependency_versions()
    hpxml_version = versions["openstudio_hpxml_version"]
    zip_path = DEPS_DIR / "OpenStudio-HPXML.zip"
    if not download_file(get_openstudio_hpxml_url(), zip_path, f"OpenStudio-HPXML {hpxml_version}"):
        return False
    
    # Extract
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DEPS_DIR)
        
        # The zip extracts to OpenStudio-HPXML/OpenStudio-HPXML, so we need to move it
        extracted_dir = DEPS_DIR / "OpenStudio-HPXML"
        if extracted_dir.exists():
            print(f"  ✓ Extracted to {extracted_dir}")
        
        # Clean up zip
        zip_path.unlink()
        return True
        
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        return False


def install_openstudio(force=False):
    """Install OpenStudio SDK to package directory."""
    if OPENSTUDIO_DIR.exists() and not force:
        print("OpenStudio already installed")
        return True
    
    system = platform.system()
    openstudio_urls = get_openstudio_urls()
    if system not in openstudio_urls:
        print(f"Unsupported platform: {system}")
        return False
    
    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]
    print(f"Installing OpenStudio {os_version} for {system}...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    OPENSTUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    url = openstudio_urls[system]
    
    if system == "Windows":
        # Windows .exe installer - we can try to extract it with 7zip or similar
        # For now, download and provide instructions
        exe_path = DEPS_DIR / "OpenStudio-installer.exe"
        print("  Note: Windows installer requires extraction")
        if not download_file(url, exe_path, f"OpenStudio {os_version} for Windows"):
            return False
        print(f"  Downloaded to: {exe_path}")
        print(f"  Please extract to: {OPENSTUDIO_DIR}")
        print("  You can use 7-Zip or run: msiexec /a {exe_path} /qb TARGETDIR={OPENSTUDIO_DIR}")
        return False
        
    else:  # Linux/Mac - tar.gz files
        tar_path = DEPS_DIR / "openstudio.tar.gz"
        if not download_file(url, tar_path, f"OpenStudio {os_version} for {system}"):
            return False
        
        try:
            # Extract tar.gz
            print(f"  Extracting to {OPENSTUDIO_DIR}...")
            with tarfile.open(tar_path, 'r:gz') as tar:
                # The tar contains OpenStudio-3.9.0+hash/ folder, extract contents
                tar.extractall(DEPS_DIR)
            
            # Find the extracted folder (it has a hash in the name)
            extracted_dirs = [d for d in DEPS_DIR.iterdir() 
                            if d.is_dir() and d.name.startswith(f"OpenStudio-{os_version}")]
            
            if extracted_dirs:
                # Move contents to our standard location
                extracted_dir = extracted_dirs[0]
                print(f"  Moving from {extracted_dir.name} to openstudio/")
                
                # If OPENSTUDIO_DIR exists, remove it first
                if OPENSTUDIO_DIR.exists():
                    import shutil
                    shutil.rmtree(OPENSTUDIO_DIR)
                    
                extracted_dir.rename(OPENSTUDIO_DIR)
                print(f"  ✓ Installed to {OPENSTUDIO_DIR}")
            else:
                print("  ⚠️  Could not find extracted OpenStudio directory")
                return False
            
            # Clean up
            tar_path.unlink()
            return True
            
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")
            return False


def ensure_dependencies():
    """
    Check and install missing dependencies.
    Called automatically on package import.
    """
    status = get_deps_status()
    
    # Only install if missing
    if not status["openstudio_hpxml"]:
        install_openstudio_hpxml()
    
    # Try to install OpenStudio if missing
    if not status["openstudio"]:
        print("OpenStudio SDK not found in package. Attempting to install...")
        if not install_openstudio():
            print("Note: OpenStudio SDK installation requires manual steps or 'h2k-deps' command.")


def get_openstudio_path():
    """Get path to OpenStudio executable - bundled or system."""
    system = platform.system()
    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]
    
    # First check for bundled OpenStudio in _deps
    # The structure is different after extraction: usr/local/openstudio-{version}/bin/openstudio
    bundled_paths = [
        OPENSTUDIO_DIR / "usr" / "local" / f"openstudio-{os_version}" / "bin" / "openstudio",
        OPENSTUDIO_DIR / "bin" / "openstudio.exe" if system == "Windows" else OPENSTUDIO_DIR / "bin" / "openstudio"
    ]
    
    for exe_path in bundled_paths:
        if exe_path.exists():
            return str(exe_path)
    
    # Fallback to system installation
    system_path = shutil.which("openstudio")
    if system_path:
        return system_path
    
    # No OpenStudio found
    return None


def get_openstudio_hpxml_path():
    """Get path to bundled OpenStudio-HPXML."""
    # After extraction, the actual path is nested
    actual_path = OPENSTUDIO_HPXML_DIR / "OpenStudio-HPXML"
    if actual_path.exists():
        return str(actual_path)
    elif OPENSTUDIO_HPXML_DIR.exists():
        return str(OPENSTUDIO_HPXML_DIR)
    return None


def get_openstudio_python_path():
    """Get path to OpenStudio Python bindings."""
    # Check bundled OpenStudio first
    bundled_py_path = OPENSTUDIO_DIR / "lib" / "python"
    if bundled_py_path.exists():
        return str(bundled_py_path)
    
    # Check if bindings are already available
    try:
        import openstudio
        return None  # Already in Python path
    except ImportError:
        pass
    
    # Check common system locations
    system = platform.system()
    if system == "Linux":
        paths = [
            Path("/usr/local/lib/python3.12/dist-packages/"),
            Path("/usr/local/lib/python3.12/site-packages/"),
        ]
    elif system == "Windows":
        paths = [
            Path("C:/openstudio-3.9.0/lib/python"),
        ]
    else:  # macOS
        paths = [
            Path("/usr/local/lib/python3.12/site-packages/"),
        ]
    
    for path in paths:
        if path.exists() and (path / "openstudio").exists():
            return str(path)
    
    return None


# Configuration helper
def get_default_config():
    """Get default configuration with bundled paths."""
    config = {
        "hpxml_os_path": get_openstudio_hpxml_path() or "",
        "openstudio_binary": get_openstudio_path() or "openstudio",
    }
    
    # Add Python path if needed
    py_path = get_openstudio_python_path()
    if py_path:
        config["openstudio_python_path"] = py_path
    
    return config


if __name__ == "__main__":
    # Manual installation
    print("Installing h2k-hpxml dependencies...")
    install_openstudio_hpxml(force=True)
    install_openstudio(force=True)
    print("\nInstallation complete!")
    print(f"OpenStudio-HPXML: {get_openstudio_hpxml_path()}")
    print(f"OpenStudio: {get_openstudio_path()}")