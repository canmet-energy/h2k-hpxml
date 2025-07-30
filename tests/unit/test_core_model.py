"""Unit tests for improved ModelData class."""

from unittest.mock import patch

import pytest

from h2k_hpxml.core.model import CounterManager
from h2k_hpxml.core.model import ModelData
from h2k_hpxml.core.model import SystemTracker


class TestCounterManager:
    """Test cases for CounterManager dataclass."""

    def test_counter_manager_initialization(self):
        """Test that CounterManager initializes with zero values."""
        counter = CounterManager()

        assert counter.window == 0
        assert counter.door == 0
        assert counter.wall == 0
        assert counter.floor == 0
        assert counter.ceiling == 0
        assert counter.foundation == 0

    def test_increment_valid_counter(self):
        """Test incrementing a valid counter."""
        counter = CounterManager()

        result = counter.increment("window")
        assert result == 1
        assert counter.window == 1

        result = counter.increment("window")
        assert result == 2
        assert counter.window == 2

    def test_increment_invalid_counter_raises_error(self):
        """Test that incrementing invalid counter raises ValueError."""
        counter = CounterManager()

        with pytest.raises(ValueError, match="Unknown counter: invalid"):
            counter.increment("invalid")

    def test_get_counter_value(self):
        """Test getting counter values."""
        counter = CounterManager()
        counter.wall = 5

        assert counter.get("wall") == 5
        assert counter.get("nonexistent") == 0  # Default for missing attribute


class TestSystemTracker:
    """Test cases for SystemTracker dataclass."""

    def test_system_tracker_initialization(self):
        """Test that SystemTracker initializes with correct defaults."""
        system = SystemTracker()

        assert system.is_hvac_translated is False
        assert system.is_dhw_translated is False
        assert system.heating_distribution_type is None
        assert system.ac_hp_distribution_type is None
        assert system.suppl_heating_distribution_types == []
        assert system.system_ids == {"primary_heating": "HeatingSystem1"}
        assert system.flue_diameters == []

    def test_set_system_id(self):
        """Test setting system IDs."""
        system = SystemTracker()

        system.set_system_id({"cooling": "CoolingSystem1", "heating": "HeatingSystem2"})

        assert system.system_ids["cooling"] == "CoolingSystem1"
        assert system.system_ids["heating"] == "HeatingSystem2"
        assert system.system_ids["primary_heating"] == "HeatingSystem1"  # Original preserved

    def test_get_system_id(self):
        """Test getting system IDs with defaults."""
        system = SystemTracker()
        system.system_ids["test"] = "TestSystem1"

        assert system.get_system_id("test") == "TestSystem1"
        assert system.get_system_id("nonexistent") is None
        assert system.get_system_id("nonexistent", "default") == "default"

    def test_add_flue_diameter(self):
        """Test adding flue diameters."""
        system = SystemTracker()

        system.add_flue_diameter(6.0)
        system.add_flue_diameter(8.0)

        assert system.flue_diameters == [6.0, 8.0]


