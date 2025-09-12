"""
Domain definitions for categorizing HPXML fields.

This module defines the logical groupings of HPXML fields into domains
that make sense for UI organization and user workflow.
"""

from typing import Dict, List, Set
from enum import Enum

class HPXMLDomain(Enum):
    """HPXML field domains for UI organization."""
    ENVIRONMENT = "environment"
    ENVELOPE = "envelope"
    LOADS = "loads" 
    HVAC = "hvac"

# Keywords for automatic domain classification
DOMAIN_KEYWORDS = {
    HPXMLDomain.ENVIRONMENT: [
        "weather", "climate", "site", "location", "azimuth", "shielding", 
        "soil", "conductivity", "orientation", "epw", "station"
    ],
    HPXMLDomain.ENVELOPE: [
        "wall", "window", "door", "roof", "ceiling", "floor", "foundation", 
        "basement", "crawlspace", "slab", "insulation", "rvalue", "uvalue",
        "frame", "assembly", "thermal", "infiltration", "leakage"
    ],
    HPXMLDomain.LOADS: [
        "occupancy", "appliance", "lighting", "plug", "resident", "bedroom", 
        "bathroom", "schedule", "usage", "load", "equipment", "fixture"
    ],
    HPXMLDomain.HVAC: [
        "heating", "cooling", "hvac", "ventilation", "distribution", "system",
        "furnace", "boiler", "heat_pump", "air_conditioning", "duct", "fan"
    ]
}

def categorize_field(field_path: str, processor: str = None) -> HPXMLDomain:
    """
    Categorize an HPXML field into a domain based on keywords and context.
    
    Args:
        field_path: The full HPXML field path
        processor: Optional processor name for additional context
        
    Returns:
        The most appropriate HPXMLDomain for this field
    """
    field_lower = field_path.lower()
    
    # Check processor name first for additional context
    if processor:
        if "weather" in processor:
            return HPXMLDomain.ENVIRONMENT
        elif "enclosure" in processor:
            return HPXMLDomain.ENVELOPE
        elif "system" in processor:
            return HPXMLDomain.HVAC
        elif "baseload" in processor or "appliance" in processor or "lighting" in processor:
            return HPXMLDomain.LOADS
    
    # Check field path keywords
    domain_scores = {domain: 0 for domain in HPXMLDomain}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in field_lower:
                domain_scores[domain] += 1
    
    # Return domain with highest score, defaulting to ENVELOPE for ties
    max_score = max(domain_scores.values())
    if max_score == 0:
        return HPXMLDomain.ENVELOPE  # Default domain
    
    for domain, score in domain_scores.items():
        if score == max_score:
            return domain
    
    return HPXMLDomain.ENVELOPE

def get_domain_display_name(domain: HPXMLDomain) -> str:
    """Get user-friendly display name for domain."""
    display_names = {
        HPXMLDomain.ENVIRONMENT: "Environment & Site",
        HPXMLDomain.ENVELOPE: "Building Envelope", 
        HPXMLDomain.LOADS: "Loads & Occupancy",
        HPXMLDomain.HVAC: "HVAC Systems"
    }
    return display_names[domain]

def get_domain_description(domain: HPXMLDomain) -> str:
    """Get detailed description for domain."""
    descriptions = {
        HPXMLDomain.ENVIRONMENT: "Weather data, site conditions, building orientation, and geographic information",
        HPXMLDomain.ENVELOPE: "Building enclosure components including walls, windows, doors, roof, and insulation",
        HPXMLDomain.LOADS: "Internal loads from occupancy, appliances, lighting, and equipment usage patterns", 
        HPXMLDomain.HVAC: "Heating, cooling, ventilation systems and distribution equipment"
    }
    return descriptions[domain]