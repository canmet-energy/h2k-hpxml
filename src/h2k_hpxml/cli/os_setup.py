#!/usr/bin/env python3
"""
h2k-hpxml ``os-setup`` command.

A thin wrapper around the reusable ``osdep`` package. Generic install/validate/
uninstall is delegated to osdep (with h2k's pinned versions injected), while the
h2k-specific behaviors (writing the conversion config.ini and running a full
H2K->HPXML conversion as a smoke test) live here.
"""

import click
from osdep import DependencyManager
from osdep import validate_dependencies as _validate_dependencies
from osdep import verify_installation

from ..utils.dependencies._h2k_versions import H2K_CONFIG


def validate_dependencies(**kwargs):
    """validate_dependencies with h2k's pinned versions injected."""
    kwargs.setdefault("config", H2K_CONFIG)
    return _validate_dependencies(**kwargs)


# ---------------------------------------------------------------------------
# h2k-specific: user configuration setup (moved from DependencyManager)
# ---------------------------------------------------------------------------
def setup_user_config():
    """Set up the h2k-hpxml user configuration (config.ini) from the template."""
    from ..config.manager import ConfigManager

    click.echo("🔧 Setting up user configuration")
    try:
        temp_config = ConfigManager(auto_create=True)
        user_config_path = temp_config._get_user_config_path()
        user_config_path.mkdir(parents=True, exist_ok=True)

        user_config_file = user_config_path / "config.ini"

        template_name = "conversionconfig.template.ini"
        template_path = temp_config._find_template_file(template_name)

        if template_path and template_path.exists():
            # Copy template to user config, preserving comments (paths auto-detected at runtime)
            content = template_path.read_text(encoding="utf-8")
            user_config_file.write_text(content, encoding="utf-8")
            click.echo(f"✅ User configuration created from template at: {user_config_file}")
        else:
            temp_config._create_minimal_config(user_config_file)
            click.echo(f"✅ User configuration created (minimal) at: {user_config_file}")

        return True
    except Exception as e:
        click.echo(f"❌ Failed to setup user configuration: {e}")
        return False


# ---------------------------------------------------------------------------
# h2k-specific: installation verification tests
# ---------------------------------------------------------------------------
def test_quick_installation():
    """Quick installation test - basic verification."""
    import importlib.util

    click.echo("🧪 H2K-HPXML Quick Installation Test")
    click.echo("=" * 40)

    tests = []

    # Test 1: Package import
    try:
        if importlib.util.find_spec("h2k_hpxml") is not None:
            tests.append(("Package Import", True, "✅"))
        else:
            tests.append(("Package Import", False, "❌ Package not found"))
    except (ImportError, ValueError) as e:
        tests.append(("Package Import", False, f"❌ {e}"))

    # Test 2: CLI tools
    try:
        if importlib.util.find_spec("h2k_hpxml.cli.convert") is not None:
            tests.append(("CLI Tools", True, "✅"))
        else:
            tests.append(("CLI Tools", False, "❌ CLI module not found"))
    except (ImportError, ValueError) as e:
        tests.append(("CLI Tools", False, f"❌ {e}"))

    # Test 3: Dependencies (delegated to osdep with h2k versions)
    try:
        manager = DependencyManager(config=H2K_CONFIG, include_hpxml=True)
        deps_ok = manager.check_only()
        tests.append(("Dependencies", deps_ok, "✅" if deps_ok else "❌ Missing dependencies"))
    except Exception as e:
        tests.append(("Dependencies", False, f"❌ {e}"))

    # Test 4: Configuration (h2k-specific)
    try:
        from h2k_hpxml.config.manager import ConfigManager

        config = ConfigManager()
        if config.openstudio_binary and config.hpxml_os_path:
            tests.append(("Configuration", True, "✅"))
        else:
            tests.append(("Configuration", False, "❌ Missing paths"))
    except Exception as e:
        tests.append(("Configuration", False, f"❌ {e}"))

    all_passed = True
    for test_name, passed, message in tests:
        click.echo(f"{test_name:15}: {message}")
        if not passed:
            all_passed = False

    click.echo("\n" + "=" * 40)
    if all_passed:
        click.echo("🎉 All quick tests passed!")
        return True
    click.echo("⚠️  Some tests failed. Run 'os-setup --setup' or 'os-setup --auto-install'")
    return False


