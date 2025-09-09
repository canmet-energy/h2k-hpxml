#!/usr/bin/env python3
"""
Test script to demonstrate the improved dependency installation system.

This script shows how the h2k-hpxml package now automatically handles
dependency installation with smart fallback logic.
"""

import os
import sys
from pathlib import Path

def test_dependency_installation():
    """Test the dependency installation system."""
    print("=" * 60)
    print("H2K-HPXML Dependency Installation Test")
    print("=" * 60)
    
    # Test current environment
    print("\n1. Current Environment:")
    print("-" * 40)
    
    try:
        import h2k_hpxml.installer as installer
        info = installer.get_installation_info()
        
        print(f"Dependencies directory: {info['deps_dir']}")
        print(f"Installation type: {info['deps_dir_type']}")
        print(f"Source: {info['deps_dir_source']}")
        print(f"Writable: {info['writable']}")
        print(f"OpenStudio-HPXML installed: {info['status']['openstudio_hpxml']}")
        print(f"OpenStudio installed: {info['status']['openstudio']}")
        
        if info['status']['openstudio_hpxml']:
            print(f"OpenStudio-HPXML path: {info['openstudio_hpxml_path']}")
        if info['status']['openstudio']:
            print(f"OpenStudio path: {info['openstudio_path']}")
            
    except Exception as e:
        print(f"Error checking installer: {e}")
    
    # Test config manager integration
    print("\n2. Config Manager Integration:")
    print("-" * 40)
    
    try:
        from h2k_hpxml.config.manager import ConfigManager
        config = ConfigManager()
        
        print(f"Auto-detected HPXML OS path: {config.hpxml_os_path}")
        print(f"Auto-detected OpenStudio binary: {config.openstudio_binary}")
        
    except Exception as e:
        print(f"Error checking config: {e}")
    
    # Test OpenStudio Python bindings
    print("\n3. OpenStudio Python Bindings:")
    print("-" * 40)
    
    try:
        import openstudio
        version = openstudio.openStudioVersion()
        print(f"OpenStudio version: {version}")
        print("✓ OpenStudio Python bindings working")
    except ImportError:
        print("✗ OpenStudio Python bindings not available")
    except Exception as e:
        print(f"Error with OpenStudio bindings: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Installation works as follows:")
    print("=" * 60)
    print("1. If H2K_DEPS_DIR is set → use that directory")
    print("2. If package directory is writable → install there")  
    print("3. Otherwise → fall back to ~/.local/share/h2k_hpxml/deps/")
    print("\nThis ensures dependencies install correctly in:")
    print("- DevContainers (uses H2K_DEPS_DIR=/app/deps)")
    print("- Virtual environments (package dir writable)")
    print("- System-wide installs (falls back to user home)")
    print("- CI/CD environments (respects environment variables)")


if __name__ == "__main__":
    test_dependency_installation()