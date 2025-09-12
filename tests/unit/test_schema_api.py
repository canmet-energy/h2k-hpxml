#!/usr/bin/env python3
"""
Unit tests for the schema API functionality (Phase 1).

This test suite validates the field analysis, schema generation,
and domain categorization functionality developed in Phase 1.
"""

import json
import tempfile
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent.parent / "src" / "h2k_hpxml" / "schema_api"))

# Skip dependency checks
import os
os.environ['H2K_SKIP_AUTO_INSTALL'] = '1'

from schema.generator import JSONSchemaGenerator
from schema.domains import HPXMLDomain, categorize_field, get_domain_display_name, get_domain_description
from schema.fields import FieldDefinition, FieldExtractor


class TestHPXMLDomains:
    """Test domain categorization functionality."""
    
    def test_domain_enum_values(self):
        """Test that all expected domain values exist."""
        expected_domains = {'environment', 'envelope', 'loads', 'hvac'}
        actual_domains = {domain.value for domain in HPXMLDomain}
        assert actual_domains == expected_domains
    
    def test_categorize_field_by_keywords(self):
        """Test field categorization based on keywords."""
        # Environment fields
        assert categorize_field("weather_station", "weather") == HPXMLDomain.ENVIRONMENT
        assert categorize_field("site_location", "building") == HPXMLDomain.ENVIRONMENT
        assert categorize_field("azimuth_data", "building") == HPXMLDomain.ENVIRONMENT
        
        # Envelope fields  
        assert categorize_field("wall_assembly", "enclosure") == HPXMLDomain.ENVELOPE
        assert categorize_field("window_area", "enclosure") == HPXMLDomain.ENVELOPE
        assert categorize_field("rvalue_insulation", "component") == HPXMLDomain.ENVELOPE
        
        # HVAC fields
        assert categorize_field("heating_system", "system") == HPXMLDomain.HVAC
        assert categorize_field("hvac_distribution", "system") == HPXMLDomain.HVAC
        assert categorize_field("cooling_capacity", "system") == HPXMLDomain.HVAC
        
        # Loads fields
        assert categorize_field("occupancy_schedule", "baseload") == HPXMLDomain.LOADS
        assert categorize_field("appliance_usage", "appliance") == HPXMLDomain.LOADS
        assert categorize_field("lighting_power", "lighting") == HPXMLDomain.LOADS
    
    def test_categorize_field_processor_precedence(self):
        """Test that processor names take precedence in categorization."""
        assert categorize_field("generic_field", "weather") == HPXMLDomain.ENVIRONMENT
        assert categorize_field("generic_field", "enclosure") == HPXMLDomain.ENVELOPE
        assert categorize_field("generic_field", "system") == HPXMLDomain.HVAC
        assert categorize_field("generic_field", "baseload") == HPXMLDomain.LOADS
    
    def test_categorize_field_default(self):
        """Test default domain assignment."""
        result = categorize_field("unknown_field", "unknown_processor")
        assert result == HPXMLDomain.ENVELOPE  # Default domain
    
    def test_get_domain_display_name(self):
        """Test domain display names."""
        assert get_domain_display_name(HPXMLDomain.ENVIRONMENT) == "Environment & Site"
        assert get_domain_display_name(HPXMLDomain.ENVELOPE) == "Building Envelope"
        assert get_domain_display_name(HPXMLDomain.LOADS) == "Loads & Occupancy"
        assert get_domain_display_name(HPXMLDomain.HVAC) == "HVAC Systems"
    
    def test_get_domain_description(self):
        """Test domain descriptions are non-empty."""
        for domain in HPXMLDomain:
            description = get_domain_description(domain)
            assert isinstance(description, str)
            assert len(description) > 0


