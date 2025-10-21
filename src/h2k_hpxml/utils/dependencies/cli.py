#!/usr/bin/env python3
"""
CLI commands for dependency management.

Provides command-line interface for os-setup tool.
"""

import click

from .manager import DependencyManager


def validate_dependencies(
    interactive=True,
    skip_deps=False,
    check_only=False,
    install_quiet=False,
    hpxml_path=None,
    openstudio_path=None,
):
    """
    Convenience function to validate h2k_hpxml dependencies.

    Args:
        interactive (bool): Whether to prompt user for installation choices.
            Default: True
        skip_deps (bool): Skip all dependency validation. Default: False
        check_only (bool): Only check dependencies, don't install.
            Default: False
        install_quiet (bool): Automatically install missing dependencies.
            Default: False
        hpxml_path (str|Path): Custom OpenStudio-HPXML installation path.
            Default: None (use environment variables or defaults)
        openstudio_path (str|Path): Custom OpenStudio installation path.
            Default: None (use environment variables or defaults)

    Returns:
        bool: True if all dependencies are satisfied or successfully
            installed, False otherwise

    Example:
        >>> # Interactive validation with prompts
        >>> validate_dependencies()

        >>> # Automatic installation with custom paths
        >>> validate_dependencies(install_quiet=True, interactive=False, hpxml_path="/custom/hpxml")

        >>> # Check only, no installation
        >>> validate_dependencies(check_only=True)
    """
    manager = DependencyManager(
        interactive=interactive,
        skip_deps=skip_deps,
        install_quiet=install_quiet,
        hpxml_path=hpxml_path,
        openstudio_path=openstudio_path,
    )

    if check_only:
        return manager.check_only()
    else:
        return manager.validate_all()


def test_quick_installation():
    """Quick installation test - basic verification."""
    import subprocess

    click.echo("🧪 H2K-HPXML Quick Installation Test")
    click.echo("=" * 40)

    tests = []

    # Test 1: Package import
    try:
        import h2k_hpxml
        tests.append(("Package Import", True, "✅"))
    except ImportError as e:
        tests.append(("Package Import", False, f"❌ {e}"))

    # Test 2: CLI tools
    try:
        from ..cli.convert import main as convert_main
        tests.append(("CLI Tools", True, "✅"))
    except ImportError as e:
        tests.append(("CLI Tools", False, f"❌ {e}"))

    # Test 3: Dependencies
    try:
        manager = DependencyManager()
        deps_ok = manager.check_only()
        if deps_ok:
            tests.append(("Dependencies", True, "✅"))
        else:
            tests.append(("Dependencies", False, "❌ Missing dependencies"))
    except Exception as e:
        tests.append(("Dependencies", False, f"❌ {e}"))

    # Test 4: Configuration
    try:
        from ..config.manager import ConfigManager
        config = ConfigManager()
        if config.openstudio_binary and config.hpxml_os_path:
            tests.append(("Configuration", True, "✅"))
        else:
            tests.append(("Configuration", False, "❌ Missing paths"))
    except Exception as e:
        tests.append(("Configuration", False, f"❌ {e}"))

    # Report results
    all_passed = True
    for test_name, passed, message in tests:
        click.echo(f"{test_name:15}: {message}")
        if not passed:
            all_passed = False

    click.echo("\n" + "=" * 40)
    if all_passed:
        click.echo("🎉 All quick tests passed!")
        return True
    else:
        click.echo("⚠️  Some tests failed. Run 'os-setup --setup' or 'os-setup --auto-install'")
        return False


