"""Examples showing before/after refactoring using common utilities."""

from ..utils import h2k
from ..utils import obj
from ..utils.common import ComponentExtractor
from ..utils.common import DataStructureHelpers
from ..utils.common import ErrorHandlingPatterns
from ..utils.common import FacilityTypeHelper
from ..utils.common import ValidationHelper


# BEFORE: Common patterns repeated across components
def old_component_pattern(h2k_dict, model_data):
    """Example of old repetitive pattern."""
    # Pattern 1: Getting components safely (repeated everywhere)
    components = obj.get_val(h2k_dict, "HouseFile,House,Components")
    if "Wall" not in components.keys():
        h2k_walls = []
    else:
        h2k_walls = components["Wall"]

    # Pattern 2: Ensure list format (repeated everywhere)
    h2k_walls = h2k_walls if isinstance(h2k_walls, list) else [h2k_walls]

    hpxml_components = []
    for wall in h2k_walls:
        # Pattern 3: Counter management (repeated everywhere)
        model_data.inc_wall_count()
        wall_id = f"Wall{model_data.get_wall_count()}"

        # Pattern 4: Label extraction (repeated everywhere)
        wall_label = wall.get("Label", "No Label")

        # Pattern 5: R-value validation (repeated everywhere)
        wall_rval = h2k.get_number_field(wall, "wall_r_value")
        if wall_rval <= 0:
            model_data.add_warning_message(
                {
                    "message": f"The wall component {wall_label} has a zero (0) R-value. "
                    f"Please reopen the h2k file in HOT2000, navigate to the affected component, "
                    f"and ensure the correct value is shown before re-saving the file."
                }
            )

        # Pattern 6: Facility type logic (repeated everywhere)
        model_data.get_building_detail("res_facility_type")

        # Component-specific processing...
        hpxml_components.append(
            {"SystemIdentifier": {"@id": wall_id}, "Label": wall_label, "RValue": wall_rval}
        )

    return hpxml_components


# AFTER: Using extracted utilities
def new_component_pattern(h2k_dict, model_data):
    """Example using extracted utilities."""

    def process_single_wall(wall, wall_id, model_data):
        """Process individual wall using utilities."""
        # Pattern 1-2: Safe extraction handled by utility
        # Pattern 3: Counter management handled by utility
        # Pattern 4: Label extraction using utility
        wall_label = ValidationHelper.get_component_label(wall)

        # Pattern 5: R-value validation using utility
        wall_rval = ValidationHelper.validate_r_value(
            wall, "wall_r_value", f"wall component {wall_label}", model_data
        )

        # Pattern 6: Facility type logic using utility
        res_facility_type = model_data.get_building_detail("res_facility_type")
        exterior_adjacent = FacilityTypeHelper.determine_exterior_adjacent(wall, res_facility_type)

        return {
            "SystemIdentifier": {"@id": wall_id},
            "Label": wall_label,
            "RValue": wall_rval,
            "ExteriorAdjacentTo": exterior_adjacent,
        }

    # All patterns 1-3 handled by extract_and_process_components utility
    return ComponentExtractor.process_component_with_counter(
        ComponentExtractor.get_components_safe(h2k_dict, "Wall"),
        model_data,
        "wall",
        "Wall",
        process_single_wall,
    )


# Example showing error handling pattern extraction
def old_error_handling_pattern():
    """Example of old error handling."""
    try:
        data = {"nested": {"deep": {"value": 42}}}
        # Manual nested access with potential failures
        value = data["nested"]["deep"]["value"]
        return float(value)
    except (KeyError, ValueError, TypeError):
        return 0.0


def new_error_handling_pattern():
    """Example using utility error handling."""
    data = {"nested": {"deep": {"value": 42}}}

    # Safe nested value extraction
    value = ErrorHandlingPatterns.safe_get_nested_value(data, "nested,deep,value", default=0.0)

    # Safe numeric conversion
    return ErrorHandlingPatterns.safe_numeric_conversion(value, float, 0.0)


# Example showing data structure pattern extraction
def old_data_structure_patterns():
    """Example of old repetitive data structure operations."""
    # Pattern: Ensure list
    data = "single_item"  # or could be list
    if not isinstance(data, list):
        data = [data] if data is not None else []

    # Pattern: Filter None values
    dict_data = {"a": 1, "b": None, "c": 3}
    filtered = {}
    for k, v in dict_data.items():
        if v is not None:
            filtered[k] = v

    # Pattern: Group by key
    items = [{"type": "A", "value": 1}, {"type": "B", "value": 2}, {"type": "A", "value": 3}]
    groups = {}
    for item in items:
        key = item.get("type")
        if key not in groups:
            groups[key] = []
        groups[key].append(item)

    return data, filtered, groups


def new_data_structure_patterns():
    """Example using utility data structure helpers."""
    # Pattern: Ensure list
    data = DataStructureHelpers.ensure_list("single_item")

    # Pattern: Filter None values
    dict_data = {"a": 1, "b": None, "c": 3}
    filtered = DataStructureHelpers.filter_none_values(dict_data)

    # Pattern: Group by key
    items = [{"type": "A", "value": 1}, {"type": "B", "value": 2}, {"type": "A", "value": 3}]
    groups = DataStructureHelpers.group_by_key(items, "type")

    return data, filtered, groups


# Summary of benefits:
"""
Benefits of extracted utilities:

1. **Code Reduction**: 40+ lines of repetitive code reduced to 10-15 lines
2. **Consistency**: Same logic applied consistently across all components
3. **Maintainability**: Bug fixes and improvements in one place
4. **Testability**: Utilities can be unit tested independently
5. **Readability**: Component code focuses on business logic, not boilerplate
6. **Error Handling**: Centralized error handling patterns reduce bugs
7. **Type Safety**: Utilities have proper type hints and validation

Common patterns extracted:
- Component extraction from H2K dictionary
- Counter management and ID generation
- Label extraction with fallbacks
- R-value validation with warnings
- Facility type determinations
- Error handling for nested data access
- Data structure normalization
- Path operations and validation
- File processing patterns
- CLI argument processing
"""
