"""
Custom exception classes for H2K-HPXML translation.

This module defines application-specific exceptions to provide better
error handling and more informative error messages throughout the system.
"""


class H2KHPXMLError(Exception):
    """Base exception class for all H2K-HPXML application errors.

    This serves as the root exception class that all other application-specific
    exceptions inherit from, allowing for easy catching of all application errors.
    """

    def __init__(self, message, details=None):
        """Initialize H2K-HPXML base error.

        Args:
            message: Human-readable error message
            details: Optional dictionary containing additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class H2KParsingError(H2KHPXMLError):
    """Exception raised when H2K file parsing fails.

    This exception is raised when the input H2K file cannot be parsed,
    either due to invalid XML structure, missing required fields, or
    unsupported H2K file formats.
    """

    def __init__(
        self,
        message,
        h2k_file_path=None,
        xml_error=None,
    ):
        """Initialize H2K parsing error.

        Args:
            message: Human-readable error message
            h2k_file_path: Path to the H2K file that failed to parse
            xml_error: Original XML parsing exception if available
        """
        details = {}
        if h2k_file_path:
            details["h2k_file_path"] = h2k_file_path
        if xml_error:
            details["xml_error"] = str(xml_error)
            details["xml_error_type"] = type(xml_error).__name__

        super().__init__(message, details)
        self.h2k_file_path = h2k_file_path
        self.xml_error = xml_error


class HPXMLGenerationError(H2KHPXMLError):
    """Exception raised when HPXML generation fails.

    This exception is raised when the translation process fails to generate
    valid HPXML output, either due to missing data, invalid transformations,
    or HPXML format violations.
    """

    def __init__(self, message, component=None, h2k_data=None):
        """Initialize HPXML generation error.

        Args:
            message: Human-readable error message
            component: Name of the component that failed to translate
            h2k_data: Relevant H2K data that caused the failure
        """
        details = {}
        if component:
            details["component"] = component
        if h2k_data:
            details["h2k_data_keys"] = (
                str(list(h2k_data.keys())) if isinstance(h2k_data, dict) else str(type(h2k_data))
            )

        super().__init__(message, details)
        self.component = component
        self.h2k_data = h2k_data


class ConfigurationError(H2KHPXMLError):
    """Exception raised when configuration is invalid or missing.

    This exception is raised when the application configuration is invalid,
    missing required settings, or contains conflicting values.
    """

    def __init__(self, message, config_key=None, config_value=None):
        """Initialize configuration error.

        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            config_value: Invalid configuration value
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value

        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class DependencyError(H2KHPXMLError):
    """Exception raised when required dependencies are missing or invalid.

    This exception is raised when OpenStudio, OpenStudio-HPXML, or other
    required dependencies are not found, incorrectly installed, or incompatible.
    """

    def __init__(
        self,
        message,
        dependency_name=None,
        expected_version=None,
        found_version=None,
    ):
        """Initialize dependency error.

        Args:
            message: Human-readable error message
            dependency_name: Name of the missing or invalid dependency
            expected_version: Expected version of the dependency
            found_version: Actually found version (if any)
        """
        details = {}
        if dependency_name:
            details["dependency_name"] = dependency_name
        if expected_version:
            details["expected_version"] = expected_version
        if found_version:
            details["found_version"] = found_version

        super().__init__(message, details)
        self.dependency_name = dependency_name
        self.expected_version = expected_version
        self.found_version = found_version


class ValidationError(H2KHPXMLError):
    """Exception raised when input validation fails.

    This exception is raised when input data fails validation checks,
    such as invalid file formats, out-of-range values, or missing required fields.
    """

    def __init__(
        self,
        message,
        field_name=None,
        field_value=None,
        validation_rule=None,
    ):
        """Initialize validation error.

        Args:
            message: Human-readable error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            validation_rule: Description of the validation rule that was violated
        """
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = field_value
        if validation_rule:
            details["validation_rule"] = validation_rule

        super().__init__(message, details)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule


class WeatherDataError(H2KHPXMLError):
    """Exception raised when weather data processing fails.

    This exception is raised when weather files cannot be found, downloaded,
    or processed, or when weather location mapping fails.
    """

    def __init__(
        self,
        message,
        weather_location=None,
        weather_file=None,
    ):
        """Initialize weather data error.

        Args:
            message: Human-readable error message
            weather_location: Weather location that caused the error
            weather_file: Weather file path that caused the error
        """
        details = {}
        if weather_location:
            details["weather_location"] = weather_location
        if weather_file:
            details["weather_file"] = weather_file

        super().__init__(message, details)
        self.weather_location = weather_location
        self.weather_file = weather_file


class SimulationError(H2KHPXMLError):
    """Exception raised when OpenStudio simulation fails.

    This exception is raised when the OpenStudio-HPXML simulation process
    fails, either due to invalid HPXML input, OpenStudio errors, or system issues.
    """

    def __init__(
        self,
        message,
        hpxml_file=None,
        simulation_log=None,
        return_code=None,
    ):
        """Initialize simulation error.

        Args:
            message: Human-readable error message
            hpxml_file: HPXML file that failed to simulate
            simulation_log: Simulation log output
            return_code: Process return code
        """
        details = {}
        if hpxml_file:
            details["hpxml_file"] = hpxml_file
        if simulation_log:
            details["simulation_log"] = simulation_log[:500]  # Truncate long logs
        if return_code is not None:
            details["return_code"] = str(return_code)

        super().__init__(message, details)
        self.hpxml_file = hpxml_file
        self.simulation_log = simulation_log
        self.return_code = return_code