class TestModelData:
    """Test cases for the improved ModelData class."""

    def test_model_data_initialization(self):
        """Test that ModelData initializes with correct defaults."""
        model = ModelData()

        # Check building details
        assert model.building_details == {"building_type": "house", "murb_units": 0}

        # Check lists are empty
        assert model.foundation_details == []
        assert model.wall_segments == []
        assert model.warnings_list == []
        assert model.error_list == []

        # Check counters and systems are initialized
        assert isinstance(model.counters, CounterManager)
        assert isinstance(model.systems, SystemTracker)

        # Check results structure
        expected_results = {"General": {}, "SOC": {}, "Reference": {}}
        assert model.results == expected_results

    def test_building_detail_access_methods(self):
        """Test building detail access methods."""
        model = ModelData()

        # Test __setitem__ and __getitem__
        model["test_key"] = "test_value"
        assert model["test_key"] == "test_value"

        # Test get_building_detail with default
        assert model.get_building_detail("test_key") == "test_value"
        assert model.get_building_detail("nonexistent", "default") == "default"

        # Test set_building_details
        model.set_building_details({"key1": "value1", "key2": "value2"})
        assert model["key1"] == "value1"
        assert model["key2"] == "value2"

    def test_foundation_detail_validation(self):
        """Test foundation detail validation."""
        model = ModelData()

        # Valid foundation detail
        valid_detail = {"type": "basement", "area": 100}
        model.add_foundation_detail(valid_detail)
        assert len(model.foundation_details) == 1
        assert model.foundation_details[0] == valid_detail

        # Invalid foundation detail (not a dict)
        with pytest.raises(ValueError, match="Foundation detail must be a dictionary"):
            model.add_foundation_detail("invalid")

        # Foundation detail missing required field should warn but not fail
        with patch("h2k_hpxml.core.model.logger") as mock_logger:
            incomplete_detail = {"area": 50}  # Missing 'type'
            model.add_foundation_detail(incomplete_detail)

            mock_logger.warning.assert_called_once_with(
                "Foundation detail missing required field: type"
            )
            assert len(model.foundation_details) == 2

    def test_wall_segment_validation(self):
        """Test wall segment validation."""
        model = ModelData()

        # Valid wall segment
        valid_segment = {"id": "wall1", "area": 50}
        model.add_wall_segment(valid_segment)
        assert len(model.wall_segments) == 1
        assert model.wall_segments[0] == valid_segment

        # Invalid wall segment (not a dict)
        with pytest.raises(ValueError, match="Wall segment must be a dictionary"):
            model.add_wall_segment("invalid")

    def test_counter_properties_and_methods(self):
        """Test counter properties and increment methods."""
        model = ModelData()

        # Test increment methods
        model.inc_window_count()
        model.inc_window_count()
        model.inc_wall_count()

        # Test property access
        assert model.window_count == 2
        assert model.wall_count == 1
        assert model.door_count == 0

        # Test legacy getter methods
        assert model.get_window_count() == 2
        assert model.get_wall_count() == 1
        assert model.get_door_count() == 0

        # Test generic increment method
        assert model.increment_counter("ceiling") == 1
        assert model.ceiling_count == 1

    def test_system_properties(self):
        """Test system tracking properties."""
        model = ModelData()

        # Test boolean properties
        assert model.is_hvac_translated is False
        model.is_hvac_translated = True
        assert model.is_hvac_translated is True

        # Test optional string properties
        assert model.heating_distribution_type is None
        model.heating_distribution_type = "ducted"
        assert model.heating_distribution_type == "ducted"

        # Test legacy methods
        model.set_is_dhw_translated(True)
        assert model.get_is_dhw_translated() is True

        model.set_heating_distribution_type("hydronic")
        assert model.get_heating_distribution_type() == "hydronic"

    def test_system_id_management(self):
        """Test system ID management."""
        model = ModelData()

        # Test setting system IDs
        model.set_system_id({"cooling": "CoolingSystem1", "heating": "HeatingSystem2"})

        assert model.get_system_id("cooling") == "CoolingSystem1"
        assert model.get_system_id("heating") == "HeatingSystem2"
        assert model.get_system_id("primary_heating") == "HeatingSystem1"  # Default preserved
        assert model.get_system_id("nonexistent") is None
        assert model.get_system_id("nonexistent", "default") == "default"

    def test_flue_diameter_management(self):
        """Test flue diameter management."""
        model = ModelData()

        # Test adding flue diameters
        model.set_flue_diameters(6.0)
        model.set_flue_diameters(8.0)

        diameters = model.get_flue_diameters()
        assert diameters == [6.0, 8.0]

    def test_supplemental_heating_distribution_types(self):
        """Test supplemental heating distribution types."""
        model = ModelData()

        types = ["ducted", "hydronic"]
        model.set_suppl_heating_distribution_types(types)

        assert model.get_suppl_heating_distribution_types() == types

    def test_warning_message_handling(self):
        """Test warning message handling with logging."""
        model = ModelData()

        with patch("h2k_hpxml.core.model.logger") as mock_logger:
            # Test string warning
            model.add_warning_message("Test warning")

            assert len(model.warnings_list) == 1
            assert model.warnings_list[0] == {"message": "Test warning"}
            mock_logger.warning.assert_called_with("H2K Translation Warning: Test warning")

            # Test dict warning
            warning_dict = {"message": "Dict warning", "code": "W001"}
            model.add_warning_message(warning_dict)

            assert len(model.warnings_list) == 2
            assert model.warnings_list[1] == warning_dict
            mock_logger.warning.assert_called_with("H2K Translation Warning: Dict warning")

        # Test legacy getter
        warnings = model.get_warning_messages()
        assert len(warnings) == 2

    def test_results_management(self):
        """Test results management."""
        model = ModelData()

        # Test setting results with empty dict
        model.set_results({})
        assert model.results == {"General": {}, "SOC": {}, "Reference": {}}

        # Test setting results with H2K data
        h2k_data = {
            "HouseFile": {
                "AllResults": {
                    "Results": [
                        {"@houseCode": "UserHouse", "energy": 1000},
                        {"@houseCode": "SOC", "energy": 800},
                        {"@houseCode": "Reference", "energy": 1200},
                        {
                            "@houseCode": "SOC",
                            "@type": "upgrade",
                            "energy": 700,
                        },  # Should be ignored
                    ]
                }
            }
        }

        model.set_results(h2k_data)

        assert model.results["General"] == {"@houseCode": "UserHouse", "energy": 1000}
        assert model.results["SOC"] == {"@houseCode": "SOC", "energy": 800}
        assert model.results["Reference"] == {"@houseCode": "Reference", "energy": 1200}

        # Test getting results
        assert model.get_results() == {"@houseCode": "SOC", "energy": 800}  # SOC preferred
        assert model.get_results("General") == {"@houseCode": "UserHouse", "energy": 1000}
        assert model.get_results("nonexistent") == {}

    def test_results_fallback_to_general(self):
        """Test that get_results falls back to General when SOC not available."""
        model = ModelData()

        h2k_data = {
            "HouseFile": {"AllResults": {"Results": [{"@houseCode": "UserHouse", "energy": 1000}]}}
        }

        model.set_results(h2k_data)

        # Should return General results when SOC not available
        assert model.get_results() == {"@houseCode": "UserHouse", "energy": 1000}

    def test_backward_compatibility_methods(self):
        """Test that all legacy methods are still available."""
        model = ModelData()

        # Test all legacy counter getters exist
        legacy_getters = [
            "get_window_count",
            "get_door_count",
            "get_wall_count",
            "get_floor_count",
            "get_ceiling_count",
            "get_floor_header_count",
            "get_attic_count",
            "get_roof_count",
            "get_foundation_count",
            "get_foundation_wall_count",
            "get_crawlspace_count",
            "get_slab_count",
        ]

        for getter in legacy_getters:
            assert hasattr(model, getter)
            assert callable(getattr(model, getter))

        # Test all legacy increment methods exist
        legacy_incrementers = [
            "inc_window_count",
            "inc_door_count",
            "inc_wall_count",
            "inc_floor_count",
            "inc_ceiling_count",
            "inc_floor_header_count",
            "inc_attic_count",
            "inc_roof_count",
            "inc_foundation_count",
            "inc_foundation_wall_count",
            "inc_crawlspace_count",
            "inc_slab_count",
        ]

        for incrementer in legacy_incrementers:
            assert hasattr(model, incrementer)
            assert callable(getattr(model, incrementer))

        # Test legacy data access methods exist
        legacy_methods = [
            "get_foundation_details",
            "get_wall_segments",
            "get_warning_messages",
            "set_building_details",
            "get_building_detail",
            "add_foundation_detail",
            "add_wall_segment",
        ]

        for method in legacy_methods:
            assert hasattr(model, method)
            assert callable(getattr(model, method))
