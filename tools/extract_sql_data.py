#!/usr/bin/env python3
"""
Extract conditioned floor area from EnergyPlus SQL output files.

Usage:
    python extract_sql_data.py <output_directory> [--output results.csv]

CSV column headers comply with BTAP output format conventions.
"""

import argparse
import csv
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_floor_area(sql_path: str) -> float | None:
    """Extract Net Conditioned Building Area from SQL file."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Building Area'
                AND RowName = 'Net Conditioned Building Area'
                AND ColumnName='Area'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else None
    except:
        return None


def extract_net_site_eui(sql_path: str) -> float | None:
    """Extract Net Site EUI from SQL file and convert from MJ/m² to GJ/m²."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Site and Source Energy'
                AND RowName='Net Site Energy'
                AND ColumnName='Energy Per Conditioned Building Area'
                AND Units='MJ/m2'
            """)
            result = cursor.fetchone()
            # Convert from MJ/m² to GJ/m² (divide by 1000)
            return float(result[0]) / 1000 if result and result[0] else None
    except:
        return None


def extract_total_site_eui(sql_path: str) -> float | None:
    """
    Extract Total Site EUI from SQL file and convert from MJ/m² to GJ/m².
    
    Total Site Energy is the "gross" energy used by a building (before on-site generation).
    """
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Site and Source Energy'
                AND RowName='Total Site Energy'
                AND ColumnName='Energy Per Conditioned Building Area'
                AND Units='MJ/m2'
            """)
            result = cursor.fetchone()
            # Convert from MJ/m² to GJ/m² (divide by 1000)
            return float(result[0]) / 1000 if result and result[0] else None
    except:
        return None


def extract_unmet_hours_cooling_during_occupied(sql_path: str) -> float | None:
    """Extract Time Setpoint Not Met During Occupied Cooling from SQL file."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Comfort and Setpoint Not Met Summary'
                AND RowName='Time Setpoint Not Met During Occupied Cooling'
                AND ColumnName='Facility'
                AND Units='Hours'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else None
    except:
        return None


def extract_unmet_hours_heating_during_occupied(sql_path: str) -> float | None:
    """Extract Time Setpoint Not Met During Occupied Heating from SQL file."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Comfort and Setpoint Not Met Summary'
                AND RowName='Time Setpoint Not Met During Occupied Heating'
                AND ColumnName='Facility'
                AND Units='Hours'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else None
    except:
        return None


def extract_unmet_hours_cooling(sql_path: str) -> float | None:
    """Extract total Time Setpoint Not Met During Cooling (occupied + unoccupied) from SQL file."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='SystemSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Time Setpoint Not Met'
                AND RowName='Facility'
                AND ColumnName='During Cooling'
                AND Units='hr'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else None
    except:
        return None


def extract_unmet_hours_heating(sql_path: str) -> float | None:
    """Extract total Time Setpoint Not Met During Heating (occupied + unoccupied) from SQL file."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='SystemSummary'
                AND ReportForString='Entire Facility'
                AND TableName='Time Setpoint Not Met'
                AND RowName='Facility'
                AND ColumnName='During Heating'
                AND Units='hr'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else None
    except:
        return None


def extract_house_type(h2k_path: str) -> str | None:
    """Extract HouseType from H2K XML file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        house_type = root.find('.//HouseType/English')
        return house_type.text if house_type is not None else None
    except:
        return None


def extract_location_city(h2k_path: str) -> str | None:
    """Extract Location (city) from H2K XML file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        location = root.find('.//Weather/Location/English')
        return location.text if location is not None else None
    except:
        return None


