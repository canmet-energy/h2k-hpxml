"""
Type definitions and aliases for the H2K-HPXML package.

This module defines common type aliases used throughout the codebase
to improve type safety and code documentation.
"""

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Tuple
from typing import Union

# Configuration types
ConfigDict = Dict[str, Any]
ConfigValue = Union[str, int, float, bool, None]

# XML/Dictionary types
XMLDict = Dict[str, Any]
H2KDict = XMLDict
HPXMLDict = XMLDict

# Path types
PathLike = Union[str, Path]

# Translation types
TranslationMode = str  # "SOC", "ASHRAE140", etc.
WeatherVintage = str  # "CWEC2020", "EWY2020", etc.
WeatherLibrary = str  # "historic", etc.

# Building component types
ComponentID = str
ComponentDict = Dict[str, Any]

# Numeric types with units
Temperature = float  # Celsius
Area = float  # m²
Volume = float  # m³
Length = float  # m
Efficiency = float  # decimal (0.0-1.0)
RValue = float  # m²K/W
UValue = float  # W/m²K

# Error context types
ErrorContext = Dict[str, Any]

# Model data types
ModelDataDict = Dict[str, Any]
BuildingDetails = Dict[str, Any]
FoundationDetails = Dict[str, Any]
WallSegment = Dict[str, Any]

# Result types
TranslationResult = str  # HPXML string
ValidationResult = Tuple[bool, str]  # (success, translation_mode)

# Logger types
LogLevel = str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

# File processing types
FileContent = str
FileEncoding = str
