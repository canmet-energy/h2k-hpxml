"""Tests for build_translation_config and input validation."""

import pytest

from h2k_hpxml.config.translation_config import build_translation_config
from h2k_hpxml.core.input_validation import validate_and_load_configuration
from h2k_hpxml.exceptions import ConfigurationError


def test_build_translation_config_applies_overrides():
    config = build_translation_config(
        overrides={"translation_mode": "ASHRAE140", "operating_condition": "ROC"}
    )
    assert config["translation_mode"] == "ASHRAE140"
    assert config["operating_condition"] == "ROC"


def test_build_translation_config_includes_ini_defaults():
    config = build_translation_config()
    assert "translation_mode" in config
    assert "operating_condition" in config


def test_validate_and_load_configuration_returns_operating_condition():
    add_test_wall, translation_mode, operating_condition = validate_and_load_configuration(
        "<HouseFile></HouseFile>",
        {"translation_mode": "STANDARD", "operating_condition": "ROC"},
    )
    assert add_test_wall is False
    assert translation_mode == "STANDARD"
    assert operating_condition == "ROC"


def test_legacy_soc_translation_mode_maps_to_standard():
    add_test_wall, translation_mode, operating_condition = validate_and_load_configuration(
        "<HouseFile></HouseFile>",
        {"translation_mode": "SOC", "operating_condition": "SOC"},
    )
    assert add_test_wall is False
    assert translation_mode == "STANDARD"
    assert operating_condition == "SOC"


def test_invalid_operating_condition_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="Invalid operating condition"):
        validate_and_load_configuration(
            "<HouseFile></HouseFile>",
            {"translation_mode": "STANDARD", "operating_condition": "HOC"},
        )
