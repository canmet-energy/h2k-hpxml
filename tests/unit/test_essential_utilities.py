"""Essential unit tests for key utility functions used in H2K translation."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from h2k_hpxml.utils.common import ComponentExtractor
from h2k_hpxml.utils.common import FacilityTypeHelper
from h2k_hpxml.utils.common import ValidationHelper
from h2k_hpxml.utils.common import extract_and_process_components


class TestEssentialUtilities:
    """Test essential utility functions that directly impact H2K translation."""

    def test_component_extraction_with_real_h2k_structure(self):
        """Test component extraction with realistic H2K data structure."""
        h2k_dict = {
            "HouseFile": {
                "House": {
                    "Components": {
                        "Wall": [
                            {"Label": "North Wall", "wall_r_value": 12.5},
                            {"Label": "South Wall", "wall_r_value": 15.0},
                        ]
                    }
                }
            }
        }

        components = ComponentExtractor.get_components_safe(h2k_dict, "Wall")
        assert len(components) == 2
        assert components[0]["Label"] == "North Wall"
        assert components[1]["Label"] == "South Wall"

    def test_component_extraction_with_missing_components(self):
        """Test component extraction when components don't exist."""
        h2k_dict = {"HouseFile": {"House": {"Components": {}}}}

        components = ComponentExtractor.get_components_safe(h2k_dict, "Wall")
        assert components == []

    def test_r_value_validation_warns_on_zero(self):
        """Test that zero R-values generate appropriate warnings."""
        component = {"wall_r_value": 0}
        mock_model_data = MagicMock()

        with patch("h2k_hpxml.utils.common.h2k.get_number_field", return_value=0):
            ValidationHelper.validate_r_value(
                component, "wall_r_value", "Test Wall", mock_model_data
            )

        # Should have called add_warning_message
        mock_model_data.add_warning_message.assert_called_once()
        warning = mock_model_data.add_warning_message.call_args[0][0]
        assert "zero (0) R-value" in warning["message"]

    def test_facility_type_determines_attached_correctly(self):
        """Test facility type determination for attached vs detached."""
        # Test attached cases
        assert FacilityTypeHelper.is_attached_unit("attached house") is True
        assert FacilityTypeHelper.is_attached_unit("apartment building") is True

        # Test detached cases
        assert FacilityTypeHelper.is_attached_unit("single family detached") is False
        assert FacilityTypeHelper.is_attached_unit("detached house") is False

    def test_exterior_adjacency_determination(self):
        """Test exterior adjacency logic for building components."""
        component_enclosed = {"@adjacentEnclosedSpace": "true"}
        component_outside = {"@adjacentEnclosedSpace": "false"}

        # Attached unit with enclosed space
        result = FacilityTypeHelper.determine_exterior_adjacent(
            component_enclosed, "attached house"
        )
        assert result == "other non-freezing space"

        # Detached unit with enclosed space should still be outside
        result = FacilityTypeHelper.determine_exterior_adjacent(
            component_enclosed, "detached house"
        )
        assert result == "outside"

        # Any unit without enclosed space is outside
        result = FacilityTypeHelper.determine_exterior_adjacent(component_outside, "attached house")
        assert result == "outside"

    def test_complete_component_processing_workflow(self):
        """Test the complete workflow that components use."""
        h2k_dict = {
            "HouseFile": {
                "House": {"Components": {"Floor": [{"Label": "Main Floor", "area": 1000}]}}
            }
        }

        mock_model_data = MagicMock()
        mock_model_data.increment_counter.return_value = 1

        def mock_processor(component, component_id, model_data):
            return {"id": component_id, "label": component["Label"], "area": component["area"]}

        result = extract_and_process_components(
            h2k_dict, "Floor", mock_model_data, "floor", "Floor", mock_processor
        )

        assert len(result) == 1
        assert result[0]["id"] == "Floor1"
        assert result[0]["label"] == "Main Floor"
        assert result[0]["area"] == 1000

        # Verify counter was incremented
        mock_model_data.increment_counter.assert_called_once_with("floor")

    def test_label_extraction_handles_missing_labels(self):
        """Test label extraction with fallback for missing labels."""
        component_with_label = {"Label": "Custom Wall"}
        component_without_label = {}

        assert ValidationHelper.get_component_label(component_with_label) == "Custom Wall"
        assert ValidationHelper.get_component_label(component_without_label) == "No Label"