def extract_region(h2k_path: str) -> str | None:
    """Extract Region (province/state) from H2K XML file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        region = root.find('.//Weather/Region/English')
        return region.text if region is not None else None
    except:
        return None


def extract_weather_file(hpxml_path: str) -> str | None:
    """Extract weather file name from HPXML file."""
    try:
        tree = ET.parse(hpxml_path)
        root = tree.getroot()
        # Handle namespace
        ns = {'hpxml': 'http://hpxmlonline.com/2023/09'}
        epw_path = root.find('.//hpxml:EPWFilePath', ns)
        if epw_path is not None and epw_path.text:
            # Extract just the filename from the full path
            return os.path.basename(epw_path.text)
        return None
    except:
        return None


def get_end_uses_table(sql_path: str) -> list[dict] | None:
    """
    Extract End Uses table from SQL file.
    Returns a list of dicts with end use name and fuel columns.
    """
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            
            # Get all rows from End Uses table
            cursor.execute("""
                SELECT RowName, ColumnName, Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='End Uses'
                AND Units='GJ'
            """)
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            # Reorganize into list of dicts by row name
            end_uses = {}
            for row_name, column_name, value in rows:
                # Skip Total and Average rows, and empty row names
                if 'Total' in row_name or 'Average' in row_name or not row_name.strip():
                    continue
                
                if row_name not in end_uses:
                    end_uses[row_name] = {'name': row_name}
                
                # Map column names to standardized keys
                column_map = {
                    'Electricity': 'electricity_gj',
                    'Natural Gas': 'natural_gas_gj',
                    'Additional Fuel': 'additional_fuel_gj',
                    'District Cooling': 'district_cooling_gj',
                    'District Heating': 'district_heating_gj',
                    'Water': 'water_m3'
                }
                
                key = column_map.get(column_name, column_name.lower().replace(' ', '_'))
                end_uses[row_name][key] = float(value) if value else 0.0
            
            return list(end_uses.values())
    except Exception as e:
        print(f"Error extracting end uses table: {e}")
        return None


def extract_end_use_eui(sql_path: str, floor_area: float) -> dict:
    """
    Extract energy EUI for each end use (summed across all fuel types).
    Returns dict with keys like 'energy_eui_heating_gj_per_m_sq'.
    End use names preserve spaces to match BTAP conventions (e.g., 'interior equipment').
    Only returns the following end uses:
    - interior equipment
    - heat recovery
    - water systems
    - interior lighting
    - heat rejection
    - fans
    - heating
    - cooling
    - pumps
    """
    # Define allowed end uses
    allowed_end_uses = {
        'energy_eui_interior equipment_gj_per_m_sq',
        'energy_eui_heat recovery_gj_per_m_sq',
        'energy_eui_water systems_gj_per_m_sq',
        'energy_eui_interior lighting_gj_per_m_sq',
        'energy_eui_heat rejection_gj_per_m_sq',
        'energy_eui_fans_gj_per_m_sq',
        'energy_eui_heating_gj_per_m_sq',
        'energy_eui_cooling_gj_per_m_sq',
        'energy_eui_pumps_gj_per_m_sq',
    }
    
    result = {}
    end_uses = get_end_uses_table(sql_path)
    
    if not end_uses or not floor_area or floor_area == 0:
        return result
    
    # For each end use, sum all energy columns (exclude water)
    for end_use in end_uses:
        # Lowercase but preserve spaces to match BTAP naming conventions
        name = end_use['name'].lower().strip()
        
        # Skip empty names
        if not name:
            continue
        
        # Generate the key name
        key = f'energy_eui_{name}_gj_per_m_sq'
        
        # Only process if it's in the allowed list
        if key not in allowed_end_uses:
            continue
        
        # Sum all energy columns (not water)
        total_energy = sum(
            v for k, v in end_use.items() 
            if k != 'name' and k != 'water_m3' and isinstance(v, (int, float))
        )
        
        # Calculate EUI
        eui = total_energy / floor_area
        result[key] = eui
    
    return result


def extract_fuel_type_eui(sql_path: str, floor_area: float) -> dict:
    """
    Extract energy EUI for each fuel type directly from the Total row in End Uses table.
    Returns dict with keys like 'energy_eui_electricity_gj_per_m_sq'.
    
    Note: This function extracts the Total row values from the End Uses table,
    which includes ALL end uses as calculated by EnergyPlus. It dynamically extracts
    all fuel types present in the ColumnName, not just predefined ones.
    """
    result = {}
    
    if not floor_area or floor_area == 0:
        return result
    
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            
            # Get the Total row from End Uses table
            cursor.execute("""
                SELECT ColumnName, Value
                FROM TabularDataWithStrings
                WHERE ReportName='AnnualBuildingUtilityPerformanceSummary'
                AND ReportForString='Entire Facility'
                AND TableName='End Uses'
                AND RowName='Total End Uses'
                AND Units='GJ'
            """)
            
            rows = cursor.fetchall()
            if not rows:
                return result
            
            # Map known column names to standardized keys (for consistency)
            column_map = {
                'Electricity': 'energy_eui_electricity_gj_per_m_sq',
                'Natural Gas': 'energy_eui_natural_gas_gj_per_m_sq',
                'Additional Fuel': 'energy_eui_additional_fuel_gj_per_m_sq',
                'District Cooling': 'energy_eui_district_cooling_gj_per_m_sq',
                'District Heating': 'energy_eui_district_heating_gj_per_m_sq',
            }
            
            # Extract and calculate EUI for each fuel type
            for column_name, value in rows:
                if value:
                    total_gj = float(value)
                    eui = total_gj / floor_area
                    
                    # Use predefined key if available, otherwise generate from column name
                    if column_name in column_map:
                        key = column_map[column_name]
                    else:
                        # Dynamically generate key for other fuel types
                        # Convert "Other Fuel" -> "energy_eui_other_fuel_gj_per_m_sq"
                        sanitized_name = column_name.lower().replace(' ', '_')
                        key = f'energy_eui_{sanitized_name}_gj_per_m_sq'
                    
                    result[key] = eui
            
            # Calculate total energy EUI (sum of all fuels)
            result['energy_eui_total_gj_per_m_sq'] = sum(result.values())
            
    except Exception as e:
        print(f"Error extracting fuel type EUI: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Extract floor area from EnergyPlus SQL files")
    parser.add_argument('input_dir', help='Directory containing eplusout.sql files')
    parser.add_argument('--output', '-o', help='Output CSV file (default: sql_data.csv in input_dir)')
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    output_csv = args.output or os.path.join(args.input_dir, "sql_data.csv")
    parent_dir = os.path.dirname(os.path.abspath(args.input_dir))
    
    # Find SQL files
    sql_files = []
    for item in os.listdir(args.input_dir):
        item_path = os.path.join(args.input_dir, item)
        if os.path.isdir(item_path):
            run_sql = os.path.join(item_path, "run", "eplusout.sql")
            if os.path.exists(run_sql):
                sql_files.append((item, run_sql))
    
    if not sql_files:
        print(f"No eplusout.sql files found in {args.input_dir}")
        sys.exit(1)
    
    # Extract data
    results = []
    for house_name, sql_path in sorted(sql_files):
        floor_area = extract_floor_area(sql_path)
        net_site_eui = extract_net_site_eui(sql_path)
        total_site_eui = extract_total_site_eui(sql_path)
        unmet_hours_cooling_occupied = extract_unmet_hours_cooling_during_occupied(sql_path)
        unmet_hours_heating_occupied = extract_unmet_hours_heating_during_occupied(sql_path)
        unmet_hours_cooling_total = extract_unmet_hours_cooling(sql_path)
        unmet_hours_heating_total = extract_unmet_hours_heating(sql_path)
        
        # Extract end use and fuel type EUI data
        end_use_eui = {}
        fuel_type_eui = {}
        if floor_area:
            # Define allowed end use columns to keep in output
            allowed_end_use_columns = {
                'energy_eui_fans_gj_per_m_sq',
                'energy_eui_heating_gj_per_m_sq',
                'energy_eui_cooling_gj_per_m_sq',
                'energy_eui_interior equipment_gj_per_m_sq',
                'energy_eui_pumps_gj_per_m_sq',
                'energy_eui_heat recovery_gj_per_m_sq',
                'energy_eui_water systems_gj_per_m_sq',
                'energy_eui_interior lighting_gj_per_m_sq',
                'energy_eui_heat rejection_gj_per_m_sq',
            }
            
            # Extract and filter to only allowed columns
            all_end_use_eui = extract_end_use_eui(sql_path, floor_area)
            end_use_eui = {k: v for k, v in all_end_use_eui.items() if k in allowed_end_use_columns}
            
            # Extract all fuel type EUI (no filtering - include all dynamically extracted fuel types)
            fuel_type_eui = extract_fuel_type_eui(sql_path, floor_area)
        
        # Look for H2K file in parent directory
        h2k_path = os.path.join(parent_dir, f"{house_name}.H2K")
        if not os.path.exists(h2k_path):
            h2k_path = os.path.join(parent_dir, f"{house_name}.h2k")
        
        if os.path.exists(h2k_path):
            house_type = extract_house_type(h2k_path)
            location_city = extract_location_city(h2k_path)
            region = extract_region(h2k_path)
        else:
            house_type = None
            location_city = None
            region = None
        
        # Look for HPXML file in the house output directory
        house_dir = os.path.dirname(sql_path).replace('/run', '')
        hpxml_path = os.path.join(house_dir, f"{house_name}.xml")
        weather_file = extract_weather_file(hpxml_path) if os.path.exists(hpxml_path) else None
        
        if floor_area:
            result = {
                'house_name': house_name,
                ':building_type': house_type or '',
                'location_city': location_city or '',
                'location_state_province_region': region or '',
                'location_weather_file': weather_file or '',
                'bldg_conditioned_floor_area_m_sq': floor_area,
                'net_site_eui_gj_per_m_sq': net_site_eui if net_site_eui is not None else '',
                'total_site_eui_gj_per_m_sq': total_site_eui if total_site_eui is not None else '',
                'unmet_hours_cooling': unmet_hours_cooling_total if unmet_hours_cooling_total is not None else '',
                'unmet_hours_cooling_during_occupied': unmet_hours_cooling_occupied if unmet_hours_cooling_occupied is not None else '',
                'unmet_hours_heating': unmet_hours_heating_total if unmet_hours_heating_total is not None else '',
                'unmet_hours_heating_during_occupied': unmet_hours_heating_occupied if unmet_hours_heating_occupied is not None else ''
            }
            
            # Add end use EUI data
            result.update(end_use_eui)
            
            # Add fuel type EUI data
            result.update(fuel_type_eui)
            
            results.append(result)
            type_str = f" ({house_type})" if house_type else ""
            net_eui_str = f", Net EUI: {net_site_eui:.3f}" if net_site_eui is not None else ""
            total_eui_str = f", Total EUI: {total_site_eui:.3f}" if total_site_eui is not None else ""
            unmet_cooling_str = f", Unmet Cooling: {unmet_hours_cooling_total:.1f} hrs ({unmet_hours_cooling_occupied:.1f} occupied)" if unmet_hours_cooling_total is not None and unmet_hours_cooling_occupied is not None else ""
            unmet_heating_str = f", Unmet Heating: {unmet_hours_heating_total:.1f} hrs ({unmet_hours_heating_occupied:.1f} occupied)" if unmet_hours_heating_total is not None and unmet_hours_heating_occupied is not None else ""
            print(f"{house_name}: {floor_area:.2f} m²{type_str}{net_eui_str}{total_eui_str} GJ/m²{unmet_cooling_str}{unmet_heating_str}")
    
    # Write CSV
    if results:
        with open(output_csv, 'w', newline='') as f:
            # Automatically sort columns alphabetically, keeping house_name first
            all_fields = list(results[0].keys())
            all_fields.remove('house_name')
            fieldnames = ['house_name'] + sorted(all_fields)
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✓ Saved to {output_csv} ({len(results)} buildings)")
    else:
        print("No data extracted")
        sys.exit(1)


if __name__ == "__main__":
    main()
