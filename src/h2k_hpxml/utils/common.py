"""Common utility functions for H2K-HPXML components and processing."""

import logging
import os
from pathlib import Path

from ..core import data_utils as obj
from ..core import h2k_parser as h2k

# Get logger for this module
logger = logging.getLogger(__name__)


class ComponentExtractor:
    """Utility class for extracting H2K components with common patterns."""

    @staticmethod
    def get_components_safe(h2k_dict, component_type):
        """
        Safely extract components from H2K dictionary.

        Args:
            h2k_dict: H2K dictionary containing house data
            component_type: Type of component to extract (e.g., 'Wall', 'Floor')

        Returns:
            List of component dictionaries, empty list if none found
        """
        components = obj.get_val(h2k_dict, "HouseFile,House,Components")

        if component_type not in components.keys():
            return []

        component_data = components[component_type]

        # Always return as list for consistent processing
        return component_data if isinstance(component_data, list) else [component_data]

    @staticmethod
    def process_component_with_counter(
        h2k_components,
        model_data,
        counter_name,
        id_prefix,
        processor_func,
    ):
        """
        Process components with automatic counter management.

        Args:
            h2k_components: List of H2K component dictionaries
            model_data: Model data object for counter management
            counter_name: Name of counter to increment ('wall', 'floor', etc.)
            id_prefix: Prefix for generated IDs ('Wall', 'Floor', etc.)
            processor_func: Function to process individual component

        Returns:
            List of processed HPXML components
        """
        hpxml_components = []

        for component in h2k_components:
            # Increment counter and generate ID
            count = model_data.increment_counter(counter_name)
            component_id = f"{id_prefix}{count}"

            # Process the component
            processed = processor_func(component, component_id, model_data)
            if processed:
                hpxml_components.append(processed)

        return hpxml_components


class ValidationHelper:
    """Utility class for common validation patterns."""

    @staticmethod
    def validate_r_value(component, r_value_field, component_label, model_data):
        """
        Validate R-value and add warning if invalid.

        Args:
            component: Component dictionary
            r_value_field: Field name for R-value
            component_label: Label for warning messages
            model_data: Model data for warning collection

        Returns:
            R-value as float
        """
        r_value = h2k.get_number_field(component, r_value_field)

        if r_value <= 0:
            model_data.add_warning_message(
                {
                    "message": f"The {component_label} has a zero (0) R-value. "
                    f"Please reopen the h2k file in HOT2000, navigate to the affected component, "
                    f"and ensure the correct value is shown before re-saving the file.",
                    "code": "ZERO_R_VALUE",
                    "component": component_label,
                }
            )

        return r_value

    @staticmethod
    def get_component_label(component, default="No Label"):
        """Get component label with fallback."""
        return component.get("Label", default)

    @staticmethod
    def calculate_area_from_dimensions(
        height: float, perimeter: float, precision: int = 2
    ) -> float:
        """Calculate area from height and perimeter with rounding."""
        return round(height * perimeter, precision)


class FacilityTypeHelper:
    """Utility class for facility type determinations."""

    @staticmethod
    def is_attached_unit(res_facility_type):
        """Determine if residence is attached unit type."""
        return "attached" in res_facility_type or "apartment" in res_facility_type

    @staticmethod
    def get_buffered_attached_type(res_facility_type):
        """Get buffered space type for attached units."""
        return (
            "other non-freezing space"
            if FacilityTypeHelper.is_attached_unit(res_facility_type)
            else "outside"
        )

    @staticmethod
    def determine_exterior_adjacent(component, res_facility_type):
        """Determine exterior adjacency for component."""
        buffered_type = FacilityTypeHelper.get_buffered_attached_type(res_facility_type)

        return buffered_type if component.get("@adjacentEnclosedSpace") == "true" else "outside"


