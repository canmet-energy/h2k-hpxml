"""
Type definitions and aliases for the H2K-HPXML package.

This module defines common type aliases used throughout the codebase
to improve type safety and code documentation.
"""


# Configuration types
ConfigDict = dict
ConfigValue = object

# XML/Dictionary types
XMLDict = dict
H2KDict = XMLDict
HPXMLDict = XMLDict

# Path types
PathLike = object

# Translation types
TranslationMode = str  # "SOC", "ASHRAE140", etc.
WeatherVintage = str  # "CWEC2020", "EWY2020", etc.
WeatherLibrary = str  # "historic", etc.

# Building component types
ComponentID = str
ComponentDict = dict

# Numeric types with units
Temperature = float  # Celsius
Area = float  # m²
Volume = float  # m³
Length = float  # m
Efficiency = float  # decimal (0.0-1.0)
RValue = float  # m²K/W
UValue = float  # W/m²K

# Error context types
ErrorContext = dict

# Model data types
ModelDataDict = dict
BuildingDetails = dict
FoundationDetails = dict
WallSegment = dict

# Result types
TranslationResult = str  # HPXML string
ValidationResult = tuple  # (success, translation_mode)

# Logger types
LogLevel = str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

# File processing types
FileContent = str
FileEncoding = str
