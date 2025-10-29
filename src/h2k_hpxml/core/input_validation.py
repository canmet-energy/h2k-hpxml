"""
Input validation for H2K to HPXML translation.

This module provides validation functions for H2K input files and configuration parameters.
"""

from ..exceptions import ConfigurationError
from ..exceptions import H2KParsingError
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def validate_and_load_configuration(h2k_string, config):
    """
    Validate inputs and extract configuration parameters.

    Args:
        h2k_string: H2K file content as XML string
        config: Configuration dictionary for translation options

    Returns:
        tuple: (add_test_wall, translation_mode) configuration parameters

    Raises:
        H2KParsingError: If H2K input is invalid
        ConfigurationError: If configuration is invalid
    """
    logger.info("Validating inputs and loading configuration")

    # Validate H2K input
    if not h2k_string or not h2k_string.strip():
        raise H2KParsingError("H2K input string is empty or None")

    # Validate configuration
    if not isinstance(config, dict):
        raise ConfigurationError(
            "Configuration must be a dictionary", config_value=str(type(config))
        )

    # Extract configuration parameters
    add_test_wall = config.get("add_test_wall", False)
    translation_mode = config.get("translation_mode", "SOC")

    # Validate translation mode
    valid_modes = ["SOC", "ASHRAE140"]
    if translation_mode not in valid_modes:
        raise ConfigurationError(
            f"Invalid translation mode: {translation_mode}. Must be one of {valid_modes}",
            config_key="translation_mode",
            config_value=translation_mode,
        )

    logger.info(f"Translation Mode: {translation_mode}")
    logger.debug(f"Add test wall: {add_test_wall}")

    return add_test_wall, translation_mode