class PathUtilities:
    """Utility functions for path operations."""

    @staticmethod
    def ensure_path_exists(path, create_parents=True):
        """
        Ensure path exists, creating parent directories if needed.

        Args:
            path: Path to check/create
            create_parents: Whether to create parent directories

        Returns:
            Path object

        Raises:
            OSError: If path cannot be created
        """
        path_obj = Path(path)

        if not path_obj.exists():
            if create_parents and not path_obj.parent.exists():
                try:
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created parent directories for: {path_obj}")
                except OSError as e:
                    logger.error(f"Failed to create parent directories for {path_obj}: {e}")
                    raise

        return path_obj

    @staticmethod
    def validate_file_path(file_path):
        """
        Validate that a file path exists and is readable.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            return False, f"File does not exist: {path_obj}"

        if not path_obj.is_file():
            return False, f"Path is not a file: {path_obj}"

        if not os.access(path_obj, os.R_OK):
            return False, f"File is not readable: {path_obj}"

        return True, ""

    @staticmethod
    def get_relative_path(file_path, base_path):
        """Get relative path from base path."""
        return Path(file_path).relative_to(Path(base_path))


class ErrorHandlingPatterns:
    """Common error handling patterns."""

    @staticmethod
    def safe_get_nested_value(data, path, default=None, separator=","):
        """
        Safely get nested dictionary value with path notation.

        Args:
            data: Dictionary to search
            path: Comma-separated path (e.g., "HouseFile,House,Components")
            default: Default value if path not found
            separator: Path separator character

        Returns:
            Value at path or default
        """
        try:
            # Manual path traversal to properly detect missing keys
            current = data
            for key in path.split(separator):
                if not isinstance(current, dict) or key not in current:
                    return default
                current = current[key]
            return current
        except (KeyError, AttributeError, TypeError) as e:
            logger.debug(f"Failed to get nested value at path '{path}': {e}")
            return default

    @staticmethod
    def safe_numeric_conversion(value, conversion_type=float, default=0.0):
        """
        Safely convert value to numeric type.

        Args:
            value: Value to convert
            conversion_type: Target type (int or float)
            default: Default value if conversion fails

        Returns:
            Converted value or default
        """
        try:
            return conversion_type(value)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to convert '{value}' to {conversion_type.__name__}: {e}")
            return default

    @staticmethod
    def collect_processing_errors(func):
        """
        Decorator to collect processing errors without stopping execution.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function that collects errors
        """

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                # If model_data is available in args, add warning
                if len(args) > 1 and hasattr(args[1], "add_warning_message"):
                    args[1].add_warning_message(
                        {
                            "message": f"Processing error in {func.__name__}: {str(e)}",
                            "code": "PROCESSING_ERROR",
                            "function": func.__name__,
                        }
                    )
                return None

        return wrapper


class DataStructureHelpers:
    """Helpers for common data structure operations."""

    @staticmethod
    def ensure_list(data):
        """Ensure data is returned as a list."""
        if data is None:
            return []
        return data if isinstance(data, list) else [data]

    @staticmethod
    def merge_dictionaries(*dicts):
        """Merge multiple dictionaries, with later ones taking precedence."""
        result = {}
        for d in dicts:
            if d:
                result.update(d)
        return result

    @staticmethod
    def filter_none_values(data):
        """Remove None values from dictionary."""
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def group_by_key(items, key):
        """Group list of dictionaries by a specific key."""
        groups = {}
        for item in items:
            group_key = item.get(key)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
        return groups


class IDGenerators:
    """Utility functions for generating consistent IDs."""

    @staticmethod
    def generate_component_id(prefix, counter, suffix=""):
        """Generate component ID with consistent formatting."""
        base_id = f"{prefix}{counter}"
        return f"{base_id}{suffix}" if suffix else base_id

    @staticmethod
    def generate_system_id(system_type, counter):
        """Generate system ID with consistent formatting."""
        return f"{system_type.title()}System{counter}"

    @staticmethod
    def sanitize_label_for_id(label, max_length=20):
        """Sanitize label text for use in IDs."""
        # Remove special characters and spaces, limit length
        sanitized = "".join(c for c in label if c.isalnum() or c in "_-")
        return sanitized[:max_length] if len(sanitized) > max_length else sanitized


# Convenience functions that combine multiple utilities
def extract_and_process_components(
    h2k_dict,
    component_type,
    model_data,
    counter_name,
    id_prefix,
    processor_func,
):
    """
    Complete workflow to extract and process H2K components.

    Args:
        h2k_dict: H2K dictionary
        component_type: Component type to extract
        model_data: Model data object
        counter_name: Counter name for model_data
        id_prefix: ID prefix for generated components
        processor_func: Function to process each component

    Returns:
        List of processed HPXML components
    """
    h2k_components = ComponentExtractor.get_components_safe(h2k_dict, component_type)

    return ComponentExtractor.process_component_with_counter(
        h2k_components, model_data, counter_name, id_prefix, processor_func
    )


def validate_and_warn_r_value(
    component,
    r_value_field,
    model_data,
    component_type="component",
):
    """
    Validate R-value with automatic label detection and warning.

    Args:
        component: Component dictionary
        r_value_field: R-value field name
        model_data: Model data for warnings
        component_type: Type of component for warning message

    Returns:
        R-value as float
    """
    label = ValidationHelper.get_component_label(component)
    full_label = f"{component_type} {label}" if label != "No Label" else component_type

    return ValidationHelper.validate_r_value(component, r_value_field, full_label, model_data)
