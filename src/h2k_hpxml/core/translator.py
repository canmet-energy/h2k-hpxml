"""
Main module that handles the conversion of an h2k file to hpxml

Inputs: h2k string in xml format, config class instance to handle config params

Outputs: hpxml string
"""

from typing import Optional

from ..types import ConfigDict
from ..types import H2KDict
from ..types import HPXMLDict
from ..types import TranslationMode
from ..types import TranslationResult
from ..utils.logging import get_logger
from . import model as Model
from .hpxml_assembly import finalize_hpxml_output as _finalize_hpxml_output
from .input_validation import validate_and_load_configuration as _validate_and_load_configuration
from .processors.building import process_building_details as _process_building_details
from .processors.enclosure import process_enclosure_components as _process_enclosure_components
from .processors.systems import process_systems_and_loads as _process_systems_and_loads
from .processors.weather import process_weather_data as _process_weather_data
from .template_loader import load_and_parse_templates as _load_and_parse_templates

# Get logger for this module
logger = get_logger(__name__)


def h2ktohpxml(h2k_string: str = "", config: Optional[ConfigDict] = None) -> TranslationResult:
    """
    Convert H2K XML string to HPXML format.

    Args:
        h2k_string: H2K file content as XML string
        config: Configuration dictionary for translation options

    Returns:
        HPXML formatted string

    Raises:
        H2KParsingError: If H2K input cannot be parsed
        HPXMLGenerationError: If HPXML generation fails
        ConfigurationError: If configuration is invalid
        WeatherDataError: If weather data processing fails
    """
    logger.info("Starting H2K to HPXML translation")

    # Handle None config
    if config is None:
        config = {}

    # ================ 0. Validate inputs and get config parameters ================
    add_test_wall: bool
    translation_mode: TranslationMode
    add_test_wall, translation_mode = _validate_and_load_configuration(h2k_string, config)

    # ================ 1. Load and parse templates ================
    h2k_dict: H2KDict
    hpxml_dict: HPXMLDict
    h2k_dict, hpxml_dict = _load_and_parse_templates(h2k_string)

    # ================ 2. Initialize model data and process building details ================
    model_data: Model.ModelData = Model.ModelData()
    _process_building_details(h2k_dict, hpxml_dict, model_data)

    # ================ 3. Process weather data ================
    _process_weather_data(h2k_dict, hpxml_dict, translation_mode)

    # ================ 7. Process enclosure components ================
    _process_enclosure_components(h2k_dict, hpxml_dict, model_data, add_test_wall)

    # ================ 8. Process systems and loads ================
    _process_systems_and_loads(h2k_dict, hpxml_dict, model_data)

    # ================ 9. Finalize HPXML output ================
    return _finalize_hpxml_output(hpxml_dict, h2k_dict, model_data, translation_mode)
