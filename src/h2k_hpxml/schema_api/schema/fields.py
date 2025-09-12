"""
HPXML field definitions and metadata extraction.

This module provides utilities to extract field information from the existing
processors and components to build comprehensive field schemas.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from .domains import HPXMLDomain, categorize_field

@dataclass 
class FieldDefinition:
    """Complete definition of an HPXML field."""
    name: str
    field_path: str
    data_type: str
    domain: HPXMLDomain
    processor: str
    is_required: bool = False
    default_value: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    units: Optional[str] = None
    description: str = ""
    validation_rules: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []
        if self.dependencies is None:
            self.dependencies = []

class FieldExtractor:
    """Extracts field definitions from processor and component files."""
    
    def __init__(self):
        self.fields: Dict[str, FieldDefinition] = {}
        
        # Common HPXML data types inferred from usage patterns
        self.type_mapping = {
            'get_selection_field': 'string',
            'get_number_field': 'number', 
            'str(': 'string',
            'int(': 'integer',
            'float(': 'number',
            'round(': 'number',
            'True': 'boolean',
            'False': 'boolean',
            '"': 'string',
            "'": 'string'
        }
        
        # Common units found in HPXML
        self.unit_patterns = {
            r'area|ft2|m2': 'ft²',
            r'rvalue|r_val|r-value': 'ft²·°F·h/Btu', 
            r'uvalue|u_val|u-value': 'Btu/ft²·°F·h',
            r'capacity|btu|kw|watts': 'Btu/h',
            r'temperature|temp|°f|fahrenheit': '°F',
            r'volume|ft3|cubic': 'ft³',
            r'height|width|length|depth': 'ft'
        }
        
    def extract_from_component_dict(self, component_dict: Dict, component_name: str) -> List[FieldDefinition]:
        """Extract field definitions from a component dictionary structure."""
        fields = []
        
        def extract_recursive(obj, path_parts: List[str] = None):
            if path_parts is None:
                path_parts = []
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = path_parts + [key]
                    
                    # Skip metadata keys
                    if key.startswith('@') or key in ['extension', 'SystemIdentifier']:
                        if isinstance(value, (str, int, float, bool)):
                            # This is a leaf value
                            field_name = key.replace('@', '')
                            field_path = ' → '.join(current_path)
                            data_type = self._infer_type_from_value(value)
                            
                            field_def = FieldDefinition(
                                name=field_name,
                                field_path=field_path, 
                                data_type=data_type,
                                domain=categorize_field(field_path, component_name),
                                processor=component_name,
                                description=self._generate_description(field_name, component_name)
                            )
                            fields.append(field_def)
                    else:
                        # Recurse into nested structures
                        extract_recursive(value, current_path)
                        
            elif isinstance(obj, (str, int, float, bool)):
                # Leaf value
                if path_parts:
                    field_name = path_parts[-1]
                    field_path = ' → '.join(path_parts)
                    data_type = self._infer_type_from_value(obj)
                    
                    field_def = FieldDefinition(
                        name=field_name,
                        field_path=field_path,
                        data_type=data_type, 
                        domain=categorize_field(field_path, component_name),
                        processor=component_name,
                        description=self._generate_description(field_name, component_name),
                        default_value=obj if data_type != 'string' else None
                    )
                    fields.append(field_def)
        
        extract_recursive(component_dict)
        return fields
    
    def _infer_type_from_value(self, value: Any) -> str:
        """Infer JSON Schema type from Python value."""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'string'  # Default fallback
    
    def _generate_description(self, field_name: str, component_name: str) -> str:
        """Generate a descriptive label for a field based on naming patterns."""
        # Convert camelCase/snake_case to readable format
        readable_name = re.sub(r'([A-Z])', r' \1', field_name)
        readable_name = readable_name.replace('_', ' ').strip()
        
        # Component-specific context
        if 'heating' in component_name.lower():
            context = 'for heating system'
        elif 'cooling' in component_name.lower():
            context = 'for cooling system'  
        elif 'wall' in component_name.lower():
            context = 'for wall assembly'
        elif 'window' in component_name.lower():
            context = 'for window component'
        elif 'door' in component_name.lower():
            context = 'for door component'
        else:
            context = f'for {component_name.replace("_", " ")}'
            
        return f"{readable_name} {context}".strip()
    
    def _extract_units(self, field_name: str, context: str = "") -> Optional[str]:
        """Extract likely units for a field based on naming patterns."""
        combined_text = f"{field_name} {context}".lower()
        
        for pattern, unit in self.unit_patterns.items():
            if re.search(pattern, combined_text):
                return unit
                
        return None
    
    def get_common_fields(self) -> Dict[str, FieldDefinition]:
        """Get common HPXML fields that appear across multiple components."""
        common_fields = {}
        
        # Fields that appear in most HPXML components
        system_id_field = FieldDefinition(
            name="id",
            field_path="SystemIdentifier → @id", 
            data_type="string",
            domain=HPXMLDomain.HVAC,  # Default, will be overridden
            processor="common",
            is_required=True,
            description="Unique identifier for this component"
        )
        common_fields["SystemIdentifier_id"] = system_id_field
        
        area_field = FieldDefinition(
            name="Area",
            field_path="Area",
            data_type="number",
            domain=HPXMLDomain.ENVELOPE,
            processor="common", 
            is_required=True,
            min_value=0.1,
            units="ft²",
            description="Surface area of the component"
        )
        common_fields["Area"] = area_field
        
        rvalue_field = FieldDefinition(
            name="RValue", 
            field_path="RValue",
            data_type="number",
            domain=HPXMLDomain.ENVELOPE,
            processor="common",
            min_value=0.1,
            units="ft²·°F·h/Btu",
            description="Thermal resistance value"
        )
        common_fields["RValue"] = rvalue_field
        
        return common_fields