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
from pathlib import Path
from urllib.request import urlretrieve
import ssl
import urllib.error

# Package-relative paths
PACKAGE_DIR = Path(__file__).parent
DEPS_DIR = PACKAGE_DIR / "_deps"
OPENSTUDIO_HPXML_DIR = DEPS_DIR / "OpenStudio-HPXML"
OPENSTUDIO_DIR = DEPS_DIR / "openstudio"

# Dependency URLs
OPENSTUDIO_HPXML_URL = "https://github.com/NREL/OpenStudio-HPXML/releases/download/v1.9.1/OpenStudio-HPXML-v1.9.1.zip"

OPENSTUDIO_URLS = {
    "Windows": "https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+c77fbb9569-Windows.exe",
    "Linux": "https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+c77fbb9569-Ubuntu-22.04-x86_64.tar.gz",
    "Darwin": "https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+c77fbb9569-Darwin-x86_64.tar.gz"
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
    zip_path = DEPS_DIR / "OpenStudio-HPXML.zip"
    if not download_file(OPENSTUDIO_HPXML_URL, zip_path, "OpenStudio-HPXML v1.9.1"):
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
    if system not in OPENSTUDIO_URLS:
        print(f"Unsupported platform: {system}")
        return False
    
    print(f"Installing OpenStudio for {system}...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    OPENSTUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    url = OPENSTUDIO_URLS[system]
    
    if system == "Windows":
        # Windows .exe installer - we can try to extract it with 7zip or similar
        # For now, download and provide instructions
        exe_path = DEPS_DIR / "OpenStudio-installer.exe"
        print("  Note: Windows installer requires extraction")
        if not download_file(url, exe_path, f"OpenStudio 3.9.0 for Windows"):
            return False
        print(f"  Downloaded to: {exe_path}")
        print(f"  Please extract to: {OPENSTUDIO_DIR}")
        print("  You can use 7-Zip or run: msiexec /a {exe_path} /qb TARGETDIR={OPENSTUDIO_DIR}")
        return False
        
    else:  # Linux/Mac - tar.gz files
        tar_path = DEPS_DIR / "openstudio.tar.gz"
        if not download_file(url, tar_path, f"OpenStudio 3.9.0 for {system}"):
            return False
        
        try:
            # Extract tar.gz
            print(f"  Extracting to {OPENSTUDIO_DIR}...")
            with tarfile.open(tar_path, 'r:gz') as tar:
                # The tar contains OpenStudio-3.9.0+hash/ folder, extract contents
                tar.extractall(DEPS_DIR)
            
            # Find the extracted folder (it has a hash in the name)
            extracted_dirs = [d for d in DEPS_DIR.iterdir() 
                            if d.is_dir() and d.name.startswith("OpenStudio-3.9")]
            
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
    
    # First check for bundled OpenStudio in _deps
    # The structure is different after extraction: usr/local/openstudio-3.9.0/bin/openstudio
    bundled_paths = [
        OPENSTUDIO_DIR / "usr" / "local" / "openstudio-3.9.0" / "bin" / "openstudio",
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