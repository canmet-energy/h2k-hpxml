#!/usr/bin/env python3
"""
H2K-HPXML Installation and Test Helper

This script guides users through installation options and runs tests.
Supports both pip and uv installation methods.
"""

import os
import sys
import subprocess
import platform


def run_command(cmd, timeout=60):
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                              text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_uv_available():
    """Check if uv is available."""
    success, _, _ = run_command("uv --version")
    return success


def check_python_pip():
    """Check if Python and pip are available."""
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    python_ok, _, _ = run_command(f"{python_cmd} --version")
    pip_ok, _, _ = run_command(f"{python_cmd} -m pip --version")
    return python_ok and pip_ok, python_cmd


def install_uv():
    """Guide user through uv installation."""
    print("\n🚀 Installing uv (recommended)")
    print("=" * 40)
    
    if platform.system() == "Windows":
        cmd = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        print("Run this command in PowerShell:")
        print(f"  {cmd}")
    else:
        cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        print("Run this command:")
        print(f"  {cmd}")
    
    print("\nOr install with pip:")
    print("  pip install uv")
    
    input("\nPress Enter after installing uv...")
    
    if check_uv_available():
        print("✅ uv installed successfully!")
        return True
    else:
        print("❌ uv installation failed or not in PATH")
        return False


def install_with_uv():
    """Install H2K-HPXML with uv."""
    print("\n📦 Installing H2K-HPXML with uv")
    print("=" * 40)
    
    print("Choose installation type:")
    print("1. New project (creates isolated environment) - RECOMMENDED")
    print("2. Add to existing project")  
    print("3. Global tool installation")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        project_name = input("Project name (default: h2k-project): ").strip() or "h2k-project"
        print(f"\nCreating project '{project_name}'...")
        
        commands = [
            f"uv init {project_name}",
            f"cd {project_name}",
            "uv add h2k-hpxml"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            success, stdout, stderr = run_command(cmd)
            if not success:
                print(f"❌ Failed: {cmd}")
                print(f"Error: {stderr}")
                return False
        
        print(f"✅ Project created! Run: cd {project_name}")
        return True
        
    elif choice == "2":
        print("Adding to current directory...")
        success, stdout, stderr = run_command("uv add h2k-hpxml")
        if success:
            print("✅ Added to project!")
            return True
        else:
            print(f"❌ Failed: {stderr}")
            return False
            
    elif choice == "3":
        print("Installing as global tool...")
        success, stdout, stderr = run_command("uv tool install h2k-hpxml")
        if success:
            print("✅ Installed globally!")
            print("You can now use h2k2hpxml and h2k-deps directly")
            return True
        else:
            print(f"❌ Failed: {stderr}")
            return False
    else:
        print("Invalid choice")
        return False


def install_with_pip():
    """Install H2K-HPXML with pip."""
    print("\n📦 Installing H2K-HPXML with pip")
    print("=" * 40)
    
    python_available, python_cmd = check_python_pip()
    if not python_available:
        print("❌ Python or pip not available")
        return False
    
    print("Installing h2k-hpxml...")
    success, stdout, stderr = run_command(f"{python_cmd} -m pip install h2k-hpxml")
    
    if success:
        print("✅ Installed with pip!")
        return True
    else:
        print(f"❌ Installation failed: {stderr}")
        return False


def setup_dependencies():
    """Setup OpenStudio and OpenStudio-HPXML dependencies."""
    print("\n🔧 Setting up dependencies")
    print("=" * 40)
    
    # Determine command prefix
    if check_uv_available():
        # Check if h2k-hpxml is available via uv
        success, _, _ = run_command("uv run h2k-deps --help")
        if success:
            cmd_prefix = "uv run "
        else:
            cmd_prefix = ""
    else:
        cmd_prefix = ""
    
    # Setup configuration
    print("Setting up configuration...")
    success, stdout, stderr = run_command(f"{cmd_prefix}h2k-deps --setup", timeout=120)
    
    if not success:
        print(f"❌ Setup failed: {stderr}")
        return False
    
    # Auto-install dependencies
    print("\nInstalling OpenStudio and OpenStudio-HPXML...")
    print("⚠️  This may take several minutes and require admin privileges on some systems")
    
    success, stdout, stderr = run_command(f"{cmd_prefix}h2k-deps --auto-install", timeout=600)
    
    if success:
        print("✅ Dependencies installed!")
        return True
    else:
        print(f"❌ Dependency installation failed: {stderr}")
        print("\nYou can:")
        print("- Try manual setup with h2k-deps --setup")
        print("- Use Docker containers (no local dependencies needed)")
        return False


def run_tests():
    """Run installation tests."""
    print("\n🧪 Running tests")
    print("=" * 40)
    
    # Try to download and run smart test
    success, _, _ = run_command("curl -O https://raw.githubusercontent.com/canmet-energy/h2k-hpxml/main/smart_test.py")
    
    if success:
        print("Running comprehensive test...")
        if check_uv_available():
            success, stdout, stderr = run_command("uv run python smart_test.py")
        else:
            python_cmd = "python" if platform.system() == "Windows" else "python3"
            success, stdout, stderr = run_command(f"{python_cmd} smart_test.py")
        
        print(stdout)
        if stderr:
            print(stderr)
        
        return success
    else:
        # Fallback to simple test
        print("Running simple test...")
        if check_uv_available():
            success, stdout, stderr = run_command("uv run h2k-deps --check-only")
        else:
            success, stdout, stderr = run_command("h2k-deps --check-only")
        
        print(stdout)
        if stderr:
            print(stderr)
        
        return success


def main():
    """Main installation and test workflow."""
    print("H2K-HPXML Installation & Test Helper")
    print("=" * 50)
    print("This script will guide you through installing and testing H2K-HPXML")
    print()
    
    # Check what's available
    uv_available = check_uv_available()
    python_available, python_cmd = check_python_pip()
    
    print("Available installation methods:")
    if uv_available:
        print("✅ uv (fast, modern) - RECOMMENDED")
    else:
        print("❌ uv (not installed)")
        
    if python_available:
        print("✅ pip (traditional)")
    else:
        print("❌ pip (not available)")
    
    if not uv_available and not python_available:
        print("\n❌ No installation method available!")
        print("Please install Python or uv first.")
        return False
    
    print("\nRecommended installation method:")
    if uv_available:
        print("📦 uv (10-100x faster, better isolation)")
        default_choice = "uv"
    else:
        print("📦 pip (traditional method)")
        default_choice = "pip"
    
    # Installation choice
    print(f"\nInstall with {default_choice}? (y/N):", end=" ")
    choice = input().strip().lower()
    
    if choice in ['y', 'yes']:
        install_method = default_choice
    else:
        if uv_available and python_available:
            print("\nChoose installation method:")
            print("1. uv (recommended)")
            print("2. pip")
            method_choice = input("Enter choice (1-2): ").strip()
            install_method = "uv" if method_choice == "1" else "pip"
        elif uv_available:
            install_method = "uv"
        else:
            install_method = "pip"
    
    # Install uv if needed but not available
    if install_method == "uv" and not uv_available:
        if not install_uv():
            print("Falling back to pip...")
            install_method = "pip"
    
    # Perform installation
    print(f"\n🎯 Installing with {install_method}")
    
    if install_method == "uv":
        if not install_with_uv():
            return False
    else:
        if not install_with_pip():
            return False
    
    # Setup dependencies
    if not setup_dependencies():
        print("\n⚠️  Installation succeeded but dependencies failed")
        print("You can retry with: h2k-deps --setup")
        return False
    
    # Run tests
    if run_tests():
        print("\n🎉 Installation and testing completed successfully!")
        print("\nNext steps:")
        if install_method == "uv":
            print("- Convert H2K files: uv run h2k2hpxml your_file.h2k")
            print("- Get help: uv run h2k2hpxml --help")
        else:
            print("- Convert H2K files: h2k2hpxml your_file.h2k")
            print("- Get help: h2k2hpxml --help")
        print("- Read documentation: https://github.com/canmet-energy/h2k-hpxml")
        return True
    else:
        print("\n❌ Installation succeeded but tests failed")
        print("Check the output above for specific issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)