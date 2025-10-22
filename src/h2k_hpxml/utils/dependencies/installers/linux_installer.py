#!/usr/bin/env python3
"""
OpenStudio Linux installer.

Handles Linux-specific installation with smart detection and multiple methods.
"""

import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import click

from .base import BaseInstaller
from ..download_utils import download_file


class LinuxInstaller(BaseInstaller):
    """Linux-specific OpenStudio installer with smart detection."""

    OPENSTUDIO_BASE_URL = "https://github.com/NREL/OpenStudio/releases/download"

    def __init__(self, required_version, build_hash, default_path, interactive=True, install_quiet=False):
        """Initialize Linux installer.

        Args:
            required_version (str): Required OpenStudio version (e.g., "3.9.0")
            build_hash (str): OpenStudio build hash (e.g., "bb29e94a73")
            default_path (Path): Default installation path (user-space)
            interactive (bool): Whether to prompt user for input
            install_quiet (bool): Whether to suppress output
        """
        super().__init__(interactive, install_quiet)
        self.required_version = required_version
        self.build_hash = build_hash
        self.default_path = Path(default_path)

    def install(self, target_path=None):
        """Install OpenStudio on Linux using smart detection.

        Args:
            target_path (Path): Installation directory (auto-determined if None)

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        try:
            # 1. Check if running in container/CI (libraries usually pre-installed)
            if os.environ.get("DOCKER_BUILD_CONTEXT") or os.environ.get("CI"):
                click.echo("🐳 Container environment detected, using user-space installation")
                return self._install_openstudio_tarball_user()

            # 2. Check for required libraries
            missing_libs = self._check_required_libraries()

            if missing_libs:
                click.echo(f"⚠️  Missing required libraries: {', '.join(missing_libs)}")

                # Try to install libraries if sudo is available
                if self._can_use_sudo():
                    if self.interactive:
                        if click.confirm("Install missing system libraries (requires sudo)?"):
                            if self._install_system_libraries(missing_libs):
                                return self._install_openstudio_tarball_user()
                        else:
                            click.echo("❌ Cannot install OpenStudio without required libraries")
                            return False
                    else:
                        # Non-interactive mode - try to install libraries
                        click.echo("🔧 Installing required libraries...")
                        if self._install_system_libraries(missing_libs):
                            return self._install_openstudio_tarball_user()
                        else:
                            click.echo("❌ Failed to install required libraries")
                            return False
                else:
                    click.echo("❌ sudo not available and missing required libraries")
                    click.echo("Please install manually:", err=True)
                    click.echo(f"  sudo apt install {' '.join(missing_libs)}", err=True)
                    return False

            # 3. Libraries present or installed, proceed with user-space installation
            click.echo("✅ All required libraries found")
            return self._install_openstudio_tarball_user()

        except Exception as e:
            click.echo(f"❌ Linux OpenStudio installation failed: {e}")
            return False

    def uninstall(self, install_path=None):
        """Uninstall OpenStudio from Linux.

        Args:
            install_path (Path): Installation directory to remove (auto-detected if None)

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            # Check what installation method was actually used
            # Priority: tarball installations (user-space) over system packages
            if self.default_path.exists():
                # We have a tarball installation
                return self._uninstall_openstudio_tarball()
            elif self._is_debian_based():
                # Check for system packages
                return self._uninstall_openstudio_deb()
            else:
                # Try tarball cleanup anyway
                return self._uninstall_openstudio_tarball()
        except Exception as e:
            click.echo(f"❌ Linux OpenStudio uninstall failed: {e}")
            return False

    def validate(self):
        """Validate that OpenStudio is properly installed.

        Returns:
            bool: True if installation is valid, False otherwise
        """
        # Check user-space installation
        binary_path = self.default_path / "bin" / "openstudio"
        if binary_path.exists():
            return True

        # Check system-wide installations
        system_paths = [
            Path("/usr/local/openstudio/bin/openstudio"),
            Path("/opt/openstudio/bin/openstudio"),
        ]

        for path in system_paths:
            if path.exists():
                return True

        # Check if in PATH
        return shutil.which("openstudio") is not None

    def _install_openstudio_tarball_user(self):
        """Install OpenStudio from tarball to user-space directory.

        Installs to ~/.local/share/OpenStudio-{version}/ without requiring sudo.

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        tarball_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.required_version}/"
            f"OpenStudio-{self.required_version}+"
            f"{self.build_hash}-Ubuntu-22.04-x86_64.tar.gz"
        )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tarball_path = os.path.join(temp_dir, "openstudio.tar.gz")

                if not download_file(tarball_url, tarball_path, "OpenStudio tarball"):
                    raise Exception("Download failed")

                # Install to user-space directory
                install_dir = self.default_path

                # Remove existing installation if present
                if install_dir.exists():
                    click.echo(f"Removing existing installation: {install_dir}")
                    shutil.rmtree(install_dir)

                # Create installation directory
                install_dir.parent.mkdir(parents=True, exist_ok=True)

                click.echo(f"Extracting to {install_dir}...")
                # First extract to a temp location to handle the nested structure
                temp_extract = os.path.join(temp_dir, "extracted")
                with tarfile.open(tarball_path, "r:gz") as tar:
                    tar.extractall(temp_extract)

                # Find the actual OpenStudio directory (should be usr/local/openstudio-3.9.0)
                # The tarball structure is: OpenStudio-3.9.0+.../usr/local/openstudio-3.9.0/
                extracted_root = None
                for root, dirs, files in os.walk(temp_extract):
                    if "bin" in dirs and os.path.exists(os.path.join(root, "bin", "openstudio")):
                        extracted_root = root
                        break

                if not extracted_root:
                    raise Exception("Could not find OpenStudio binaries in extracted archive")

                # Move the contents to the final location
                shutil.move(extracted_root, install_dir)

                click.echo(f"✅ OpenStudio installed successfully to: {install_dir}")

                # Add to PATH (creates symlinks and updates shell profiles)
                self._add_to_path_linux(install_dir)

                return True

        except Exception as e:
            click.echo(f"❌ OpenStudio user-space installation failed: {e}")
            return False

    def _install_openstudio_deb(self):
        """Install OpenStudio using .deb package.

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        deb_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.required_version}/"
            f"OpenStudio-{self.required_version}+"
            f"{self.build_hash}-Ubuntu-22.04-x86_64.deb"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            deb_path = os.path.join(temp_dir, "openstudio.deb")

            click.echo("Downloading OpenStudio .deb package...")
            if not download_file(deb_url, deb_path, "OpenStudio .deb package"):
                raise Exception("Download failed")

            click.echo("Installing OpenStudio (requires sudo)...")
            subprocess.run(["sudo", "dpkg", "-i", deb_path], check=True)

            # Install dependencies if needed
            subprocess.run(["sudo", "apt-get", "install", "-f", "-y"], check=False)

            click.echo("✅ OpenStudio installed successfully")
            return True

    def _install_openstudio_tarball(self):
        """Install OpenStudio from tarball to system-wide location.

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        tarball_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.required_version}/"
            f"OpenStudio-{self.required_version}+"
            f"{self.build_hash}-Ubuntu-22.04-x86_64.tar.gz"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            tarball_path = os.path.join(temp_dir, "openstudio.tar.gz")

            if not download_file(tarball_url, tarball_path, "OpenStudio tarball"):
                raise Exception("Download failed")

            # Extract to /usr/local/openstudio
            install_dir = Path("/usr/local/openstudio")

            click.echo(f"Extracting to {install_dir} (requires sudo)...")
            subprocess.run(["sudo", "mkdir", "-p", str(install_dir)], check=True)
            subprocess.run(
                [
                    "sudo",
                    "tar",
                    "-xzf",
                    tarball_path,
                    "-C",
                    str(install_dir),
                    "--strip-components=1",
                ],
                check=True,
            )

            # Create symlink to bin directory
            bin_link = Path("/usr/local/bin/openstudio")
            openstudio_bin = install_dir / "bin" / "openstudio"

            if openstudio_bin.exists():
                subprocess.run(
                    ["sudo", "ln", "-sf", str(openstudio_bin), str(bin_link)], check=False
                )

            click.echo("✅ OpenStudio installed successfully")
            return True

    def _uninstall_openstudio_deb(self):
        """Uninstall OpenStudio .deb package on Debian-based systems.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            # Find OpenStudio packages
            result = subprocess.run(["dpkg", "-l", "*openstudio*"], capture_output=True, text=True)

            if result.returncode != 0 or "openstudio" not in result.stdout.lower():
                click.echo("ℹ️  No OpenStudio .deb packages found.")
                return True

            # Extract package names
            lines = result.stdout.split("\n")
            packages = []
            for line in lines:
                if "ii" in line and "openstudio" in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append(parts[1])

            if not packages:
                click.echo("ℹ️  No installed OpenStudio packages found.")
                return True

            # Uninstall packages
            for package in packages:
                click.echo(f"Removing package: {package}")
                subprocess.run(["sudo", "dpkg", "-r", package], check=True)

            click.echo("✅ OpenStudio .deb packages removed successfully")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to remove OpenStudio packages: {e}")
            return False

    def _uninstall_openstudio_tarball(self):
        """Uninstall OpenStudio installed from tarball.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        # Check both system and user installation paths
        install_paths = [
            # System-wide installations
            Path("/usr/local/openstudio"),
            Path("/opt/openstudio"),
            Path("/usr/local/bin/openstudio"),
            # User installations (our preferred method)
            self.default_path,
        ]

        # Also check for symlinks in ~/.local/bin
        local_bin = Path.home() / ".local" / "bin" / "openstudio"
        if local_bin.exists() or local_bin.is_symlink():
            install_paths.append(local_bin)

        removed_any = False

        for path in install_paths:
            if path.exists() or path.is_symlink():
                try:
                    if path.is_file() or path.is_symlink():
                        # User files don't need sudo
                        if str(path).startswith(str(Path.home())):
                            path.unlink()
                        else:
                            subprocess.run(["sudo", "rm", "-f", str(path)], check=True)
                        click.echo(f"Removed file: {path}")
                    else:
                        # User directories don't need sudo
                        if str(path).startswith(str(Path.home())):
                            shutil.rmtree(path)
                        else:
                            subprocess.run(["sudo", "rm", "-rf", str(path)], check=True)
                        click.echo(f"Removed directory: {path}")
                    removed_any = True
                except (subprocess.CalledProcessError, OSError) as e:
                    click.echo(f"⚠️  Failed to remove: {path} - {e}")

        if removed_any:
            click.echo("✅ OpenStudio tarball installation removed")
        else:
            click.echo("ℹ️  No OpenStudio tarball installation found")

        return True

    def _check_required_libraries(self):
        """Check for required OpenStudio runtime libraries on Linux.

        Returns:
            list: List of missing package names that need to be installed
        """
        required_libs = {
            'libgomp.so.1': 'libgomp1',
            'libX11.so.6': 'libx11-6',
            'libXext.so.6': 'libxext6',
            'libgfortran.so.5': 'libgfortran5',
            'libssl.so.3': 'libssl3'
        }

        missing = []
        for lib, package in required_libs.items():
            if not self._find_library(lib):
                missing.append(package)

        return missing

    def _find_library(self, lib_name):
        """Find a shared library on the system.

        Args:
            lib_name (str): Name of the library file (e.g., 'libgomp.so.1')

        Returns:
            bool: True if library is found, False otherwise
        """
        try:
            # Method 1: Use ldconfig to check dynamic linker cache
            result = subprocess.run(
                ['ldconfig', '-p'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and lib_name in result.stdout:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Method 2: Check common library paths
        common_paths = [
            '/lib/x86_64-linux-gnu',
            '/usr/lib/x86_64-linux-gnu',
            '/lib64',
            '/usr/lib64',
            '/lib',
            '/usr/lib'
        ]

        for path in common_paths:
            lib_path = Path(path) / lib_name
            if lib_path.exists():
                return True

        return False

    def _install_system_libraries(self, missing_packages):
        """Install missing system libraries using apt.

        Args:
            missing_packages (list): List of package names to install

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        if not missing_packages:
            return True

        try:
            click.echo(f"Installing system libraries: {' '.join(missing_packages)}")

            # Update package list first
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)

            # Install packages
            cmd = ['sudo', 'apt-get', 'install', '-y'] + missing_packages
            subprocess.run(cmd, check=True)

            click.echo("✅ System libraries installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to install system libraries: {e}")
            return False
        except FileNotFoundError:
            click.echo("❌ apt-get not found (not a Debian-based system)")
            return False

    def _can_use_sudo(self):
        """Check if sudo is available and can be used.

        Returns:
            bool: True if sudo is available, False otherwise
        """
        try:
            # Check if sudo exists
            result = subprocess.run(
                ['which', 'sudo'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False

            # Test if we can use sudo (without actually running a command)
            result = subprocess.run(
                ['sudo', '-n', 'true'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _is_debian_based(self):
        """Check if running on Debian-based system.

        Returns:
            bool: True if Debian-based, False otherwise
        """
        return os.path.exists("/etc/debian_version") or shutil.which("apt-get") is not None

    def _add_to_path_linux(self, install_dir):
        """Configure OpenStudio and EnergyPlus environment for Linux.

        Creates symlinks in ~/.local/bin/ and updates shell profile files
        (.bashrc, .bash_profile, .zshrc, .profile) to:
        - Add ~/.local/bin to PATH (for openstudio and energyplus binaries)
        - Set RUBYLIB to OpenStudio Ruby bindings directory
        - Set ENERGYPLUS_EXE_PATH to EnergyPlus installation directory

        Args:
            install_dir: Path to OpenStudio installation directory

        Returns:
            bool: True if environment configuration successful, False otherwise
        """
        try:
            local_bin = Path.home() / ".local" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)

            # Create symlinks for OpenStudio
            openstudio_bin = install_dir / "bin" / "openstudio"
            openstudio_link = local_bin / "openstudio"

            # Create symlinks for EnergyPlus
            energyplus_bin = install_dir / "EnergyPlus" / "energyplus"
            energyplus_link = local_bin / "energyplus"

            links_created = []

            # Create OpenStudio symlink
            if openstudio_bin.exists():
                if openstudio_link.exists() or openstudio_link.is_symlink():
                    openstudio_link.unlink()
                openstudio_link.symlink_to(openstudio_bin)
                links_created.append(f"openstudio → {openstudio_bin}")

            # Create EnergyPlus symlink
            if energyplus_bin.exists():
                if energyplus_link.exists() or energyplus_link.is_symlink():
                    energyplus_link.unlink()
                energyplus_link.symlink_to(energyplus_bin)
                links_created.append(f"energyplus → {energyplus_bin}")

            if links_created:
                click.echo(f"✅ Created symlinks in {local_bin}:")
                for link in links_created:
                    click.echo(f"   • {link}")

            # Check if environment is already configured
            current_path = os.environ.get("PATH", "")
            if str(local_bin) in current_path and os.environ.get("RUBYLIB") and os.environ.get("ENERGYPLUS_EXE_PATH"):
                click.echo(f"✅ Environment variables already configured")
                return True

            # In interactive mode, ask user
            if self.interactive:
                if not click.confirm(f"\n🔧 Add {local_bin} to your PATH and set OpenStudio environment variables?"):
                    click.echo("⏭️  Skipped environment variable updates")
                    click.echo(f"📝 To manually configure, add these to your shell profile:")
                    click.echo(f'   export PATH="$HOME/.local/bin:$PATH"')
                    click.echo(f'   export RUBYLIB="{install_dir}/Ruby"')
                    click.echo(f'   export ENERGYPLUS_EXE_PATH="{install_dir}/EnergyPlus"')
                    return False

            # Update shell profile files
            click.echo("🔧 Updating shell profile files...")

            home = Path.home()
            profile_files = [
                home / ".bashrc",
                home / ".bash_profile",
                home / ".zshrc",
                home / ".profile"
            ]

            # Build environment variable exports
            # Use install_dir to determine OpenStudio base path
            openstudio_base = str(install_dir).replace(str(home), "$HOME")

            env_exports = f'''
# Added by os-setup for OpenStudio and EnergyPlus
export PATH="$HOME/.local/bin:$PATH"
export RUBYLIB="{openstudio_base}/Ruby"
export ENERGYPLUS_EXE_PATH="{openstudio_base}/EnergyPlus"
'''

            files_updated = []

            for profile_file in profile_files:
                if profile_file.exists():
                    # Read current content
                    content = profile_file.read_text()

                    # Check if exports already exist
                    if 'Added by os-setup for OpenStudio and EnergyPlus' in content:
                        continue

                    # Append environment variable exports
                    with open(profile_file, 'a') as f:
                        f.write(env_exports)
                    files_updated.append(str(profile_file))

            if files_updated:
                click.echo("✅ Updated shell profile files:")
                for file in files_updated:
                    click.echo(f"   • {file}")
                click.echo("\n⚠️  Note: Run 'source ~/.bashrc' (or your shell's profile) to apply changes")
                click.echo("   Or restart your terminal for environment variable changes to take effect")
                click.echo("\n📋 Environment variables configured:")
                click.echo(f"   • PATH (includes OpenStudio and EnergyPlus binaries)")
                click.echo(f"   • RUBYLIB (OpenStudio Ruby bindings)")
                click.echo(f"   • ENERGYPLUS_EXE_PATH (EnergyPlus location)")
            else:
                click.echo("ℹ️  Shell profiles already configured or not found")

            return True

        except Exception as e:
            click.echo(f"❌ Failed to update environment variables: {e}")
            click.echo(f"\n📝 You can manually add these to your shell profile:")
            click.echo(f'   export PATH="$HOME/.local/bin:$PATH"')
            click.echo(f'   export RUBYLIB="{install_dir}/Ruby"')
            click.echo(f'   export ENERGYPLUS_EXE_PATH="{install_dir}/EnergyPlus"')
            return False
