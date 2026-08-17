"""
Input validation for H2K to HPXML translation.

This module provides validation functions for H2K input files and configuration parameters.
"""

from ..exceptions import ConfigurationError
from ..exceptions import H2KParsingError
from ..config.translation_modes import VALID_TRANSLATION_MODES
from ..config.translation_modes import normalize_translation_mode
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

VALID_OPERATING_CONDITIONS = ("SOC", "ROC", "General")


def validate_and_load_configuration(h2k_string, config):
    """
    Validate inputs and extract configuration parameters.

    Args:
        h2k_string: H2K file content as XML string
        config: Configuration dictionary for translation options

    Returns:
        tuple: (add_test_wall, translation_mode, operating_condition)

    Raises:
        H2KParsingError: If H2K input is invalid
        ConfigurationError: If configuration is invalid
    """
    logger.info("Validating inputs and loading configuration")

    if not h2k_string or not h2k_string.strip():
        raise H2KParsingError("H2K input string is empty or None")

    if not isinstance(config, dict):
        raise ConfigurationError(
            "Configuration must be a dictionary", config_value=str(type(config))
        )

    add_test_wall = config.get("add_test_wall", False)
    translation_mode = normalize_translation_mode(
        config.get("translation_mode", "STANDARD"),
        warn=logger.warning,
    )
    operating_condition = config.get("operating_condition", "SOC")

    if translation_mode not in VALID_TRANSLATION_MODES:
        raise ConfigurationError(
            f"Invalid translation mode: {translation_mode}. "
            f"Must be one of {VALID_TRANSLATION_MODES}",
            config_key="translation_mode",
            config_value=translation_mode,
        )

    if operating_condition not in VALID_OPERATING_CONDITIONS:
        raise ConfigurationError(
            f"Invalid operating condition: {operating_condition}. "
            f"Must be one of {VALID_OPERATING_CONDITIONS}",
            config_key="operating_condition",
            config_value=operating_condition,
        )

    if translation_mode == "ASHRAE140" and operating_condition != "SOC":
        logger.warning(
            "Operating condition %s is ignored for ASHRAE140 translation; "
            "using asset/H2K-driven loads instead.",
            operating_condition,
        )

    logger.info("Translation Mode: %s", translation_mode)
    logger.info("Operating Condition: %s", operating_condition)
    logger.debug("Add test wall: %s", add_test_wall)

    return add_test_wall, translation_mode, operating_condition