class TestRealWorldScenarios:
    """Test utilities against realistic H2K translation scenarios."""

    def test_mixed_component_processing(self):
        """Test processing mixed component types like real H2K files."""
        h2k_dict = {
            "HouseFile": {
                "House": {
                    "Components": {
                        "Wall": {"Label": "Single Wall", "wall_r_value": 10},
                        "Floor": [
                            {"Label": "Floor 1", "area": 500},
                            {"Label": "Floor 2", "area": 300},
                        ],
                    }
                }
            }
        }

        # Test single component becomes list
        walls = ComponentExtractor.get_components_safe(h2k_dict, "Wall")
        assert len(walls) == 1
        assert walls[0]["Label"] == "Single Wall"

        # Test multiple components stay as list
        floors = ComponentExtractor.get_components_safe(h2k_dict, "Floor")
        assert len(floors) == 2
        assert floors[0]["Label"] == "Floor 1"
        assert floors[1]["Label"] == "Floor 2"

    def test_facility_type_for_canadian_housing_types(self):
        """Test facility types common in Canadian H2K files."""
        canadian_types = [
            ("single family detached", False),
            ("single family attached", True),
            ("row house attached", True),  # row houses are usually attached
            ("apartment building", True),
            ("manufactured home", False),
        ]

        for housing_type, expected_attached in canadian_types:
            result = FacilityTypeHelper.is_attached_unit(housing_type)
            assert result == expected_attached, f"Failed for {housing_type}"


# Integration-style test for utility interaction
class TestUtilityIntegration:
    """Test how utilities work together in realistic scenarios."""

    def test_wall_processing_like_real_component(self):
        """Test utility integration similar to actual wall component processing."""
        h2k_dict = {
            "HouseFile": {
                "House": {
                    "Components": {
                        "Wall": [
                            {
                                "Label": "North Wall",
                                "wall_r_value": 12.5,
                                "@adjacentEnclosedSpace": "false",
                            },
                            {
                                "Label": "South Wall",
                                "wall_r_value": 0,  # This should warn
                                "@adjacentEnclosedSpace": "true",
                            },
                        ]
                    }
                }
            }
        }

        mock_model_data = MagicMock()
        mock_model_data.increment_counter.side_effect = [1, 2]
        mock_model_data.get_building_detail.return_value = "attached house"

        # Simulate wall processing workflow
        walls = ComponentExtractor.get_components_safe(h2k_dict, "Wall")

        processed_walls = []
        for wall in walls:
            wall_id = f"Wall{mock_model_data.increment_counter('wall')}"

            # Use utilities like real component would
            label = ValidationHelper.get_component_label(wall)

            with patch("h2k_hpxml.utils.common.h2k.get_number_field") as mock_get_field:
                mock_get_field.return_value = wall["wall_r_value"]
                r_value = ValidationHelper.validate_r_value(
                    wall, "wall_r_value", f"wall {label}", mock_model_data
                )

            facility_type = mock_model_data.get_building_detail("res_facility_type")
            exterior_adjacent = FacilityTypeHelper.determine_exterior_adjacent(wall, facility_type)

            processed_walls.append(
                {
                    "id": wall_id,
                    "label": label,
                    "r_value": r_value,
                    "exterior_adjacent": exterior_adjacent,
                }
            )

        # Verify results
        assert len(processed_walls) == 2

        # First wall should be fine
        assert processed_walls[0]["label"] == "North Wall"
        assert processed_walls[0]["r_value"] == 12.5
        assert processed_walls[0]["exterior_adjacent"] == "outside"

        # Second wall should have warning and different adjacency
        assert processed_walls[1]["label"] == "South Wall"
        assert processed_walls[1]["r_value"] == 0
        assert processed_walls[1]["exterior_adjacent"] == "other non-freezing space"

        # Should have one warning for zero R-value
        assert mock_model_data.add_warning_message.call_count == 1
