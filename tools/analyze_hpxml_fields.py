#!/usr/bin/env python3
"""
HPXML Field Analysis Tool

This script analyzes the h2k-hpxml processor files to extract all HPXML field patterns,
data types, and relationships. It generates a comprehensive field inventory for use in
the data-driven API schema generation.

Usage:
    python tools/analyze_hpxml_fields.py
    python tools/analyze_hpxml_fields.py --output docs/api/field_inventory.json
"""

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class FieldInfo:
    """Information about an HPXML field."""
    field_path: str
    data_type: str
    processor: str
    line_number: int
    context: str
    is_required: bool = False
    default_value: Optional[str] = None
    validation_rules: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []

class HPXMLFieldAnalyzer:
    """Analyzes processor files to extract HPXML field patterns."""
    
    def __init__(self, processors_dir: str = "src/h2k_hpxml/core/processors"):
        self.processors_dir = Path(processors_dir)
        self.fields: Dict[str, FieldInfo] = {}
        self.patterns = {
            # Common HPXML field assignment patterns
            'direct_assignment': re.compile(r'hpxml_dict\[(["\'][^"\']+["\']\s*,\s*)*["\']([^"\']+)["\']\]\s*=\s*(.+)'),
            'nested_assignment': re.compile(r'(\w+_dict)\[(["\'][^"\']+["\']\s*,\s*)*["\']([^"\']+)["\']\]\s*=\s*(.+)'),
            'dict_creation': re.compile(r'(\w+_dict)\s*=\s*hpxml_dict\[(["\'][^"\']+["\']\s*,\s*)*["\']([^"\']+)["\']\]'),
            'list_append': re.compile(r'(\w+)\s*\.\s*append\s*\(\s*{(.+?)}\s*\)'),
        }
        
    def analyze_all_processors(self) -> Dict[str, Any]:
        """Analyze all processor files and return field inventory."""
        if not self.processors_dir.exists():
            raise FileNotFoundError(f"Processors directory not found: {self.processors_dir}")
            
        processor_files = [
            f for f in self.processors_dir.glob("*.py") 
            if f.name != "__init__.py"
        ]
        
        print(f"Analyzing {len(processor_files)} processor files...")
        
        for processor_file in processor_files:
            print(f"  Analyzing {processor_file.name}...")
            self.analyze_processor_file(processor_file)
            
        return self.generate_inventory()
    
    def analyze_processor_file(self, file_path: Path) -> None:
        """Analyze a single processor file for HPXML field patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            processor_name = file_path.stem
            
            # Parse with AST for better understanding
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, processor_name, lines)
            except SyntaxError as e:
                print(f"    Warning: Could not parse AST for {file_path.name}: {e}")
                # Fallback to regex analysis
                self._analyze_with_regex(lines, processor_name)
                
        except Exception as e:
            print(f"    Error analyzing {file_path.name}: {e}")
    
    def _analyze_ast(self, tree: ast.AST, processor_name: str, lines: List[str]) -> None:
        """Analyze using Abstract Syntax Tree for more accurate parsing."""
        
        class HPXMLVisitor(ast.NodeVisitor):
            def __init__(self, analyzer: 'HPXMLFieldAnalyzer'):
                self.analyzer = analyzer
                
            def visit_Assign(self, node: ast.Assign) -> None:
                """Visit assignment nodes to find HPXML field assignments."""
                if len(node.targets) == 1:
                    target = node.targets[0]
                    
                    # Look for subscript assignments (dict[key] = value)
                    if isinstance(target, ast.Subscript):
                        field_path = self._extract_field_path(target)
                        if field_path and ("hpxml" in field_path.lower() or "dict" in field_path.lower()):
                            value_type = self._infer_type_from_node(node.value)
                            line_num = getattr(node, 'lineno', 0)
                            context = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                            
                            field_info = FieldInfo(
                                field_path=field_path,
                                data_type=value_type,
                                processor=processor_name,
                                line_number=line_num,
                                context=context
                            )
                            
                            self.analyzer.fields[field_path] = field_info
                
                self.generic_visit(node)
            
            def _extract_field_path(self, node: ast.Subscript) -> Optional[str]:
                """Extract HPXML field path from subscript node."""
                path_parts = []
                
                def extract_subscript_chain(n):
                    if isinstance(n, ast.Subscript):
                        extract_subscript_chain(n.value)
                        if isinstance(n.slice, ast.Constant):
                            path_parts.append(str(n.slice.value))
                        elif isinstance(n.slice, ast.Str):  # Python < 3.8
                            path_parts.append(n.slice.s)
                    elif isinstance(n, ast.Name):
                        path_parts.insert(0, n.id)
                        
                extract_subscript_chain(node)
                
                if path_parts and ("hpxml" in path_parts[0].lower() or "dict" in path_parts[0].lower()):
                    return " → ".join(path_parts)
                return None
            
            def _infer_type_from_node(self, node: ast.AST) -> str:
                """Infer data type from AST node."""
                if isinstance(node, ast.Constant):
                    return type(node.value).__name__
                elif isinstance(node, ast.Str):  # Python < 3.8
                    return "str"
                elif isinstance(node, ast.Num):  # Python < 3.8
                    return type(node.n).__name__
                elif isinstance(node, ast.List):
                    return "list"
                elif isinstance(node, ast.Dict):
                    return "dict"
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in ('str', 'int', 'float', 'bool', 'list', 'dict'):
                            return func_name
                        elif func_name in ('get_selection_field', 'get_number_field'):
                            # These are h2k utility functions that return specific types
                            return "str" if "selection" in func_name else "float"
                return "unknown"
        
        visitor = HPXMLVisitor(self)
        visitor.visit(tree)
    
    def _analyze_with_regex(self, lines: List[str], processor_name: str) -> None:
        """Fallback regex analysis when AST parsing fails."""
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Look for HPXML field patterns
            for pattern_name, pattern in self.patterns.items():
                match = pattern.search(line)
                if match:
                    field_path = self._extract_field_path_from_regex(match, pattern_name)
                    if field_path:
                        data_type = self._infer_type_from_value(match.groups()[-1] if match.groups() else "unknown")
                        
                        field_info = FieldInfo(
                            field_path=field_path,
                            data_type=data_type,
                            processor=processor_name,
                            line_number=line_num,
                            context=line
                        )
                        
                        self.fields[field_path] = field_info
    
    def _extract_field_path_from_regex(self, match, pattern_name: str) -> Optional[str]:
        """Extract field path from regex match."""
        groups = match.groups()
        
        if pattern_name == "direct_assignment" and len(groups) >= 2:
            # Extract nested keys from the match
            keys = [g.strip('"\'') for g in groups[:-1] if g and g.strip('"\'')]
            return " → ".join(["hpxml_dict"] + keys)
        elif pattern_name in ["nested_assignment", "dict_creation"] and len(groups) >= 3:
            dict_name = groups[0]
            keys = [g.strip('"\'') for g in groups[1:-1] if g and g.strip('"\'')]
            return " → ".join([dict_name] + keys)
            
        return None
    
    def _infer_type_from_value(self, value_str: str) -> str:
        """Infer data type from string representation of value."""
        value_str = value_str.strip()
        
        # Try to identify type from common patterns
        if value_str.startswith('"') and value_str.endswith('"'):
            return "str"
        elif value_str.startswith("'") and value_str.endswith("'"):
            return "str"
        elif value_str.isdigit():
            return "int"
        elif re.match(r'^\d+\.\d+$', value_str):
            return "float"
        elif value_str.lower() in ('true', 'false'):
            return "bool"
        elif value_str.startswith('[') and value_str.endswith(']'):
            return "list"
        elif value_str.startswith('{') and value_str.endswith('}'):
            return "dict"
        elif 'get_selection_field' in value_str:
            return "str"
        elif 'get_number_field' in value_str:
            return "float"
        else:
            return "unknown"
    
    def categorize_fields(self) -> Dict[str, List[str]]:
        """Categorize fields into domains based on field paths."""
        domains = {
            "Environment": [],
            "Envelope": [], 
            "Loads": [],
            "HVAC": [],
            "Miscellaneous": []
        }
        
        # Keywords to identify domains
        domain_keywords = {
            "Environment": ["weather", "climate", "site", "location", "azimuth", "shielding"],
            "Envelope": ["wall", "window", "door", "roof", "foundation", "basement", "insulation", "frame"],
            "Loads": ["occupancy", "appliance", "lighting", "plug", "resident", "bedroom", "bathroom"],
            "HVAC": ["heating", "cooling", "hvac", "ventilation", "distribution", "equipment", "system"]
        }
        
        for field_path, field_info in self.fields.items():
            categorized = False
            field_lower = field_path.lower()
            
            for domain, keywords in domain_keywords.items():
                if any(keyword in field_lower for keyword in keywords):
                    domains[domain].append(field_path)
                    categorized = True
                    break
            
            if not categorized:
                domains["Miscellaneous"].append(field_path)
        
        return domains
    
    def generate_inventory(self) -> Dict[str, Any]:
        """Generate comprehensive field inventory."""
        domains = self.categorize_fields()
        
        inventory = {
            "metadata": {
                "generated_by": "analyze_hpxml_fields.py",
                "total_fields": len(self.fields),
                "processors_analyzed": list(set(field.processor for field in self.fields.values())),
                "domains": list(domains.keys())
            },
            "fields": {
                field_path: asdict(field_info) 
                for field_path, field_info in self.fields.items()
            },
            "domains": domains,
            "processors": {}
        }
        
        # Group fields by processor
        for field_info in self.fields.values():
            proc = field_info.processor
            if proc not in inventory["processors"]:
                inventory["processors"][proc] = []
            inventory["processors"][proc].append(field_info.field_path)
        
        return inventory

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze HPXML fields in processor files")
    parser.add_argument("--processors-dir", default="src/h2k_hpxml/core/processors",
                      help="Directory containing processor files")
    parser.add_argument("--output", default="docs/api/field_inventory.json",
                      help="Output file for field inventory JSON")
    parser.add_argument("--verbose", action="store_true",
                      help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Analyze processors
    analyzer = HPXMLFieldAnalyzer(args.processors_dir)
    
    try:
        inventory = analyzer.analyze_all_processors()
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n✅ Analysis complete!")
        print(f"📊 Found {inventory['metadata']['total_fields']} HPXML fields")
        print(f"🔍 Analyzed {len(inventory['metadata']['processors_analyzed'])} processors")
        print(f"📁 Categorized into {len(inventory['domains'])} domains:")
        
        for domain, fields in inventory["domains"].items():
            print(f"   • {domain}: {len(fields)} fields")
        
        print(f"💾 Results saved to: {output_path}")
        
        if args.verbose:
            print(f"\n🔍 Field breakdown by processor:")
            for processor, fields in inventory["processors"].items():
                print(f"   • {processor}.py: {len(fields)} fields")
                
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()