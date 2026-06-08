"""Utility to post-process IDF files and add custom Output:Meter objects."""

import os
from pathlib import Path
from typing import List, Dict


def add_output_meters_to_idf(idf_path: str, meters: List[Dict[str, str]]) -> bool:
    """
    Add Output:Meter objects to an IDF file.
    
    Args:
        idf_path: Path to the IDF file
        meters: List of meter configurations, e.g.:
                [
                    {'name': 'Heating:Electricity', 'frequency': 'Zone Timestep'},
                    {'name': 'WaterSystems:Electricity', 'frequency': 'Zone Timestep'},
                ]
    
    Returns:
        bool: True if successful, False otherwise
    
    Example:
        >>> meters = [
        ...     {'name': 'Heating:Electricity', 'frequency': 'Zone Timestep'},
        ...     {'name': 'WaterSystems:Electricity', 'frequency': 'Zone Timestep'},
        ... ]
        >>> add_output_meters_to_idf('path/to/in.idf', meters)
        True
    """
    if not os.path.exists(idf_path):
        print(f"Warning: IDF file not found: {idf_path}")
        return False
    
    try:
        # Read the IDF file
        with open(idf_path, 'r', encoding='utf-8') as f:
            idf_content = f.read()
        
        # Check if meters already exist to avoid duplicates
        existing_meters = set()
        for meter in meters:
            meter_name = meter.get('name', '')
            if f"Output:Meter,\n  {meter_name}," in idf_content or \
               f"Output:Meter,{meter_name}," in idf_content:
                existing_meters.add(meter_name)
        
        # Filter out existing meters
        meters_to_add = [m for m in meters if m.get('name', '') not in existing_meters]
        
        if not meters_to_add:
            print(f"All requested meters already exist in {idf_path}")
            return True
        
        # Build Output:Meter objects
        meter_objects = []
        for meter in meters_to_add:
            meter_name = meter.get('name', '')
            frequency = meter.get('frequency', 'Zone Timestep')
            
            meter_obj = f"""
Output:Meter,
  {meter_name},                    !- Key Name
  {frequency};                     !- Reporting Frequency
"""
            meter_objects.append(meter_obj)
        
        # Find insertion point - insert near the end, before Output:VariableDictionary
        # or Output:Diagnostics if they exist
        insertion_markers = [
            'Output:VariableDictionary',
            'Output:Diagnostics',
            'OutputControl:Table:Style',
        ]
        
        insertion_point = -1
        for marker in insertion_markers:
            idx = idf_content.rfind(marker)
            if idx != -1:
                insertion_point = idx
                break
        
        if insertion_point == -1:
            # If no markers found, insert at end
            insertion_point = len(idf_content)
        
        # Insert the meter objects
        meters_text = '\n'.join(meter_objects)
        modified_content = (
            idf_content[:insertion_point] + 
            meters_text + 
            '\n' + 
            idf_content[insertion_point:]
        )
        
        # Write back to file
        with open(idf_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✓ Added {len(meters_to_add)} Output:Meter object(s) to {os.path.basename(idf_path)}")
        for meter in meters_to_add:
            print(f"  - {meter['name']} ({meter.get('frequency', 'Hourly')})")
        
        return True
        
    except Exception as e:
        print(f"Error modifying IDF file: {e}")
        return False


def process_hpxml_output_folder(hpxml_path: str, meters: List[Dict[str, str]]) -> bool:
    """
    Process the IDF file in the run folder associated with an HPXML file.
    
    Args:
        hpxml_path: Path to the HPXML file
        meters: List of meter configurations
    
    Returns:
        bool: True if IDF was found and processed successfully
    """
    # Determine the run folder location
    hpxml_dir = os.path.dirname(os.path.abspath(hpxml_path))
    idf_path = os.path.join(hpxml_dir, "run", "in.idf")
    
    if os.path.exists(idf_path):
        return add_output_meters_to_idf(idf_path, meters)
    else:
        print(f"Warning: IDF file not found at {idf_path}")
        return False


def get_default_meters() -> List[Dict[str, str]]:
    """
    Get default list of custom meters to add.
    
    Returns:
        List of meter configurations
    """
    return [
        {'name': 'Heating:Electricity', 'frequency': 'Hourly'},
        {'name': 'WaterSystems:Electricity', 'frequency': 'Hourly'},
    ]
