"""
Template loading and XML parsing for H2K to HPXML translation.

This module handles loading the base HPXML template and parsing both H2K and HPXML files.
"""

import os
from typing import Tuple

import xmltodict

from ..exceptions import ConfigurationError
from ..exceptions import H2KParsingError
from ..types import H2KDict
from ..types import HPXMLDict
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def load_and_parse_templates(h2k_string: str) -> Tuple[H2KDict, HPXMLDict]:
    """
    Load and parse HPXML template and H2K input.

    Args:
        h2k_string: H2K file content as XML string

    Returns:
        tuple: (h2k_dict, hpxml_dict) parsed dictionaries

    Raises:
        H2KParsingError: If H2K parsing fails
        ConfigurationError: If template loading fails
    """
    logger.info("Loading and parsing templates")

    # Load template HPXML file
    base_hpxml_path = os.path.join(
        os.path.dirname(__file__), "..", "resources", "template_base.xml"
    )

    if not os.path.exists(base_hpxml_path):
        raise ConfigurationError(f"Base HPXML template not found at: {base_hpxml_path}")

    try:
        with open(base_hpxml_path, encoding="utf-8") as f:
            base_hpxml = f.read()
    except OSError as e:
        raise ConfigurationError(f"Failed to read base HPXML template: {e}")

    # Parse H2K XML
    try:
        h2k_dict = xmltodict.parse(h2k_string)
    except Exception as e:
        raise H2KParsingError(f"Failed to parse H2K XML: {e}", xml_error=e)

    # Validate H2K structure
    if not isinstance(h2k_dict, dict) or "HouseFile" not in h2k_dict:
        raise H2KParsingError("Invalid H2K structure: missing 'HouseFile' root element")

    # Parse HPXML template
    try:
        hpxml_dict = xmltodict.parse(base_hpxml)
    except Exception as e:
        raise ConfigurationError(f"Failed to parse base HPXML template: {e}")

    logger.debug("Templates loaded and parsed successfully")
    return h2k_dict, hpxml_dict