class TestFieldDefinition:
    """Test FieldDefinition dataclass functionality."""
    
    def test_field_definition_creation(self):
        """Test creating a FieldDefinition instance."""
        field = FieldDefinition(
            name="test_field",
            field_path="path → to → field",
            data_type="string",
            domain=HPXMLDomain.ENVIRONMENT,
            processor="test_processor",
            is_required=True,
            default_value="test_default",
            description="Test field description"
        )
        
        assert field.name == "test_field"
        assert field.field_path == "path → to → field"
        assert field.data_type == "string"
        assert field.domain == HPXMLDomain.ENVIRONMENT
        assert field.processor == "test_processor"
        assert field.is_required == True
        assert field.default_value == "test_default"
        assert field.description == "Test field description"
    
    def test_field_definition_defaults(self):
        """Test FieldDefinition with default values."""
        field = FieldDefinition(
            name="simple_field",
            field_path="simple_path",
            data_type="number",
            domain=HPXMLDomain.HVAC,
            processor="simple_processor"
        )
        
        assert field.is_required == False
        assert field.default_value is None
        assert field.enum_values is None
        assert field.validation_rules == []
        assert field.dependencies == []


class TestFieldExtractor:
    """Test field extraction from component dictionaries."""
    
    def test_infer_type_from_value(self):
        """Test type inference from Python values."""
        extractor = FieldExtractor()
        
        assert extractor._infer_type_from_value(True) == 'boolean'
        assert extractor._infer_type_from_value(False) == 'boolean'
        assert extractor._infer_type_from_value(42) == 'integer'
        assert extractor._infer_type_from_value(3.14) == 'number'
        assert extractor._infer_type_from_value("test") == 'string'
        assert extractor._infer_type_from_value([1, 2, 3]) == 'array'
        assert extractor._infer_type_from_value({"key": "value"}) == 'object'
        assert extractor._infer_type_from_value(None) == 'string'  # Default fallback
    
    def test_generate_description(self):
        """Test description generation."""
        extractor = FieldExtractor()
        
        # Test camelCase conversion
        desc = extractor._generate_description("testFieldName", "test_component")
        assert "test Field Name" in desc
        assert "test component" in desc
        
        # Test component-specific contexts
        desc = extractor._generate_description("area", "heating_system")
        assert "for heating system" in desc
        
        desc = extractor._generate_description("rvalue", "wall_assembly")
        assert "for wall assembly" in desc
    
    def test_extract_from_component_dict(self):
        """Test extracting fields from a component dictionary."""
        extractor = FieldExtractor()
        
        sample_dict = {
            "@id": "wall_1",  # Direct attribute 
            "Area": 100.5,
            "RValue": 15.2,
            "AssemblyType": "WoodStud",
            "extension": {
                "custom_field": "custom_value"
            }
        }
        
        fields = extractor.extract_from_component_dict(sample_dict, "wall_component")
        
        # Should extract several fields
        assert len(fields) > 0
        
        # Debug output
        print(f"Debug - sample_dict structure: {sample_dict}")
        field_names = [f.name for f in fields]
        field_paths = [f.field_path for f in fields]
        print(f"Debug - extracted field names: {field_names}")
        print(f"Debug - extracted field paths: {field_paths}")
        
        # Should extract id from SystemIdentifier/@id
        assert any("id" in name.lower() for name in field_names), f"Expected 'id' field, got: {field_names}"
        assert any("Area" in name for name in field_names), f"Expected 'Area' field, got: {field_names}"
        assert any("RValue" in name for name in field_names), f"Expected 'RValue' field, got: {field_names}"
        
        # Check data types were inferred correctly
        for field in fields:
            if field.name == "Area":
                assert field.data_type == "number"
            elif field.name == "id":
                assert field.data_type == "string"
    
    def test_get_common_fields(self):
        """Test common field definitions."""
        extractor = FieldExtractor()
        common_fields = extractor.get_common_fields()
        
        assert "SystemIdentifier_id" in common_fields
        assert "Area" in common_fields
        assert "RValue" in common_fields
        
        # Check field properties
        area_field = common_fields["Area"]
        assert area_field.data_type == "number"
        assert area_field.min_value == 0.1
        assert area_field.units == "ft²"


