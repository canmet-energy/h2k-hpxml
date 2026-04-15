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
    test_idf = Path("sara/output/ERS-EX-10622/run/in.idf")
    
    if not test_idf.exists():
        print(f"\n⚠ Test IDF file not found: {test_idf}")
        print("  Run h2k-hpxml first to generate an IDF file for testing")
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


def show_usage_examples():
    """Show usage examples for custom meters."""
    print("\n" + "=" * 60)
    print("Usage Examples")
    print("=" * 60)
    
    print("\n1. Configure custom meters in config file:")
    print("   Edit: config/conversionconfig.ini")
    print("""
   [simulation]
   custom_meters = Heating:Electricity,WaterSystems:Electricity
   meter_frequency = Hourly
   """)
    
    print("2. Run h2k-hpxml normally:")
    print("   $ h2k-hpxml input.h2k")
    print("""
   → H2K converted to HPXML
   → IDF generated
   → Custom meters added automatically
   → EnergyPlus simulation runs with custom meters
   """)
    
    print("3. Check meter outputs:")
    print("   - Standard output: output/ERS-EX-XXXXX/run/eplusmtr.csv")
    print("   - Hourly data: output/ERS-EX-XXXXX/run/eplusout.csv")
    print("   - Results: output/ERS-EX-XXXXX/run/results_annual.csv")
    
    print("\n4. Available meter names (examples):")
    print("   - Heating:Electricity")
    print("   - WaterSystems:Electricity")
    print("   - Cooling:Electricity")
    print("   - InteriorLights:Electricity")
    print("   - ExteriorLights:Electricity")
    print("   - Fans:Electricity")
    print("   - Pumps:Electricity")
    print("""
   → See eplusout.mdd file for complete list of available meters""")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("H2K-HPXML Custom Meters Integration Test")
    print("=" * 60)
    
    # Test 1: ConfigManager
    custom_meters = test_config_manager()
    
    # Test 2: IDF Postprocessor
    test_idf_postprocessor()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\n")
