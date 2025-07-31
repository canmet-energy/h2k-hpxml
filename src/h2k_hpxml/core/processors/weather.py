"""
Weather data processing for H2K to HPXML translation.

This module handles processing of weather information from H2K files
and mapping to appropriate HPXML weather station data.
"""

from ...core import data_utils as obj
from ...exceptions import WeatherDataError
from ...utils import weather
from ...utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def process_weather_data(h2k_dict, hpxml_dict, translation_mode):
    """
    Process weather data and update HPXML weather station information.

    Args:
        h2k_dict: Parsed H2K dictionary
        hpxml_dict: Parsed HPXML dictionary
        translation_mode: Translation mode ('SOC' or 'ASHRAE140')

    Returns:
        None: Modifies hpxml_dict in place

    Raises:
        WeatherDataError: If weather processing fails
    """
    logger.info("Processing weather data")

    try:
        # Get weather station dictionary from HPXML
        weather_dict = hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["ClimateandRiskZones"][
            "WeatherStation"
        ]

        # Process weather file based on translation mode
        if translation_mode == "ASHRAE140":
            # ASHRAE140 mode uses specific test weather files
            weather_location = obj.get_val(
                h2k_dict, "HouseFile,ProgramInformation,Weather,Location,English"
            )

            if not weather_location:
                raise WeatherDataError("Weather location not found in H2K file for ASHRAE140 mode")

            if weather_location == "Lasvega":
                weather_file = "USA_NV_Las.Vegas-McCarran.Intl.AP.723860_TMY3"
            else:
                weather_file = "USA_CO_Colorado.Springs-Peterson.Field.724660_TMY3"

        else:
            # Standard mode uses CWEC weather files
            weather_region = obj.get_val(
                h2k_dict, "HouseFile,ProgramInformation,Weather,Region,English"
            )
            weather_location = obj.get_val(
                h2k_dict, "HouseFile,ProgramInformation,Weather,Location,English"
            )

            if not weather_region or not weather_location:
                raise WeatherDataError(
                    f"Weather information incomplete in H2K file. Region: {weather_region}, Location: {weather_location}"
                )

            weather_file = weather.get_cwec_file(weather_region, weather_location)

        # Log the weather location for diagnostics
        weather_location = obj.get_val(
            h2k_dict, "HouseFile,ProgramInformation,Weather,Location,English"
        )
        logger.info(f"HOT2000 Weather Location: {weather_location}")
        logger.info(f"Selected weather file: {weather_file}")

        # Update HPXML weather station information
        weather_dict["Name"] = weather_file
        weather_dict["extension"]["EPWFilePath"] = f"{weather_file}.epw"

        logger.debug("Weather data processed successfully")

    except Exception as e:
        if isinstance(e, WeatherDataError):
            raise
        else:
            raise WeatherDataError(
                f"Failed to process weather data: {e}", weather_location=weather_location
            )
