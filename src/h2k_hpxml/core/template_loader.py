"""
Template loading and XML parsing for H2K to HPXML translation.

This module handles loading the base HPXML template and parsing both H2K and HPXML files.
"""

import os

import xmltodict

from ..exceptions import ConfigurationError
from ..exceptions import H2KParsingError
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def load_and_parse_templates(h2k_string):
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

    # Load template HPXML file using multiple strategies for compatibility
    base_hpxml = None
    base_hpxml_path = None

    # Strategy 1: Try importlib.resources (Python 3.7+, works with installed packages)
    try:
        from importlib import resources

        try:
            with resources.open_text("h2k_hpxml.resources", "template_base.xml") as f:
                base_hpxml = f.read()
                base_hpxml_path = "h2k_hpxml.resources/template_base.xml"
                logger.debug("Loaded template using importlib.resources")
        except (FileNotFoundError, ImportError, AttributeError):
            pass
    except ImportError:
        pass

    # Strategy 2: Try pkg_resources for pip installations
    if base_hpxml is None:
        try:
            import pkg_resources

            resource_path = pkg_resources.resource_filename(
                "h2k_hpxml", "resources/template_base.xml"
            )
            if os.path.exists(resource_path):
                with open(resource_path, encoding="utf-8") as f:
                    base_hpxml = f.read()
                    base_hpxml_path = resource_path
                    logger.debug(f"Loaded template using pkg_resources from {resource_path}")
        except (ImportError, FileNotFoundError):
            pass

    # Strategy 3: Fallback to relative path (for development)
    if base_hpxml is None:
        base_hpxml_path = os.path.join(
            os.path.dirname(__file__), "..", "resources", "template_base.xml"
        )
        if os.path.exists(base_hpxml_path):
            try:
                with open(base_hpxml_path, encoding="utf-8") as f:
                    base_hpxml = f.read()
                    logger.debug(f"Loaded template using relative path from {base_hpxml_path}")
            except OSError as e:
                raise ConfigurationError(f"Failed to read base HPXML template: {e}")

    # If all strategies failed, raise an error
    if base_hpxml is None:
        raise ConfigurationError(
            "Base HPXML template not found. Tried:\n"
            "1. importlib.resources (package installation)\n"
            "2. pkg_resources (pip installation)\n"
            "3. Relative path (development mode)\n"
            "Please ensure the package is properly installed."
        )

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
