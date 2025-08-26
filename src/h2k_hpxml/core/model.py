"""
Improved model data management for H2K to HPXML translation.

This module provides a simplified ModelData class using @property decorators
and better data organization to reduce boilerplate code.
"""


from ..types import BuildingDetails
from ..types import ComponentID
from ..types import FoundationDetails
from ..types import WallSegment
from ..utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


class CounterManager:
    """Manages all component counters with automatic increment methods."""

    def __init__(self):
        self.window = 0
        self.door = 0
        self.floor_header = 0
        self.wall = 0
        self.floor = 0
        self.ceiling = 0
        self.attic = 0
        self.roof = 0
        self.foundation = 0
        self.foundation_wall = 0
        self.crawlspace = 0
        self.slab = 0

    def increment(self, counter_name):
        """Increment a counter by name and return new value."""
        if hasattr(self, counter_name):
            current = getattr(self, counter_name)
            setattr(self, counter_name, current + 1)
            return current + 1
        else:
            raise ValueError(f"Unknown counter: {counter_name}")

    def get(self, counter_name):
        """Get current counter value."""
        return getattr(self, counter_name, 0)


class SystemTracker:
    """Tracks HVAC and building system information."""

    def __init__(self):
        self.is_hvac_translated = False
        self.is_dhw_translated = False
        self.heating_distribution_type = None
        self.ac_hp_distribution_type = None
        self.suppl_heating_distribution_types = []
        self.system_ids = {"primary_heating": "HeatingSystem1"}
        self.flue_diameters = []

    def set_system_id(self, system_dict):
        """Set system IDs from dictionary."""
        self.system_ids.update(system_dict)

    def get_system_id(self, key, default=None):
        """Get system ID with default fallback."""
        return self.system_ids.get(key, default)

    def add_flue_diameter(self, diameter):
        """Add flue diameter to list."""
        self.flue_diameters.append(diameter)


