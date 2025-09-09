#!/usr/bin/env python3
"""
Cross-platform code quality tool for H2K-HPXML project.

Combines code quality checking and fixing in a single Python script.
Works on Windows, Linux, and macOS.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# ANSI color codes for cross-platform output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m' 
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @classmethod
    def disable_on_windows(cls):
        """Disable colors on Windows if not supported."""
        if os.name == 'nt' and not os.environ.get('ANSICON'):
            cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.NC = ''


def run_command(command: List[str], description: str) -> Tuple[bool, str, str]:
    """
    Run a command and return success status, stdout, stderr.
    
    Args:
        command: Command to run as list
        description: Human-readable description
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent.parent  # Run from project root
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        return False, "", f"Command not found: {command[0]}"
    except Exception as e:
        return False, "", str(e)


def check_dependencies() -> bool:
    """Check if required development dependencies are installed."""
    print(f"{Colors.BLUE}Checking development dependencies...{Colors.NC}")
    
    # Check if we can import required packages
    success, _, stderr = run_command([
        sys.executable, "-c", 
        "import black, ruff; print('Dependencies available')"
    ], "Dependency check")
    
    if not success:
        print(f"{Colors.YELLOW}⚠ Installing development dependencies...{Colors.NC}")
        install_success, stdout, install_stderr = run_command([
            sys.executable, "-m", "pip", "install", "-e", ".[dev]"
        ], "Install dependencies")
        
        if not install_success:
            print(f"{Colors.RED}❌ Failed to install dependencies: {install_stderr}{Colors.NC}")
            return False
        print(f"{Colors.GREEN}✓ Dependencies installed{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Dependencies available{Colors.NC}")
    
    return True


def run_quality_check(tool_name: str, command: List[str], fix_mode: bool = False) -> bool:
    """
    Run a quality check tool and report results.
    
    Args:
        tool_name: Human-readable name of the tool
        command: Command to run
        fix_mode: Whether this is a fix operation
        
    Returns:
        True if successful, False otherwise
    """
    action = "Fixing" if fix_mode else "Checking"
    print(f"\n{Colors.BLUE}{action} with {tool_name}...{Colors.NC}")
    print("----------------------------------------")
    
    success, stdout, stderr = run_command(command, f"{tool_name} {action.lower()}")
    
    if success:
        print(f"{Colors.GREEN}✓ {tool_name} {'fixes applied' if fix_mode else 'passed'}{Colors.NC}")
        if stdout.strip():
            print(stdout)
    else:
        print(f"{Colors.RED}✗ {tool_name} {'fix failed' if fix_mode else 'failed'}{Colors.NC}")
        if stderr.strip():
            print(f"Error: {stderr}")
        if stdout.strip():
            print(f"Output: {stdout}")
    
    return success


def run_quality_checks(fix_mode: bool = False) -> int:
    """
    Run all quality checks or fixes.
    
    Args:
        fix_mode: If True, attempt to fix issues automatically
        
    Returns:
        0 if all checks passed, 1 if any failed
    """
    print(f"🔍 H2K-HPXML Code Quality {'Fixes' if fix_mode else 'Checks'}")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    overall_status = 0
    src_paths = ["src/", "tests/"]
    
    if fix_mode:
        # Fix mode: run formatters and auto-fixers
        checks = [
            ("Black formatting", [sys.executable, "-m", "black"] + src_paths),
            ("Ruff auto-fix", [sys.executable, "-m", "ruff", "check", "--fix"] + src_paths),
            ("Import sorting", [sys.executable, "-m", "ruff", "check", "--select", "I", "--fix"] + src_paths),
        ]
    else:
        # Check mode: run validators
        checks = [
            ("Black formatting", [sys.executable, "-m", "black", "--check", "--diff"] + src_paths),
            ("Ruff linting", [sys.executable, "-m", "ruff", "check"] + src_paths),
            ("MyPy type checking", [
                sys.executable, "-m", "mypy", 
                "src/h2k_hpxml/core/", 
                "src/h2k_hpxml/config/", 
                "src/h2k_hpxml/utils/"
            ]),
            ("Basic unit tests", [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"])
        ]
    
    # Run each check
    for tool_name, command in checks:
        if not run_quality_check(tool_name, command, fix_mode):
            overall_status = 1
    
    # Final status report
    print("\n" + "=" * 50)
    if overall_status == 0:
        if fix_mode:
            print(f"{Colors.GREEN}🎉 All fixes applied successfully!{Colors.NC}")
            print("\nNext steps:")
            print("  1. Review the changes made by the formatters")
            print("  2. Run 'uv run python tools/quality.py' to verify all issues are resolved")
            print("  3. Address any remaining type checking issues manually")
            print("  4. Commit your changes")
        else:
            print(f"{Colors.GREEN}🎉 All quality checks passed!{Colors.NC}")
            print("\nYour code meets the quality standards.")
    else:
        if fix_mode:
            print(f"{Colors.RED}❌ Some fixes failed or need manual attention.{Colors.NC}")
            print("\nPlease check the output above and address any remaining issues.")
        else:
            print(f"{Colors.RED}❌ Some quality checks failed.{Colors.NC}")
            print("\nPlease fix the issues above before committing.")
            print("\nQuick fixes:")
            print("  - Run 'uv run python tools/quality.py --fix' to auto-fix many issues")
            print("  - Check mypy output for type issues")
            print("  - Run individual tests to debug failures")
    
    return overall_status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="H2K-HPXML Code Quality Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/quality.py          # Run all quality checks
  python tools/quality.py --fix    # Auto-fix code quality issues
  python tools/quality.py --no-color  # Disable colored output
        """
    )
    
    parser.add_argument(
        "--fix", 
        action="store_true",
        help="Automatically fix issues where possible (black, ruff auto-fix, import sorting)"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true", 
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested or on unsupported Windows
    if args.no_color:
        Colors.disable_on_windows()
    elif os.name == 'nt':
        Colors.disable_on_windows()
    
    # Run quality checks or fixes
    exit_code = run_quality_checks(fix_mode=args.fix)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()