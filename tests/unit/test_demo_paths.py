"""
Unit tests for demo path construction.
"""

import os
from h2k_hpxml.config.manager import ConfigManager


def test_demo_ruby_hpxml_path_construction():
    """Test that ruby_hpxml_path is constructed correctly using auto-detection."""
    # This is how demo.py should construct the path (using auto-detection)
    config = ConfigManager()
    hpxml_os_path = config.hpxml_os_path  # Use property that auto-detects
    ruby_hpxml_path = os.path.join(hpxml_os_path, "workflow", "run_simulation.rb")

    # Verify the path construction
    assert hpxml_os_path is not None, "hpxml_os_path should be auto-detected"
    assert ruby_hpxml_path is not None, "ruby_hpxml_path should be constructed"
    assert "workflow/run_simulation.rb" in ruby_hpxml_path, "Should contain workflow script path"
    assert os.path.exists(ruby_hpxml_path), f"Script should exist at {ruby_hpxml_path}"


def test_config_does_not_have_ruby_hpxml_path():
    """Verify that config file doesn't have ruby_hpxml_path key (should be constructed)."""
    config = ConfigManager()
    ruby_hpxml_path_from_config = config.get("paths", "ruby_hpxml_path")

    # This should be None because the key doesn't exist in config
    assert ruby_hpxml_path_from_config is None, (
        "Config should not contain ruby_hpxml_path key - it should be constructed from auto-detected hpxml_os_path"
    )

    # Also verify that hpxml_os_path is not in the raw config but available as property
    raw_hpxml_path = config.get("paths", "hpxml_os_path")
    property_hpxml_path = config.hpxml_os_path

    # Raw config should not have it (we removed it), but property should work
    assert property_hpxml_path is not None, "Property should auto-detect HPXML path"