"""
Data-driven API for h2k-hpxml translation.

This module provides a RESTful API that exposes HPXML schema definitions,
validation rules, and field dependencies extracted from the existing 
processor implementations. It enables dynamic UI generation without
hardcoding field definitions.

Key Features:
- Schema endpoints for each domain (Environment, Envelope, Loads, HVAC)
- Real-time validation using existing processor validation rules
- Weather station data with Canadian climate information
- Field dependency mapping for conditional form generation
"""

# Note: Main API functions are available from the parent api module
# This avoids circular imports while keeping the structure clean

__version__ = "1.0.0"
__all__ = []