class TestJSONSchemaGenerator:
    """Test JSON Schema generation functionality."""
    
    def test_generator_creation(self):
        """Test creating a JSONSchemaGenerator instance."""
        generator = JSONSchemaGenerator()
        assert isinstance(generator.field_extractor, FieldExtractor)
    
    def test_generate_field_schema_string(self):
        """Test schema generation for a string field."""
        generator = JSONSchemaGenerator()
        
        field = FieldDefinition(
            name="test_string",
            field_path="path → test_string",
            data_type="string",
            domain=HPXMLDomain.ENVIRONMENT,
            processor="test",
            description="Test string field"
        )
        
        schema = generator._generate_field_schema(field)
        
        assert schema["type"] == "string"
        assert schema["title"] == "Test String"
        assert schema["description"] == "Test string field"
        assert schema["minLength"] == 1
        assert schema["x-processor"] == "test"
        assert schema["x-field-path"] == "path → test_string"
    
    def test_generate_field_schema_number(self):
        """Test schema generation for a number field."""
        generator = JSONSchemaGenerator()
        
        field = FieldDefinition(
            name="test_number",
            field_path="path → test_number",
            data_type="number",
            domain=HPXMLDomain.ENVELOPE,
            processor="test",
            min_value=0.0,
            max_value=100.0,
            units="ft²",
            default_value=50.0,
            description="Test number field"
        )
        
        schema = generator._generate_field_schema(field)
        
        assert schema["type"] == "number"
        assert schema["minimum"] == 0.0
        assert schema["maximum"] == 100.0
        assert schema["units"] == "ft²"
        assert schema["default"] == 50.0
    
    def test_generate_field_schema_enum(self):
        """Test schema generation for an enum field."""
        generator = JSONSchemaGenerator()
        
        field = FieldDefinition(
            name="test_enum",
            field_path="path → test_enum",
            data_type="string",
            domain=HPXMLDomain.HVAC,
            processor="test",
            enum_values=["option1", "option2", "option3"],
            description="Test enum field"
        )
        
        schema = generator._generate_field_schema(field)
        
        assert schema["type"] == "string"
        assert schema["enum"] == ["option1", "option2", "option3"]
        assert "minLength" not in schema  # Should not have minLength when enum is present
    
    def test_generate_domain_schema(self):
        """Test generating a complete domain schema."""
        generator = JSONSchemaGenerator()
        
        fields = [
            FieldDefinition(
                name="field1",
                field_path="path → field1",
                data_type="string",
                domain=HPXMLDomain.ENVIRONMENT,
                processor="test",
                is_required=True,
                description="Required field"
            ),
            FieldDefinition(
                name="field2",
                field_path="path → field2",
                data_type="number",
                domain=HPXMLDomain.ENVIRONMENT,
                processor="test",
                is_required=False,
                description="Optional field"
            )
        ]
        
        schema = generator.generate_domain_schema(HPXMLDomain.ENVIRONMENT, fields)
        
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == "https://h2k-hpxml.api/schemas/environment"
        assert schema["title"] == "Environment & Site"
        assert schema["type"] == "object"
        assert len(schema["properties"]) == 2
        assert "field1" in schema["properties"]
        assert "field2" in schema["properties"]
        assert schema["required"] == ["field1"]  # Only required fields
    
    def test_normalize_data_type(self):
        """Test data type normalization."""
        generator = JSONSchemaGenerator()
        
        assert generator._normalize_data_type("str") == "string"
        assert generator._normalize_data_type("int") == "integer"
        assert generator._normalize_data_type("float") == "number"
        assert generator._normalize_data_type("bool") == "boolean"
        assert generator._normalize_data_type("list") == "array"
        assert generator._normalize_data_type("dict") == "object"
        assert generator._normalize_data_type("unknown") == "string"
        assert generator._normalize_data_type("custom_type") == "string"  # Default fallback
    
    def test_save_schemas(self):
        """Test saving schemas to files."""
        generator = JSONSchemaGenerator()
        
        # Create test schemas
        test_schemas = {
            HPXMLDomain.ENVIRONMENT: {
                "title": "Test Environment Schema",
                "properties": {"test_field": {"type": "string"}}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            generator.save_schemas(test_schemas, output_dir)
            
            # Check that files were created
            env_file = output_dir / "environment_schema.json"
            assert env_file.exists()
            
            # Check file content
            with open(env_file, 'r') as f:
                saved_schema = json.load(f)
            assert saved_schema["title"] == "Test Environment Schema"
            
            # Check that combined schema was also created
            combined_file = output_dir / "complete_schema.json"
            assert combined_file.exists()


class TestSchemaGeneration:
    """Integration tests for the complete schema generation process."""
    
    def test_field_inventory_exists(self):
        """Test that the field inventory file exists."""
        inventory_path = Path("docs/api/field_inventory.json")
        assert inventory_path.exists(), "Field inventory should exist from field analysis"
        
        with open(inventory_path, 'r') as f:
            inventory = json.load(f)
        
        assert "metadata" in inventory
        assert "fields" in inventory
        assert len(inventory["fields"]) > 0
    
    def test_generated_schemas_exist(self):
        """Test that schema files were generated."""
        schema_dir = Path("docs/api/schemas")
        assert schema_dir.exists()
        
        # Check for domain schema files
        expected_files = [
            "environment_schema.json",
            "envelope_schema.json", 
            "loads_schema.json",
            "hvac_schema.json",
            "complete_schema.json"
        ]
        
        for filename in expected_files:
            schema_file = schema_dir / filename
            assert schema_file.exists(), f"Schema file {filename} should exist"
            
            # Validate JSON structure
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            if filename != "complete_schema.json":
                assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
                assert "$id" in schema
                assert "title" in schema
                assert "description" in schema
                assert "type" in schema
                assert "properties" in schema


def run_all_tests():
    """Run all test cases manually."""
    print("🧪 Running Schema API Test Suite...")
    
    # Test domains
    print("\n📝 Testing HPXMLDomains...")
    domain_tests = TestHPXMLDomains()
    domain_tests.test_domain_enum_values()
    domain_tests.test_categorize_field_by_keywords()
    domain_tests.test_categorize_field_processor_precedence()
    domain_tests.test_categorize_field_default()
    domain_tests.test_get_domain_display_name()
    domain_tests.test_get_domain_description()
    print("✅ HPXMLDomains tests passed")
    
    # Test field definitions
    print("\n📝 Testing FieldDefinition...")
    field_tests = TestFieldDefinition()
    field_tests.test_field_definition_creation()
    field_tests.test_field_definition_defaults()
    print("✅ FieldDefinition tests passed")
    
    # Test field extractor
    print("\n📝 Testing FieldExtractor...")
    extractor_tests = TestFieldExtractor()
    extractor_tests.test_infer_type_from_value()
    extractor_tests.test_generate_description()
    extractor_tests.test_extract_from_component_dict()
    extractor_tests.test_get_common_fields()
    print("✅ FieldExtractor tests passed")
    
    # Test schema generator
    print("\n📝 Testing JSONSchemaGenerator...")
    generator_tests = TestJSONSchemaGenerator()
    generator_tests.test_generator_creation()
    generator_tests.test_generate_field_schema_string()
    generator_tests.test_generate_field_schema_number()
    generator_tests.test_generate_field_schema_enum()
    generator_tests.test_generate_domain_schema()
    generator_tests.test_normalize_data_type()
    generator_tests.test_save_schemas()
    print("✅ JSONSchemaGenerator tests passed")
    
    # Test schema generation integration
    print("\n📝 Testing SchemaGeneration integration...")
    integration_tests = TestSchemaGeneration()
    integration_tests.test_field_inventory_exists()
    integration_tests.test_generated_schemas_exist()
    print("✅ SchemaGeneration integration tests passed")
    
    print("\n🎉 All tests passed successfully!")


if __name__ == "__main__":
    # Run tests if script is executed directly
    try:
        run_all_tests()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()