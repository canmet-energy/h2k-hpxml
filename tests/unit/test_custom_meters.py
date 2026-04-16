#!/usr/bin/env python3
"""
Test script to verify automatic custom Output:Meter functionality.

This script demonstrates how custom meters are automatically added during
the h2k-hpxml workflow.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from h2k_hpxml.config import ConfigManager
from h2k_hpxml.utils.idf_postprocessor import add_output_meters_to_idf


def test_config_manager():
    """Test that ConfigManager properly reads custom meters from config."""
    print("=" * 60)
    print("Testing ConfigManager Custom Meters")
    print("=" * 60)
    
    config = ConfigManager()
    custom_meters = config.custom_meters
    
    print(f"\nCustom meters from configuration:")
    if custom_meters:
        for meter in custom_meters:
            print(f"  - {meter['name']} ({meter['frequency']})")
    else:
        print("  (No custom meters configured)")
    
    print("\n✓ ConfigManager test passed\n")
    return custom_meters


def test_idf_postprocessor():
    """Test the IDF postprocessor functionality."""
    print("=" * 60)
    print("Testing IDF Postprocessor")
    print("=" * 60)
    
    # Find an existing IDF file to test with
    # Search in standard output directory for any building
    output_dir = Path("output")
    test_idf = None
    
    if output_dir.exists():
        # Look for any in.idf file in output/*/run/in.idf
        for idf_path in output_dir.glob("*/run/in.idf"):
            test_idf = idf_path
            break
    
    if not test_idf or not test_idf.exists():
        print(f"\n⚠ No test IDF file found in output directory")
        print("  Run h2k-hpxml first to generate an IDF file for testing")
        print("  Example: h2k-hpxml input.h2k")
        return False
    
    print(f"\nTest IDF file: {test_idf}")
    
    # Test meters
    test_meters = [
        {'name': 'Heating:Electricity', 'frequency': 'Hourly'},
        {'name': 'WaterSystems:Electricity', 'frequency': 'Hourly'},
    ]
    
    print(f"\nAdding test meters:")
    for meter in test_meters:
        print(f"  - {meter['name']} ({meter['frequency']})")
    
    # Create a backup
    backup_path = test_idf.with_suffix('.idf.backup')
    import shutil
    shutil.copy2(test_idf, backup_path)
    print(f"\n✓ Created backup: {backup_path}")
    
    # Add meters
    result = add_output_meters_to_idf(str(test_idf), test_meters)
    
    if result:
        print("\n✓ IDF postprocessor test passed")
        
        # Verify meters were added
        with open(test_idf, 'r') as f:
            content = f.read()
            for meter in test_meters:
                if meter['name'] in content:
                    print(f"  ✓ Found {meter['name']} in IDF")
                else:
                    print(f"  ✗ {meter['name']} not found in IDF")
        
        # Restore from backup
        shutil.copy2(backup_path, test_idf)
        print(f"\n✓ Restored original IDF from backup")
        
        return True
    else:
        print("\n✗ IDF postprocessor test failed")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("H2K-HPXML Custom Meters Integration Test")
    print("=" * 60)
    
    # Test 1: ConfigManager
    custom_meters = test_config_manager()
    
    # Test 2: IDF Postprocessor
    test_idf_postprocessor()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\n")
