"""
JSON Schema generator for HPXML fields.

This module generates JSON Schema definitions from the extracted field
definitions, suitable for use in dynamic UI generation.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from .fields import FieldDefinition, FieldExtractor
from .domains import HPXMLDomain, get_domain_display_name, get_domain_description

class JSONSchemaGenerator:
    """Generates JSON Schema from HPXML field definitions."""
    
    def __init__(self):
        self.field_extractor = FieldExtractor()
        
    def generate_domain_schema(self, domain: HPXMLDomain, fields: List[FieldDefinition]) -> Dict[str, Any]:
        """Generate JSON Schema for a specific domain."""
        
        # Filter fields for this domain
        domain_fields = [f for f in fields if f.domain == domain]
        
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://h2k-hpxml.api/schemas/{domain.value}",
            "title": get_domain_display_name(domain),
            "description": get_domain_description(domain),
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for field in domain_fields:
            field_schema = self._generate_field_schema(field)
            schema["properties"][field.name] = field_schema
            
            if field.is_required:
                schema["required"].append(field.name)
        
        return schema
    
    def _generate_field_schema(self, field: FieldDefinition) -> Dict[str, Any]:
        """Generate JSON Schema for a single field."""
        field_schema = {
            "type": field.data_type,
            "title": field.name.replace('_', ' ').title(),
            "description": field.description
        }
        
        # Add constraints based on data type
        if field.data_type == "number":
            if field.min_value is not None:
                field_schema["minimum"] = field.min_value
            if field.max_value is not None:
                field_schema["maximum"] = field.max_value
                
        elif field.data_type == "string":
            if field.enum_values:
                field_schema["enum"] = field.enum_values
            else:
                field_schema["minLength"] = 1  # Non-empty strings
                
        elif field.data_type == "integer":
            if field.min_value is not None:
                field_schema["minimum"] = int(field.min_value)
            if field.max_value is not None:
                field_schema["maximum"] = int(field.max_value)
        
        # Add default value
        if field.default_value is not None:
            field_schema["default"] = field.default_value
            
        # Add units information in extension
        if field.units:
            field_schema["units"] = field.units
            
        # Add validation rules
        if field.validation_rules:
            field_schema["validation"] = field.validation_rules
            
        # Add field dependencies  
        if field.dependencies:
            field_schema["dependencies"] = field.dependencies
            
        # Add processor source for debugging
        field_schema["x-processor"] = field.processor
        field_schema["x-field-path"] = field.field_path
        
        return field_schema
    
    def generate_full_schema(self, fields: List[FieldDefinition]) -> Dict[str, Any]:
        """Generate complete JSON Schema with all domains."""
        
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://h2k-hpxml.api/schemas/complete",
            "title": "H2K-HPXML Complete Building Model",
            "description": "Complete schema for H2K to HPXML building energy model translation",
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Generate schema for each domain
        for domain in HPXMLDomain:
            domain_schema = self.generate_domain_schema(domain, fields)
            schema["properties"][domain.value] = domain_schema
            
        return schema
    
    def generate_schema_from_inventory(self, inventory_file: Path) -> Dict[HPXMLDomain, Dict[str, Any]]:
        """Generate schemas from existing field inventory JSON."""
        
        if not inventory_file.exists():
            raise FileNotFoundError(f"Field inventory not found: {inventory_file}")
            
        with open(inventory_file, 'r') as f:
            inventory = json.load(f)
            
        # Convert inventory to field definitions
        fields = []
        for field_path, field_data in inventory.get("fields", {}).items():
            # Map inventory data to FieldDefinition
            field_def = FieldDefinition(
                name=field_path.split(' → ')[-1],  # Last part of path
                field_path=field_path,
                data_type=self._normalize_data_type(field_data.get("data_type", "string")),
                domain=self._determine_domain_from_inventory(field_path, field_data),
                processor=field_data.get("processor", "unknown"),
                description=field_data.get("description", ""),
                validation_rules=field_data.get("validation_rules", [])
            )
            fields.append(field_def)
            
        # Generate schemas by domain  
        schemas = {}
        for domain in HPXMLDomain:
            schemas[domain] = self.generate_domain_schema(domain, fields)
            
        return schemas
    
    def _normalize_data_type(self, raw_type: str) -> str:
        """Normalize data types to JSON Schema types."""
        type_mapping = {
            "str": "string",
            "int": "integer", 
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "unknown": "string"
        }
        return type_mapping.get(raw_type, "string")
    
    def _determine_domain_from_inventory(self, field_path: str, field_data: Dict) -> HPXMLDomain:
        """Determine domain from inventory field data."""
        processor = field_data.get("processor", "")
        
        # Use existing categorization logic
        from .domains import categorize_field
        return categorize_field(field_path, processor)
    
    def save_schemas(self, schemas: Dict[HPXMLDomain, Dict[str, Any]], output_dir: Path):
        """Save generated schemas to JSON files."""
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for domain, schema in schemas.items():
            schema_file = output_dir / f"{domain.value}_schema.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
                
        # Also save combined schema
        combined_fields = []
        for domain_fields in schemas.values():
            for field_name, field_schema in domain_fields.get("properties", {}).items():
                combined_fields.append(field_schema)
                
        combined_schema = self.generate_full_schema([])  # Empty for now, would need field defs
        combined_file = output_dir / "complete_schema.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(combined_schema, f, indent=2, ensure_ascii=False)