class ModelData:
    """
    Simplified model data container for H2K to HPXML translation.

    Uses @property decorators and dataclasses to reduce boilerplate code
    while maintaining full compatibility with existing code.
    """

    def __init__(self):
        # Core data structures
        self._building_details = {"building_type": "house", "murb_units": 0}
        self._foundation_details = []
        self._wall_segments = []
        self._warnings_list = []
        self._error_list = []

        # Use classes for organized data management
        self._counters = CounterManager()
        self._systems = SystemTracker()

        # Results storage
        self._results = {
            "General": {},
            "SOC": {},
            "Reference": {},
        }

    # Building details with improved interface
    def __getitem__(self, key):
        """Get building detail by key (maintains compatibility)."""
        return self._building_details.get(key, key)

    def __setitem__(self, key, value):
        """Set building detail by key (maintains compatibility)."""
        self._building_details[key] = value

    @property
    def building_details(self):
        """Access to building details dictionary."""
        return self._building_details

    def set_building_details(self, details):
        """Set multiple building details from dictionary."""
        self._building_details.update(details)

    def get_building_detail(self, key, default=None):
        """Get building detail with default fallback."""
        return self._building_details.get(key, default)

    # Foundation and wall tracking with validation
    @property
    def foundation_details(self):
        """Get foundation details list."""
        return self._foundation_details

    def add_foundation_detail(self, detail):
        """Add foundation detail with validation."""
        if not isinstance(detail, dict):
            raise ValueError("Foundation detail must be a dictionary")

        # Basic validation
        required_fields = ["type"]  # Add more as needed
        for required_field in required_fields:
            if required_field not in detail:
                logger.warning(f"Foundation detail missing required field: {required_field}")

        self._foundation_details.append(detail)

    @property
    def wall_segments(self):
        """Get wall segments list."""
        return self._wall_segments

    def add_wall_segment(self, segment):
        """Add wall segment with validation."""
        if not isinstance(segment, dict):
            raise ValueError("Wall segment must be a dictionary")

        self._wall_segments.append(segment)

    # Counter management with simplified interface
    @property
    def counters(self):
        """Access to counter manager."""
        return self._counters

    def increment_counter(self, counter_name):
        """Increment any counter by name."""
        return self._counters.increment(counter_name)

    # Maintain compatibility with old counter methods
    def inc_window_count(self):
        """Increment window counter."""
        self._counters.increment("window")

    def inc_door_count(self):
        """Increment door counter."""
        self._counters.increment("door")

    def inc_wall_count(self) -> None:
        """Increment wall counter."""
        self._counters.increment("wall")

    def inc_floor_count(self):
        """Increment floor counter."""
        self._counters.increment("floor")

    def inc_ceiling_count(self):
        """Increment ceiling counter."""
        self._counters.increment("ceiling")

    def inc_floor_header_count(self):
        """Increment floor header counter."""
        self._counters.increment("floor_header")

    def inc_attic_count(self):
        """Increment attic counter."""
        self._counters.increment("attic")

    def inc_roof_count(self):
        """Increment roof counter."""
        self._counters.increment("roof")

    def inc_foundation_count(self):
        """Increment foundation counter."""
        self._counters.increment("foundation")

    def inc_foundation_wall_count(self):
        """Increment foundation wall counter."""
        self._counters.increment("foundation_wall")

    def inc_crawlspace_count(self):
        """Increment crawlspace counter."""
        self._counters.increment("crawlspace")

    def inc_slab_count(self):
        """Increment slab counter."""
        self._counters.increment("slab")

    # Counter getters using properties
    @property
    def window_count(self):
        return self._counters.window

    @property
    def door_count(self):
        return self._counters.door

    @property
    def wall_count(self):
        return self._counters.wall

    @property
    def floor_count(self):
        return self._counters.floor

    @property
    def ceiling_count(self):
        return self._counters.ceiling

    @property
    def floor_header_count(self):
        return self._counters.floor_header

    @property
    def attic_count(self):
        return self._counters.attic

    @property
    def roof_count(self):
        return self._counters.roof

    @property
    def foundation_count(self):
        return self._counters.foundation

    @property
    def foundation_wall_count(self):
        return self._counters.foundation_wall

    @property
    def crawlspace_count(self):
        return self._counters.crawlspace

    @property
    def slab_count(self):
        return self._counters.slab

    # Legacy getter methods for backward compatibility
    def get_window_count(self):
        return self.window_count

    def get_door_count(self):
        return self.door_count

    def get_wall_count(self):
        return self.wall_count

    def get_floor_count(self):
        return self.floor_count

    def get_ceiling_count(self):
        return self.ceiling_count

    def get_floor_header_count(self):
        return self.floor_header_count

    def get_attic_count(self):
        return self.attic_count

    def get_roof_count(self):
        return self.roof_count

    def get_foundation_count(self):
        return self.foundation_count

    def get_foundation_wall_count(self):
        return self.foundation_wall_count

    def get_crawlspace_count(self):
        return self.crawlspace_count

    def get_slab_count(self):
        return self.slab_count

    def get_foundation_details(self):
        """Get foundation details (legacy compatibility)."""
        return self.foundation_details

    def get_wall_segments(self):
        """Get wall segments (legacy compatibility)."""
        return self.wall_segments

    # System tracking with properties
    @property
    def systems(self):
        """Access to system tracker."""
        return self._systems

    @property
    def is_hvac_translated(self):
        return self._systems.is_hvac_translated

    @is_hvac_translated.setter
    def is_hvac_translated(self, value):
        self._systems.is_hvac_translated = value

    @property
    def is_dhw_translated(self):
        return self._systems.is_dhw_translated

    @is_dhw_translated.setter
    def is_dhw_translated(self, value):
        self._systems.is_dhw_translated = value

    @property
    def heating_distribution_type(self):
        return self._systems.heating_distribution_type

    @heating_distribution_type.setter
    def heating_distribution_type(self, value):
        self._systems.heating_distribution_type = value

    @property
    def ac_hp_distribution_type(self):
        return self._systems.ac_hp_distribution_type

    @ac_hp_distribution_type.setter
    def ac_hp_distribution_type(self, value):
        self._systems.ac_hp_distribution_type = value

    # Legacy system methods for backward compatibility
    def set_is_hvac_translated(self, value):
        self.is_hvac_translated = value

    def get_is_hvac_translated(self):
        return self.is_hvac_translated

    def set_is_dhw_translated(self, value):
        self.is_dhw_translated = value

    def get_is_dhw_translated(self):
        return self.is_dhw_translated

    def set_heating_distribution_type(self, value):
        self.heating_distribution_type = value

    def get_heating_distribution_type(self):
        return self.heating_distribution_type

    def set_ac_hp_distribution_type(self, value):
        self.ac_hp_distribution_type = value

    def get_ac_hp_distribution_type(self):
        return self.ac_hp_distribution_type

    def set_suppl_heating_distribution_types(self, value):
        self._systems.suppl_heating_distribution_types = value

    def get_suppl_heating_distribution_types(self):
        return self._systems.suppl_heating_distribution_types

    def set_flue_diameters(self, diameter):
        """Add flue diameter to list."""
        self._systems.add_flue_diameter(diameter)

    def get_flue_diameters(self):
        return self._systems.flue_diameters

    def set_system_id(self, system_dict):
        self._systems.set_system_id(system_dict)

    def get_system_id(self, key, default=None):
        return self._systems.get_system_id(key, default)

    # Warning and error management
    @property
    def warnings_list(self):
        """Get warnings list."""
        return self._warnings_list

    def add_warning_message(self, message):
        """Add a warning message and log it."""
        if isinstance(message, dict):
            warning_text = message.get("message", str(message))
        else:
            warning_text = str(message)
            message = {"message": warning_text}

        self._warnings_list.append(message)
        logger.warning(f"H2K Translation Warning: {warning_text}")

    def get_warning_messages(self):
        """Get all warning messages."""
        return self.warnings_list

    @property
    def error_list(self):
        """Get error list."""
        return self._error_list

    # Results management (simplified)
    @property
    def results(self):
        """Get results dictionary."""
        return self._results

    def set_results(self, h2k_dict=None):
        """Set results from H2K dictionary."""
        if h2k_dict is None:
            h2k_dict = {}

        file_results = h2k_dict.get("HouseFile", {}).get("AllResults", {}).get("Results", [])

        if isinstance(file_results, list):
            for res in file_results:
                house_code = res.get("@houseCode", "")
                upgrade_case = "@type" in res.keys()

                if (
                    house_code == "UserHouse" or "@houseCode" not in res.keys()
                ) and not upgrade_case:
                    self._results["General"] = res
                elif house_code == "SOC" and not upgrade_case:
                    self._results["SOC"] = res
                elif house_code == "Reference" and not upgrade_case:
                    self._results["Reference"] = res

    def get_results(self, res_type=""):
        """Get results by type."""
        if res_type == "":
            # Return SOC results if available, otherwise general
            soc_results = self._results.get("SOC", {})
            if soc_results:
                return soc_results
            return self._results.get("General", {})
        else:
            return self._results.get(res_type, {})
