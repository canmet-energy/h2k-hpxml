#!/usr/bin/env python3
"""
Test script for schema generation functionality.

This script tests the schema generation from the field inventory
to ensure the API module structure is working correctly.
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Skip dependency checks and CLI imports
import os
os.environ['H2K_SKIP_AUTO_INSTALL'] = '1'

# Import directly from the schema modules to avoid main package dependencies  
sys.path.append(str(Path(__file__).parent.parent / "src" / "h2k_hpxml" / "schema_api"))

from schema.generator import JSONSchemaGenerator
from schema.domains import HPXMLDomain

def test_schema_generation():
    """Test the schema generation process."""
    print("🧪 Testing schema generation...")
    
    # Initialize generator
    generator = JSONSchemaGenerator()
    
    # Test with field inventory
    inventory_file = Path("docs/api/field_inventory.json")
    
    if not inventory_file.exists():
        print(f"❌ Field inventory not found: {inventory_file}")
        return False
        
    try:
        # Generate schemas from inventory
        schemas = generator.generate_schema_from_inventory(inventory_file)
        
        print(f"✅ Generated schemas for {len(schemas)} domains:")
        
        for domain, schema in schemas.items():
            field_count = len(schema.get("properties", {}))
            required_count = len(schema.get("required", []))
            print(f"   • {domain.value}: {field_count} fields ({required_count} required)")
            
            # Show a few example fields
            properties = schema.get("properties", {})
            if properties:
                print(f"     Example fields: {list(properties.keys())[:3]}")
        
        # Save schemas to output directory
        output_dir = Path("docs/api/schemas")
        generator.save_schemas(schemas, output_dir)
        
        print(f"💾 Schemas saved to: {output_dir}")
        
        # Show sample schema structure
        if HPXMLDomain.ENVIRONMENT in schemas:
            env_schema = schemas[HPXMLDomain.ENVIRONMENT]
            print(f"\n📋 Sample Environment Schema:")
            print(f"   Title: {env_schema.get('title')}")
            print(f"   Description: {env_schema.get('description')}")
            
            sample_fields = list(env_schema.get("properties", {}).items())[:2]
            for field_name, field_schema in sample_fields:
                print(f"   Field '{field_name}': {field_schema.get('type')} - {field_schema.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_schema_generation()
    sys.exit(0 if success else 1)