def test_smart_installation():
    """Smart installation test - detects uv vs pip automatically."""
    import shutil
    import subprocess

    click.echo("🧪 H2K-HPXML Smart Installation Test")
    click.echo("=" * 40)

    runner = "python"
    if shutil.which("uv"):
        try:
            result = subprocess.run(
                ["uv", "run", "python", "-c", "import h2k_hpxml"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.returncode == 0:
                runner = "uv"
        except Exception:
            pass

    click.echo(f"🔍 Detected runner: {runner}")

    if not test_quick_installation():
        return False

    click.echo("\n📋 Testing CLI Commands")
    click.echo("-" * 20)

    commands = [
        ("h2k-hpxml --help", "Main CLI help"),
        ("os-setup --check-only", "Dependencies check"),
        ("h2k-resilience --help", "Resilience CLI help"),
    ]

    all_passed = True
    for cmd, description in commands:
        try:
            if runner == "uv" and not cmd.startswith("python"):
                full_cmd = ["uv", "run"] + cmd.split()
            else:
                full_cmd = cmd.split()

            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
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
    click.echo("⚠️  Some CLI tests failed.")
    return False


def test_comprehensive_installation():
    """Comprehensive installation test with an actual H2K->HPXML conversion."""
    import tempfile
    from pathlib import Path

    click.echo("🧪 H2K-HPXML Comprehensive Installation Test")
    click.echo("=" * 50)

    # Generic dependency verification first
    if not verify_installation(config=H2K_CONFIG, include_hpxml=True):
        click.echo("❌ Dependency verification failed, skipping conversion test")
        return False

    click.echo("\n🔄 Testing H2K to HPXML Conversion")
    click.echo("-" * 30)

    try:
        from h2k_hpxml.examples import list_example_files

        examples = list_example_files()
        if not examples:
            click.echo("❌ No example files found")
            return False

        example_file = examples[0]
        click.echo(f"📁 Using example: {example_file.name}")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_output.xml"

            from h2k_hpxml.api import convert_h2k_file

            result_path = convert_h2k_file(input_path=example_file, output_path=output_file)

            if result_path and Path(result_path).exists():
                click.echo("✅ H2K to HPXML conversion successful")
                if output_file.exists() and output_file.stat().st_size > 0:
                    size_kb = output_file.stat().st_size // 1024
                    click.echo(f"✅ Output HPXML file created ({size_kb} KB)")
                    try:
                        import xml.etree.ElementTree as ET

                        ET.parse(output_file)
                        click.echo("✅ Output XML is well-formed")
                        return True
                    except ET.ParseError as e:
                        click.echo(f"❌ Output XML is malformed: {e}")
                        return False
                click.echo("❌ Output file not created or empty")
                return False
            click.echo("❌ Conversion failed: No output file generated")
            return False
    except Exception as e:
        click.echo(f"❌ Comprehensive test failed: {e}")
        return False


def main():
    """Entry point for the h2k-hpxml ``os-setup`` command."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="os-setup",
        description="Install and manage OpenStudio, EnergyPlus, and OpenStudio-HPXML for h2k-hpxml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Check dependencies and prompt to install if missing
  %(prog)s --check-only           # Only check dependencies, don't install
  %(prog)s --auto-install         # Automatically install missing dependencies (no prompts)
  %(prog)s --setup                # Set up user configuration from template
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
  %(prog)s --test-quick           # Quick installation verification
  %(prog)s --test-installation    # Smart installation test (auto-detects uv vs pip)
  %(prog)s --test-comprehensive   # Comprehensive test with conversion
        """,
    )

    parser.add_argument(
        "--check-only", action="store_true", help="Only check dependencies, don't install"
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Automatically install missing dependencies without prompts (recommended)",
    )
    parser.add_argument("--install-quiet", action="store_true", help="Alias for --auto-install")
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
        "--hpxml-path", type=str, metavar="PATH", help="Custom OpenStudio-HPXML installation path"
    )
    parser.add_argument(
        "--openstudio-path", type=str, metavar="PATH", help="Custom OpenStudio installation path"
    )
    parser.add_argument(
        "--test-quick", action="store_true", help="Run quick installation verification"
    )
    parser.add_argument(
        "--test-installation",
        action="store_true",
        help="Run smart installation test (auto-detects uv vs pip)",
    )
    parser.add_argument(
        "--test-comprehensive",
        action="store_true",
        help="Run comprehensive installation test with conversion",
    )

    args = parser.parse_args()

    if args.test_quick:
        success = test_quick_installation()
    elif args.test_installation:
        success = test_smart_installation()
    elif args.test_comprehensive:
        success = test_comprehensive_installation()
    elif args.setup:
        success = setup_user_config()
        if success:
            click.echo("✅ User configuration setup completed!")
        else:
            click.echo("❌ Failed to setup user configuration")
    elif args.uninstall:
        manager = DependencyManager(
            interactive=True,  # Uninstall is always interactive for safety
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            config=H2K_CONFIG,
            include_hpxml=True,
        )
        success = manager.uninstall_dependencies()
    elif args.check_only:
        success = validate_dependencies(
            check_only=True,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            include_hpxml=True,
        )
    elif args.install_quiet or args.auto_install:
        success = validate_dependencies(
            interactive=False,
            install_quiet=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            include_hpxml=True,
        )
    else:
        success = validate_dependencies(
            interactive=True,
            skip_deps=args.skip_deps,
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
            include_hpxml=True,
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
