#!/usr/bin/env python3
"""
Main Entry Point for H2K to HPXML Converter GUI

This script launches the graphical user interface for the H2K to HPXML converter.
It can be run directly from the command line or imported as a module.

Usage:
    python -m h2k_hpxml.gui.main
    python src/h2k_hpxml/gui/main.py
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('h2k_gui.log', mode='a')
        ]
    )
    
    # Reduce noise from GUI libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('tkinter').setLevel(logging.WARNING)

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    # Check CustomTkinter
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    # Check psutil for system monitoring
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # Check core project modules
    try:
        from h2k_hpxml.gui.app import H2KConverterGUI
    except ImportError as e:
        missing_deps.append(f"h2k_hpxml core modules ({e})")
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies:")
        print("  pip install customtkinter psutil")
        return False
    
    return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="H2K to HPXML Converter GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Launch GUI normally
  %(prog)s --debug            # Launch with debug logging
  %(prog)s --check-deps       # Check dependencies only
  %(prog)s --version          # Show version information
        """
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )
    
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "system"],
        default="system",
        help="Set GUI theme (default: system)"
    )
    
    return parser.parse_args()

def show_version():
    """Show version information."""
    try:
        from h2k_hpxml import __version__
        version = __version__
    except ImportError:
        version = "1.7.0"  # Fallback version
    
    print(f"H2K to HPXML Converter GUI v{version}")
    print("Copyright (c) 2024 NRCAN")
    print("License: All rights reserved")
    
    # Show Python and system info
    print(f"\nPython: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Show dependency versions
    deps_info = []
    
    try:
        import customtkinter
        deps_info.append(f"CustomTkinter: {customtkinter.__version__}")
    except (ImportError, AttributeError):
        deps_info.append("CustomTkinter: Not available")
    
    try:
        import psutil
        deps_info.append(f"psutil: {psutil.__version__}")
    except (ImportError, AttributeError):
        deps_info.append("psutil: Not available")
    
    if deps_info:
        print("\nDependencies:")
        for info in deps_info:
            print(f"  {info}")

def main():
    """Main entry point for the GUI application."""
    args = parse_arguments()
    
    # Handle special commands
    if args.version:
        show_version()
        return 0
    
    if args.check_deps:
        print("Checking dependencies...")
        if check_dependencies():
            print("✓ All dependencies are available")
            return 0
        else:
            return 1
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting H2K to HPXML Converter GUI")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    try:
        # Import and configure GUI
        from h2k_hpxml.gui.app import H2KConverterGUI
        import customtkinter as ctk
        
        # Set theme
        ctk.set_appearance_mode(args.theme)
        
        logger.info(f"GUI theme set to: {args.theme}")
        
        # Create and run application
        logger.info("Creating GUI application...")
        app = H2KConverterGUI()
        
        logger.info("Starting GUI main loop...")
        app.mainloop()
        
        logger.info("GUI application closed normally")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to start GUI application: {e}", exc_info=True)
        
        # Try to show error dialog if possible
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Startup Error",
                f"Failed to start H2K GUI application:\n\n{str(e)}\n\nCheck the log file for details."
            )
        except:
            print(f"ERROR: Failed to start GUI application: {e}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())