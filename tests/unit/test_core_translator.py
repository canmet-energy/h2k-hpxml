"""Unit tests for core translator module."""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from h2k_hpxml.core.model import ModelData
from h2k_hpxml.core.translator import h2ktohpxml
from h2k_hpxml.exceptions import ConfigurationError
from h2k_hpxml.exceptions import H2KParsingError


class TestH2KToHPXML:
    """Test cases for the main h2ktohpxml function."""

    def test_empty_h2k_string_raises_error(self):
        """Test that empty H2K string raises H2KParsingError."""
        with pytest.raises(H2KParsingError, match="H2K input string is empty"):
            h2ktohpxml("", {})

    def test_none_h2k_string_raises_error(self):
        """Test that None H2K string raises H2KParsingError."""
        with pytest.raises(H2KParsingError, match="H2K input string is empty or None"):
            h2ktohpxml(None, {})

    def test_invalid_config_type_raises_error(self):
        """Test that non-dict config raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Configuration must be a dictionary"):
            h2ktohpxml("<test>valid</test>", "invalid_config")

    def test_none_config_defaults_to_empty_dict(self):
        """Test that None config is handled gracefully."""
        with patch("h2k_hpxml.core.translator._validate_and_load_configuration") as mock_validate:
            mock_validate.return_value = (False, "SOC")
            with patch("h2k_hpxml.core.translator._load_and_parse_templates") as mock_templates:
                mock_templates.return_value = ({}, {})
                with patch("h2k_hpxml.core.translator._process_building_details"):
                    with patch("h2k_hpxml.core.translator._process_weather_data"):
                        with patch("h2k_hpxml.core.translator._process_enclosure_components"):
                            with patch("h2k_hpxml.core.translator._process_systems_and_loads"):
                                with patch(
                                    "h2k_hpxml.core.translator._finalize_hpxml_output"
                                ) as mock_finalize:
                                    mock_finalize.return_value = "<hpxml></hpxml>"

                                    result = h2ktohpxml("<test>valid</test>", None)

                                    # Verify validate was called with empty dict
                                    mock_validate.assert_called_once_with("<test>valid</test>", {})
                                    assert result == "<hpxml></hpxml>"

    def test_invalid_translation_mode_raises_error(self):
        """Test that invalid translation mode raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Invalid translation mode"):
            h2ktohpxml("<test>valid</test>", {"translation_mode": "INVALID"})

    def test_valid_translation_modes(self):
        """Test that valid translation modes are accepted."""
        valid_modes = ["SOC", "ASHRAE140"]

        for mode in valid_modes:
            with patch("h2k_hpxml.core.translator._load_and_parse_templates") as mock_templates:
                mock_templates.return_value = ({}, {})
                with patch("h2k_hpxml.core.translator._process_building_details"):
                    with patch("h2k_hpxml.core.translator._process_weather_data"):
                        with patch("h2k_hpxml.core.translator._process_enclosure_components"):
                            with patch("h2k_hpxml.core.translator._process_systems_and_loads"):
                                with patch(
                                    "h2k_hpxml.core.translator._finalize_hpxml_output"
                                ) as mock_finalize:
                                    mock_finalize.return_value = f"<hpxml mode='{mode}'></hpxml>"

                                    result = h2ktohpxml(
                                        "<test>valid</test>", {"translation_mode": mode}
                                    )
                                    assert f"mode='{mode}'" in result

    @patch("h2k_hpxml.core.translator._finalize_hpxml_output")
    @patch("h2k_hpxml.core.translator._process_systems_and_loads")
    @patch("h2k_hpxml.core.translator._process_enclosure_components")
    @patch("h2k_hpxml.core.translator._process_weather_data")
    @patch("h2k_hpxml.core.translator._process_building_details")
    @patch("h2k_hpxml.core.translator._load_and_parse_templates")
    @patch("h2k_hpxml.core.translator._validate_and_load_configuration")
    def test_processor_function_call_order(
        self,
        mock_validate,
        mock_templates,
        mock_building,
        mock_weather,
        mock_enclosure,
        mock_systems,
        mock_finalize,
    ):
        """Test that processor functions are called in correct order."""
        # Setup mocks
        mock_validate.return_value = (False, "SOC")
        mock_templates.return_value = ({"test": "h2k"}, {"test": "hpxml"})
        mock_finalize.return_value = "<hpxml>result</hpxml>"

        # Call function
        result = h2ktohpxml("<test>valid</test>", {"translation_mode": "SOC"})

        # Verify call order and arguments
        mock_validate.assert_called_once_with("<test>valid</test>", {"translation_mode": "SOC"})
        mock_templates.assert_called_once_with("<test>valid</test>")

        # Verify ModelData was created and passed to processors
        model_data_calls = [
            call
            for call in [mock_building.call_args, mock_enclosure.call_args, mock_systems.call_args]
            if call is not None
        ]

        # Check that all processor functions received a ModelData instance
        for call in model_data_calls:
            assert len(call[0]) >= 3  # h2k_dict, hpxml_dict, model_data
            assert isinstance(call[0][2], ModelData)

        mock_weather.assert_called_once()
        mock_finalize.assert_called_once()

        assert result == "<hpxml>result</hpxml>"

    def test_add_test_wall_parameter_passed_correctly(self):
        """Test that add_test_wall parameter is passed to enclosure processor."""
        with patch("h2k_hpxml.core.translator._validate_and_load_configuration") as mock_validate:
            mock_validate.return_value = (True, "SOC")  # add_test_wall = True

            with patch("h2k_hpxml.core.translator._load_and_parse_templates") as mock_templates:
                mock_templates.return_value = ({}, {})

                with patch("h2k_hpxml.core.translator._process_building_details"):
                    with patch("h2k_hpxml.core.translator._process_weather_data"):
                        with patch(
                            "h2k_hpxml.core.translator._process_enclosure_components"
                        ) as mock_enclosure:
                            with patch("h2k_hpxml.core.translator._process_systems_and_loads"):
                                with patch(
                                    "h2k_hpxml.core.translator._finalize_hpxml_output"
                                ) as mock_finalize:
                                    mock_finalize.return_value = "<hpxml></hpxml>"

                                    h2ktohpxml("<test>valid</test>", {"add_test_wall": True})

                                    # Verify add_test_wall=True was passed to enclosure processor
                                    mock_enclosure.assert_called_once()
                                    args = mock_enclosure.call_args[0]
                                    assert (
                                        len(args) == 4
                                    )  # h2k_dict, hpxml_dict, model_data, add_test_wall
                                    assert args[3] is True  # add_test_wall parameter

    def test_translation_mode_passed_to_processors(self):
        """Test that translation_mode is passed to appropriate processors."""
        test_mode = "ASHRAE140"

        with patch("h2k_hpxml.core.translator._validate_and_load_configuration") as mock_validate:
            mock_validate.return_value = (False, test_mode)

            with patch("h2k_hpxml.core.translator._load_and_parse_templates") as mock_templates:
                mock_templates.return_value = ({}, {})

                with patch("h2k_hpxml.core.translator._process_building_details"):
                    with patch("h2k_hpxml.core.translator._process_weather_data") as mock_weather:
                        with patch("h2k_hpxml.core.translator._process_enclosure_components"):
                            with patch("h2k_hpxml.core.translator._process_systems_and_loads"):
                                with patch(
                                    "h2k_hpxml.core.translator._finalize_hpxml_output"
                                ) as mock_finalize:
                                    mock_finalize.return_value = "<hpxml></hpxml>"

                                    h2ktohpxml(
                                        "<test>valid</test>", {"translation_mode": test_mode}
                                    )

                                    # Verify translation_mode passed to weather processor
                                    mock_weather.assert_called_once()
                                    weather_args = mock_weather.call_args[0]
                                    assert (
                                        len(weather_args) == 4
                                    )  # h2k_dict, hpxml_dict, translation_mode, config_manager
                                    assert weather_args[2] == test_mode

                                    # Verify translation_mode passed to finalize
                                    mock_finalize.assert_called_once()
                                    finalize_args = mock_finalize.call_args[0]
                                    assert (
                                        len(finalize_args) == 4
                                    )  # hpxml_dict, h2k_dict, model_data, translation_mode
                                    assert finalize_args[3] == test_mode
