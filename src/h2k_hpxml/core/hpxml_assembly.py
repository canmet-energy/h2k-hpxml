"""
Final HPXML assembly and output generation for H2K to HPXML translation.

This module handles the final assembly of the HPXML document including
applying translation mode specifications and generating the final XML output.
"""

import xmltodict

from ..components.ashrae140_mode import apply_ashrae_140
from ..exceptions import HPXMLGenerationError
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def finalize_hpxml_output(hpxml_dict, h2k_dict, model_data, translation_mode):
    """
    Apply final processing and generate HPXML output string.

    Args:
        hpxml_dict: Parsed HPXML dictionary
        h2k_dict: Parsed H2K dictionary
        model_data: ModelData instance for tracking building information
        translation_mode: Translation mode ('SOC' or 'ASHRAE140')

    Returns:
        str: Final HPXML formatted string

    Raises:
        HPXMLGenerationError: If final assembly fails
    """
    logger.info("Finalizing HPXML output")

    try:
        # ================ Apply overall translation mode specifications ================
        if translation_mode == "ASHRAE140":
            hpxml_dict = apply_ashrae_140(hpxml_dict, h2k_dict, model_data)

        # Generate final HPXML string
        hpxml_output = xmltodict.unparse(
            hpxml_dict, encoding="utf-8", pretty=True, short_empty_elements=True
        )

        logger.info("HPXML output generated successfully")
        logger.debug(f"Final HPXML length: {len(hpxml_output)} characters")

        return hpxml_output

    except Exception as e:
        raise HPXMLGenerationError(
            f"Failed to finalize HPXML output: {e}", component="final_assembly"
        )