def test_smart_installation():
    """Smart installation test - detects uv vs pip automatically."""
    import subprocess
    import shutil
    from pathlib import Path

    click.echo("🧪 H2K-HPXML Smart Installation Test")
    click.echo("=" * 40)

    # Detect runner
    runner = "python"

    # Check if uv is available
    if shutil.which("uv"):
        try:
            # Check if we can run h2k-hpxml with uv
            result = subprocess.run(["uv", "run", "python", "-c", "import h2k_hpxml"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                runner = "uv"
        except:
            pass

    click.echo(f"🔍 Detected runner: {runner}")

    # Run quick test first
    if not test_quick_installation():
        return False

    # Test CLI commands with detected runner
    click.echo("\n📋 Testing CLI Commands")
    click.echo("-" * 20)

    commands = [
        ("h2k-hpxml --help", "Main CLI help"),
        ("os-setup --check-only", "Dependencies check"),
        ("h2k-resilience --help", "Resilience CLI help")
    ]

    all_passed = True
    for cmd, description in commands:
        try:
            if runner == "uv" and not cmd.startswith("python"):
                full_cmd = ["uv", "run"] + cmd.split()
            else:
                full_cmd = cmd.split()

            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                click.echo(f"✅ {description}")
            else:
                click.echo(f"❌ {description} (exit code {result.returncode})")
                all_passed = False
        except Exception as e:
            click.echo(f"❌ {description} ({e})")
            all_passed = False

    click.echo("\n" + "=" * 40)
    if all_passed:
        click.echo("🎉 Smart installation test passed!")
        click.echo(f"📦 Using {runner} runner")
        return True
    else:
        click.echo("⚠️  Some CLI tests failed.")
        return False


def test_comprehensive_installation():
    """Comprehensive installation test with actual conversion."""
    import tempfile
    import shutil
    from pathlib import Path

    click.echo("🧪 H2K-HPXML Comprehensive Installation Test")
    click.echo("=" * 50)

    # Run smart test first
    if not test_smart_installation():
        click.echo("❌ Smart test failed, skipping conversion test")
        return False

    click.echo("\n🔄 Testing H2K to HPXML Conversion")
    click.echo("-" * 30)

    try:
        # Get example files
        from .. import get_example_files
        examples = get_example_files()

        if not examples:
            click.echo("❌ No example files found")
            return False

        # Use first example
        example_file = examples[0]
        click.echo(f"📁 Using example: {example_file.name}")

        # Create temp directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "test_output.xml"

            # Test conversion using API
            from ..api import convert_file

            result = convert_file(
                h2k_file=str(example_file),
                output_file=str(output_file),
                run_simulation=False  # Skip simulation for speed
            )

            if result.get("success", False):
                click.echo("✅ H2K to HPXML conversion successful")

                # Check output file
                if output_file.exists() and output_file.stat().st_size > 0:
                    size_kb = output_file.stat().st_size // 1024
                    click.echo(f"✅ Output HPXML file created ({size_kb} KB)")

                    # Basic validation - check if it's valid XML
                    try:
                        import xml.etree.ElementTree as ET
                        ET.parse(output_file)
                        click.echo("✅ Output XML is well-formed")
                        return True
                    except ET.ParseError as e:
                        click.echo(f"❌ Output XML is malformed: {e}")
                        return False
                else:
                    click.echo("❌ Output file not created or empty")
                    return False
            else:
                click.echo(f"❌ Conversion failed: {result.get('error', 'Unknown error')}")
                return False

    except Exception as e:
        click.echo(f"❌ Comprehensive test failed: {e}")
        return False


def main():
    """Main entry point for standalone dependency checking."""
    import os
    # Prevent auto-install when running os-setup CLI
    os.environ['H2K_SKIP_AUTO_INSTALL'] = '1'
    
    import argparse

    parser = argparse.ArgumentParser(
        description="Install and manage OpenStudio, EnergyPlus, and OpenStudio-HPXML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Check dependencies and prompt to install if missing
  %(prog)s --check-only           # Only check dependencies, don't install
  %(prog)s --install-quiet        # Install missing dependencies and setup PATH (no prompts)
  %(prog)s --add-to-path          # Add h2k-hpxml to PATH and clean up old entries (Windows only)
  %(prog)s --setup                # Set up user configuration from template
  %(prog)s --update-config        # Update all config files with detected paths
  %(prog)s --update-config --global   # Update user config files only
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
  %(prog)s --test-quick            # Quick installation verification
  %(prog)s --test-installation     # Smart installation test (auto-detects uv vs pip)
  %(prog)s --test-comprehensive    # Comprehensive test with conversion
        """,
    )

    parser.add_argument(
        "--check-only", action="store_true", help="Only check dependencies, don't install"
    )
    parser.add_argument(
        "--install-quiet", action="store_true", help="Install missing dependencies and setup PATH without prompts"
    )
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency validation")
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall OpenStudio and OpenStudio-HPXML dependencies",
    )
    parser.add_argument(
        "--setup", action="store_true", help="Set up user configuration from templates"
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update configuration file with detected dependency paths",
    )
    parser.add_argument(
        "--global",
        dest="update_global",
        action="store_true",
        help="Update user configuration files only (use with --update-config)",
    )
    parser.add_argument(
        "--local",
        dest="update_local",
        action="store_true",
        help="Update project configuration files only (use with --update-config)",
    )
    parser.add_argument(
        "--hpxml-path", type=str, metavar="PATH", help="Custom OpenStudio-HPXML installation path"
    )
    parser.add_argument(
        "--openstudio-path", type=str, metavar="PATH", help="Custom OpenStudio installation path"
    )
    parser.add_argument(
        "--add-to-path",
        action="store_true",
        help="Add h2k-hpxml to Windows PATH and clean up old entries (Windows only)"
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Automatically install missing dependencies without prompts"
    )
    parser.add_argument(
        "--test-installation",
        action="store_true",
        help="Run smart installation test (auto-detects uv vs pip)"
    )
    parser.add_argument(
        "--test-quick",
        action="store_true",
        help="Run quick installation verification"
    )
    parser.add_argument(
        "--test-comprehensive",
        action="store_true",
        help="Run comprehensive installation test with conversion"
    )

    args = parser.parse_args()

    # Handle add-to-path option (Windows only)
    if args.add_to_path:
        import platform
        if platform.system() != 'Windows':
            click.echo("ℹ️  --add-to-path is for Windows only.")
            click.echo("On Linux/Mac, h2k-hpxml should already be accessible after installation.")
            return

        # Use the integrated PATH setup from DependencyManager
        manager = DependencyManager(interactive=False)
        manager._offer_windows_path_setup()
        return

    # Handle test options
    elif args.test_quick:
        success = test_quick_installation()
        import sys
        sys.exit(0 if success else 1)
    elif args.test_installation:
        success = test_smart_installation()
        import sys
        sys.exit(0 if success else 1)
    elif args.test_comprehensive:
        success = test_comprehensive_installation()
        import sys
        sys.exit(0 if success else 1)

    # Handle setup option
    elif args.setup:
        manager = DependencyManager(
            interactive=True,  # Setup is always interactive
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
        )
        success = manager.setup_user_config()
        if success:
            click.echo("✅ User configuration setup completed!")
        else:
            click.echo("❌ Failed to setup user configuration")
    # Handle uninstall option
    elif args.uninstall:
        manager = DependencyManager(
            interactive=True,  # Uninstall is always interactive for safety
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
        )
        success = manager.uninstall_dependencies()
    # Handle update-config option
    elif args.update_config:
        manager = DependencyManager(
            interactive=False, hpxml_path=args.hpxml_path, openstudio_path=args.openstudio_path
        )
        click.echo("🔄 Updating configuration with detected dependency paths...")

        # Determine update scope
        user_only = args.update_global and not args.update_local
        if args.update_global and args.update_local:
            click.echo("⚠️  Both --global and --local specified, updating all configs")
            user_only = False
        elif args.update_local:
            click.echo(
                "ℹ️  --local specified, but user config takes priority. Consider using --global for user configs."
            )
            user_only = False

        success = manager._update_config_file(user_only=user_only)
        if success:
            click.echo("✅ Configuration file updated successfully!")
        else:
            click.echo("❌ Failed to update configuration file")
    else:
        # Determine mode: check-only, install-quiet, or interactive (default)
        if args.check_only:
            success = validate_dependencies(
                check_only=True,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )
        elif args.install_quiet:
            success = validate_dependencies(
                interactive=False,
                install_quiet=True,
                skip_deps=args.skip_deps,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )
        else:
            # Default interactive mode
            success = validate_dependencies(
                interactive=True,
                skip_deps=args.skip_deps,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )

    import sys

    sys.exit(0 if success else 1)

# Compatibility functions for legacy installer.py imports
