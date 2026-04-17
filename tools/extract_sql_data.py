#!/usr/bin/env python3
"""
Extract annual and hourly data from EnergyPlus SQL output files.

This script extracts building performance metrics from OpenStudio-HPXML simulation results.
CSV column headers comply with BTAP output format conventions.

Usage Examples:

    # Extract annual data (one sql_annual.csv per building in each house folder)
    python extract_sql_data.py output/
    # Output: output/temporary_output_folder/BUILDING_NAME/sql_annual.csv (one per building)

    # Extract hourly data (all hourly variables, BTAP format)
    # Produces one parquet file per building with timestamps as columns
    python extract_sql_data.py output/ --hourly
    # Output: output/temporary_output_folder/BUILDING_NAME/sql_hourly.parquet (one per building)

    # Extract timestep data (sub-hourly, BTAP format)
    # Produces one parquet file per building with timesteps as rows
    python extract_sql_data.py output/ --timestep
    # Output: output/temporary_output_folder/BUILDING_NAME/sql_timestep.parquet (one per building)

    # Copy h2k-hpxml output files (.H2K, .xml, results CSVs) to house folders
    # Source .H2K files are automatically found in parent directory
    python extract_sql_data.py output/

    # Delete results_timeseries.parquet files from house folders
    python extract_sql_data.py output/ --delete-timeseries

    # Delete timeseries and extract hourly data
    python extract_sql_data.py output/ --delete-timeseries --hourly

    # Extract annual data (source files are copied automatically)
    python extract_sql_data.py output/

Annual CSV columns:
    - Building metadata (name, type, location, weather file)
    - Floor area, EUI (energy use intensity)
    - Unmet hours (heating/cooling)
    - End-use EUI breakdown (heating, cooling, fans, pumps, etc.)
    - Fuel type EUI breakdown (electricity, natural gas, etc.)
    - Peak loads (W/m²): annual peaks for facility, heating, cooling, water systems

Hourly CSV format (BTAP-compatible):
    - Rows: All hourly variables (Output:Meter and Output:Variable)
    - Columns: 8760 hourly timestamps (2006-01-01 01:00 to 2006-12-31 24:00)
    - Metadata columns: datapoint_id, Name, KeyValue, Units

Timestep CSV format (BTAP-compatible):
    - Rows: All timestep data points (one row per timestep per variable)
    - Columns: Index, Timestep, datapoint_id, Name, KeyValue, Units, Value
    - Timesteps per hour: Auto-detected from simulation data
"""

import argparse
import csv
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd


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
    """Extract HouseType from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        house_type = root.find('.//HouseType/English')
        return house_type.text if house_type is not None else None
    except:
        return None


def extract_location_city(h2k_path: str) -> str | None:
    """Extract Location (city) from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        location = root.find('.//Weather/Location/English')
        return location.text if location is not None else None
    except:
        return None


def extract_region(h2k_path: str) -> str | None:
    """Extract Region (province/state) from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        region = root.find('.//Weather/Region/English')
        return region.text if region is not None else None
    except:
        return None


def extract_primary_space_heating_fuel(h2k_path: str) -> str | None:
    """Extract primary space heating fuel type from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        
        # Primary heating system is in Type1
        # Could be Boiler, Furnace, Baseboards, P9, or ComboHeatDhw
        type1 = root.find('.//HeatingCooling/Type1')
        if type1 is None:
            return None
        
        # Check for Baseboards (always electric - no Equipment/EnergySource element)
        if type1.find('.//Baseboards') is not None:
            return "Electricity"
        
        # Search for EnergySource within any Type1 system type
        # Path: Type1/{SystemType}/Equipment/EnergySource/English
        energy_source = type1.find('.//Equipment/EnergySource/English')
        
        return energy_source.text if energy_source is not None else None
    except:
        return None


def extract_primary_dhw_fuel(h2k_path: str) -> str | None:
    """Extract primary domestic hot water fuel type from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        
        # Primary DHW system is in Components/HotWater/Primary
        dhw_fuel = root.find('.//Components/HotWater/Primary/EnergySource/English')
        
        return dhw_fuel.text if dhw_fuel is not None else None
    except:
        return None


def extract_year_built(h2k_path: str) -> int | None:
    """Extract YearBuilt from H2K file."""
    try:
        tree = ET.parse(h2k_path)
        root = tree.getroot()
        
        # YearBuilt is in House/Specifications/YearBuilt with a 'value' attribute
        year_built = root.find('.//House/Specifications/YearBuilt')
        if year_built is not None and year_built.get('value'):
            return int(year_built.get('value'))
        
        return None
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


def extract_energy_peak_data(sql_path: str, floor_area: float) -> dict:
    """
    Extract peak load data similar to BTAP's energy_peak_data method.
    
    Extracts peak power demands (W/m²) for various end uses from EnergyPlus SQL output.
    
    Returns dict with keys:
        - energy_principal_heating_source: Primary heating fuel type (from LEED summary)
        - energy_peak_electric_w_per_m_sq: Peak facility electricity demand (W/m²)
        - energy_peak_natural_gas_w_per_m_sq: Peak facility natural gas demand (W/m²)
        - heating_peak_w_per_m_sq: Peak heating load across all fuel types (W/m²)
        - cooling_peak_w_per_m_sq: Peak cooling load across all fuel types (W/m²)
        - energy_peak_water_systems_w_per_m_sq: Peak DHW load across all fuel types (W/m²)
        - energy_peak_electric_w_per_m_sq_winter: Peak facility electricity demand in winter months (Dec, Jan, Feb) (W/m²)
        - energy_peak_electric_heating_w_per_m_sq_winter: Peak electricity heating demand in winter months (W/m²)
        - energy_peak_electric_water_systems_w_per_m_sq_winter: Peak water systems electricity demand in winter months (W/m²)
    """
    from datetime import datetime, timedelta
    
    result = {}
    
    if not floor_area or floor_area == 0:
        return result
    
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            
            # Extract principal heating source
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='LEEDsummary'
                AND ReportForString='Entire Facility'
                AND TableName='Sec1.1A-General Information'
                AND RowName = 'Principal Heating Source'
                AND ColumnName='Data'
            """)
            heating_source = cursor.fetchone()
            result['energy_principal_heating_source'] = heating_source[0] if heating_source and heating_source[0] else 'unknown'
            
            # Extract electric peak (W)
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='EnergyMeters'
                AND ReportForString='Entire Facility'
                AND TableName='Annual and Peak Values - Electricity'
                AND RowName='Electricity:Facility'
                AND ColumnName LIKE '%Maximum Value'
                AND Units='W'
            """)
            electric_peak = cursor.fetchone()
            result['energy_peak_electric_w_per_m_sq'] = (float(electric_peak[0]) / floor_area) if (electric_peak and electric_peak[0]) else 0.0
            
            # Extract natural gas peak (W)
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='EnergyMeters'
                AND ReportForString='Entire Facility'
                AND TableName='Annual and Peak Values - Natural Gas'
                AND RowName='NaturalGas:Facility'
                AND ColumnName LIKE '%Maximum Value'
                AND Units='W'
            """)
            natural_gas_peak = cursor.fetchone()
            result['energy_peak_natural_gas_w_per_m_sq'] = (float(natural_gas_peak[0]) / floor_area) if (natural_gas_peak and natural_gas_peak[0]) else 0.0
            
            # Extract heating peaks across all fuel types
            # Query all EnergyMeters tables for any Heating:* meters
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='EnergyMeters'
                AND ReportForString='Entire Facility'
                AND TableName LIKE 'Annual and Peak Values - %'
                AND RowName LIKE 'Heating:%'
                AND ColumnName LIKE '%Maximum Value'
                AND Units='W'
            """)
            heating_peak_values = cursor.fetchall()
            
            # Find the maximum heating peak across all fuel types
            heating_peak_w = 0.0
            if heating_peak_values:
                heating_peak_w = max(
                    float(row[0]) for row in heating_peak_values if row[0]
                )
            
            result['heating_peak_w_per_m_sq'] = heating_peak_w / floor_area if heating_peak_w > 0 else 0.0
            
            # Extract cooling peaks across all fuel types
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='EnergyMeters'
                AND ReportForString='Entire Facility'
                AND TableName LIKE 'Annual and Peak Values - %'
                AND RowName LIKE 'Cooling:%'
                AND ColumnName LIKE '%Maximum Value'
                AND Units='W'
            """)
            cooling_peak_values = cursor.fetchall()
            
            # Find the maximum cooling peak across all fuel types
            cooling_peak_w = 0.0
            if cooling_peak_values:
                cooling_peak_w = max(
                    float(row[0]) for row in cooling_peak_values if row[0]
                )
            
            result['cooling_peak_w_per_m_sq'] = cooling_peak_w / floor_area if cooling_peak_w > 0 else 0.0
            
            # Extract water systems peaks across all fuel types
            cursor.execute("""
                SELECT Value
                FROM TabularDataWithStrings
                WHERE ReportName='EnergyMeters'
                AND ReportForString='Entire Facility'
                AND TableName LIKE 'Annual and Peak Values - %'
                AND RowName LIKE 'WaterSystems:%'
                AND ColumnName LIKE '%Maximum Value'
                AND Units='W'
            """)
            water_peak_values = cursor.fetchall()
            
            # Find the maximum water systems peak across all fuel types
            water_peak_w = 0.0
            if water_peak_values:
                water_peak_w = max(
                    float(row[0]) for row in water_peak_values if row[0]
                )
            
            result['energy_peak_water_systems_w_per_m_sq'] = water_peak_w / floor_area if water_peak_w > 0 else 0.0
            
            # Extract winter peak electricity data (Dec, Jan, Feb) from timestep simulation
            # Auto-detect number of timesteps per hour from actual data
            cursor.execute("""
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE Name='Electricity:Facility' 
                AND ReportingFrequency='Zone Timestep' 
                AND Units='J'
            """)
            electricity_index_result = cursor.fetchone()
            
            if not electricity_index_result:
                # Fallback: try Hourly if available (though typically not)
                cursor.execute("""
                    SELECT ReportDataDictionaryIndex
                    FROM ReportDataDictionary
                    WHERE Name='Electricity:Facility' 
                    AND ReportingFrequency='Hourly' 
                    AND Units='J'
                """)
                electricity_index_result = cursor.fetchone()
            
            if electricity_index_result:
                index_electricity = electricity_index_result[0]
                
                # Get timestep values - try ReportData first (for meters), then ReportVariableData
                cursor.execute("""
                    SELECT Value
                    FROM ReportData
                    WHERE ReportDataDictionaryIndex = ?
                """, (index_electricity,))
                timestep_values = cursor.fetchall()
                
                if not timestep_values:
                    # Try ReportVariableData (for variables)
                    cursor.execute("""
                        SELECT VariableValue
                        FROM ReportVariableData
                        WHERE ReportVariableDataDictionaryIndex = ?
                    """, (index_electricity,))
                    timestep_values = cursor.fetchall()
                
                if timestep_values:
                    # Auto-detect number of timesteps per hour
                    total_timesteps = len(timestep_values)
                    expected_hours = 365 * 24  # 8760 hours per year
                    number_of_timesteps_per_hour = max(1, total_timesteps / expected_hours)
                    timestep_seconds = 3600 / number_of_timesteps_per_hour
                    
                    # Generate month mapping for all timesteps
                    start_time = datetime(2006, 1, 1, 0, 0)
                    timestep_minutes = 60 / number_of_timesteps_per_hour
                    months_of_year = []
                    
                    for i in range(total_timesteps):
                        timestamp = start_time + timedelta(minutes=i * timestep_minutes)
                        months_of_year.append(timestamp.month)
                    
                    # Group by month
                    monthly_data = {}
                    for month, value_tuple in zip(months_of_year, timestep_values):
                        value = value_tuple[0]
                        if month not in monthly_data:
                            monthly_data[month] = []
                        monthly_data[month].append(value)
                    
                    # Find monthly peaks (J)
                    monthly_peaks_J = {month: max(values) for month, values in monthly_data.items()}
                    
                    # Convert to W (divide by seconds per timestep)
                    monthly_peaks_W = {month: peak_J / timestep_seconds for month, peak_J in monthly_peaks_J.items()}
                    
                    # Get winter peak (Dec=12, Jan=1, Feb=2)
                    winter_peak_W = max(
                        monthly_peaks_W.get(12, 0.0),
                        monthly_peaks_W.get(1, 0.0),
                        monthly_peaks_W.get(2, 0.0)
                    )
                    
                    # Normalize by floor area
                    result['energy_peak_electric_w_per_m_sq_winter'] = winter_peak_W / floor_area
                else:
                    result['energy_peak_electric_w_per_m_sq_winter'] = 0.0
            else:
                result['energy_peak_electric_w_per_m_sq_winter'] = 0.0
            
            # Extract winter peak electricity heating (Heating:Electricity)
            # Try Zone Timestep first, then Hourly
            cursor.execute("""
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE Name='Heating:Electricity' 
                AND ReportingFrequency='Zone Timestep' 
                AND Units='J'
            """)
            index_result = cursor.fetchone()
            
            if not index_result:
                # Fallback to Hourly if available
                cursor.execute("""
                    SELECT ReportDataDictionaryIndex
                    FROM ReportDataDictionary
                    WHERE Name='Heating:Electricity' 
                    AND ReportingFrequency='Hourly' 
                    AND Units='J'
                """)
                index_result = cursor.fetchone()
            
            if index_result:
                index_heating = index_result[0]
                
                # Get hourly values
                cursor.execute("""
                    SELECT Value
                    FROM ReportData
                    WHERE ReportDataDictionaryIndex = ?
                """, (index_heating,))
                hourly_values = cursor.fetchall()
                
                if not hourly_values:
                    cursor.execute("""
                        SELECT VariableValue
                        FROM ReportVariableData
                        WHERE ReportVariableDataDictionaryIndex = ?
                    """, (index_heating,))
                    hourly_values = cursor.fetchall()
                
                if hourly_values:
                    # Group by month
                    monthly_data = {}
                    for month, value_tuple in zip(months_of_year, hourly_values):
                        value = value_tuple[0]
                        if month not in monthly_data:
                            monthly_data[month] = []
                        monthly_data[month].append(value)
                    
                    # Find monthly peaks (J)
                    monthly_peaks_J = {month: max(values) for month, values in monthly_data.items()}
                    
                    # Convert to W
                    monthly_peaks_W = {month: peak_J / timestep_seconds for month, peak_J in monthly_peaks_J.items()}
                    
                    # Get winter peak (Dec, Jan, Feb)
                    winter_peak_W = max(
                        monthly_peaks_W.get(12, 0.0),
                        monthly_peaks_W.get(1, 0.0),
                        monthly_peaks_W.get(2, 0.0)
                    )
                    
                    # Normalize by floor area
                    result['energy_peak_electric_heating_w_per_m_sq_winter'] = winter_peak_W / floor_area
                else:
                    result['energy_peak_electric_heating_w_per_m_sq_winter'] = 0.0
            else:
                result['energy_peak_electric_heating_w_per_m_sq_winter'] = 0.0
            
            # Extract winter peak water systems electricity (WaterSystems:Electricity)
            # Try Zone Timestep first, then Hourly
            cursor.execute("""
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE Name='WaterSystems:Electricity' 
                AND ReportingFrequency='Zone Timestep' 
                AND Units='J'
            """)
            index_result = cursor.fetchone()
            
            if not index_result:
                # Fallback to Hourly if available
                cursor.execute("""
                    SELECT ReportDataDictionaryIndex
                    FROM ReportDataDictionary
                    WHERE Name='WaterSystems:Electricity' 
                    AND ReportingFrequency='Hourly' 
                    AND Units='J'
                """)
                index_result = cursor.fetchone()
            
            if index_result:
                index_water_systems = index_result[0]
                
                # Get hourly values
                cursor.execute("""
                    SELECT Value
                    FROM ReportData
                    WHERE ReportDataDictionaryIndex = ?
                """, (index_water_systems,))
                hourly_values = cursor.fetchall()
                
                if not hourly_values:
                    cursor.execute("""
                        SELECT VariableValue
                        FROM ReportVariableData
                        WHERE ReportVariableDataDictionaryIndex = ?
                    """, (index_water_systems,))
                    hourly_values = cursor.fetchall()
                
                if hourly_values:
                    # Group by month
                    monthly_data = {}
                    for month, value_tuple in zip(months_of_year, hourly_values):
                        value = value_tuple[0]
                        if month not in monthly_data:
                            monthly_data[month] = []
                        monthly_data[month].append(value)
                    
                    # Find monthly peaks (J)
                    monthly_peaks_J = {month: max(values) for month, values in monthly_data.items()}
                    
                    # Convert to W
                    monthly_peaks_W = {month: peak_J / timestep_seconds for month, peak_J in monthly_peaks_J.items()}
                    
                    # Get winter peak (Dec, Jan, Feb)
                    winter_peak_W = max(
                        monthly_peaks_W.get(12, 0.0),
                        monthly_peaks_W.get(1, 0.0),
                        monthly_peaks_W.get(2, 0.0)
                    )
                    
                    # Normalize by floor area
                    result['energy_peak_electric_water_systems_w_per_m_sq_winter'] = winter_peak_W / floor_area
                else:
                    result['energy_peak_electric_water_systems_w_per_m_sq_winter'] = 0.0
            else:
                result['energy_peak_electric_water_systems_w_per_m_sq_winter'] = 0.0            
                
    except Exception as e:
        print(f"  Error extracting peak data: {e}")
    
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


def extract_hourly_data(sql_path: str, output_csv: str, house_name: str = None) -> bool:
    """
    Extract hourly simulation data in BTAP format (timestamps as columns, variables as rows).
    
    Extracts all variables with ReportingFrequency = 'Hourly' from the SQL database,
    including both Output:Meter (IsMeter=1) and Output:Variable (IsMeter=0) objects.
    
    Args:
        sql_path: Path to eplusout.sql file
        output_csv: Path for output CSV file
        house_name: Optional identifier for the datapoint
        
    Returns:
        True if successful, False otherwise
    """
    from datetime import datetime, timedelta
    
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            
            # Generate timestamps for 8760 hours (full year)
            start_time = datetime(2006, 1, 1, 1, 0)  # Match BTAP's year convention
            hours_of_year = []
            for hour in range(8760):
                timestamp = start_time + timedelta(hours=hour)
                hours_of_year.append(timestamp.strftime('%Y-%m-%d %H:%M'))
            
            # Find all hourly outputs available (both Output:Meter and Output:Variable)
            cursor.execute("""
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE ReportingFrequency = 'Hourly'
                ORDER BY IsMeter DESC, Name
            """)
            
            rdd_indices = cursor.fetchall()
            if not rdd_indices:
                print(f"  No hourly data found in {os.path.basename(sql_path)}")
                return False
            
            array_of_data = []
            
            # Process each hourly output variable
            for (rdd_index,) in rdd_indices:
                # Get Name
                cursor.execute("""
                    SELECT Name
                    FROM ReportDataDictionary
                    WHERE ReportDataDictionaryIndex = ?
                """, (rdd_index,))
                name = cursor.fetchone()[0]
                
                # Get KeyValue (may be NULL)
                cursor.execute("""
                    SELECT KeyValue
                    FROM ReportDataDictionary
                    WHERE ReportDataDictionaryIndex = ?
                """, (rdd_index,))
                key_value_result = cursor.fetchone()
                key_value = key_value_result[0] if key_value_result[0] else ""
                
                # Get Units
                cursor.execute("""
                    SELECT Units
                    FROM ReportDataDictionary
                    WHERE ReportDataDictionaryIndex = ?
                """, (rdd_index,))
                units = cursor.fetchone()[0]
                
                # Get hourly values
                cursor.execute("""
                    SELECT Value
                    FROM ReportData
                    WHERE ReportDataDictionaryIndex = ?
                """, (rdd_index,))
                hourly_values = [row[0] for row in cursor.fetchall()]
                
                # Create data row with metadata + hourly values (BTAP format)
                data_row = {
                    'datapoint_id': house_name or '',
                    'Name': name,
                    'KeyValue': key_value,
                    'Units': units
                }
                
                # Add hourly values with timestamp keys (timestamps become column headers)
                for timestamp, value in zip(hours_of_year, hourly_values):
                    data_row[timestamp] = value
                
                array_of_data.append(data_row)
            
            # Write to CSV temporarily (variables as rows, timestamps as columns)
            if array_of_data:
                with open(output_csv, 'w', newline='') as f:
                    fieldnames = ['datapoint_id', 'Name', 'KeyValue', 'Units'] + hours_of_year
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(array_of_data)
                
                # Convert to parquet (keeping CSV for checking)
                output_parquet = output_csv.replace('.csv', '.parquet')
                df = pd.read_csv(output_csv, low_memory=False)
                df.to_parquet(output_parquet, index=False)
                # Uncomment the line below to delete CSV after parquet conversion
                os.remove(output_csv)
                
                print(f"  ✓ Extracted {len(array_of_data)} hourly variables to {os.path.basename(output_parquet)} (CSV also saved)")
                return True
            
            return False
            
    except Exception as e:
        print(f"  Error extracting hourly data: {e}")
        return False


def extract_timestep_data(sql_path: str, output_csv: str, house_name: str = None, timesteps_per_hour: int = None) -> bool:
    """
    Extract timestep simulation data in BTAP format (long format with one Value column for all variables).
    
    Extracts all variables with ReportingFrequency = 'Zone Timestep' from the SQL database
    and outputs in long format matching BTAP's timestep output (one row per timestep per variable).
    
    Args:
        sql_path: Path to eplusout.sql file
        output_csv: Path for output CSV file
        house_name: Optional identifier for the datapoint
        timesteps_per_hour: Number of timesteps per hour (default: auto-detect from data)
        
    Returns:
        True if successful, False otherwise
    """
    from datetime import datetime, timedelta
    
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()
            
            # Find all timestep outputs available
            cursor.execute("""
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE ReportingFrequency = 'Zone Timestep'
                ORDER BY IsMeter DESC, Name
            """)
            
            rdd_indices = cursor.fetchall()
            if not rdd_indices:
                print(f"  No timestep data found in {os.path.basename(sql_path)}")
                return False
            
            # Auto-detect timesteps per hour if not provided
            if timesteps_per_hour is None:
                # Get count of timestep values for first variable to determine timesteps per hour
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM ReportVariableData
                    WHERE ReportVariableDataDictionaryIndex = ?
                """, (rdd_indices[0][0],))
                total_timesteps = cursor.fetchone()[0]
                
                # Calculate timesteps per hour (assuming 365 days * 24 hours)
                timesteps_per_hour = total_timesteps // (365 * 24)
                if timesteps_per_hour == 0:
                    timesteps_per_hour = 1  # Fallback to hourly
            
            # Calculate total timesteps for the year
            number_of_timesteps_of_year = 365 * 24 * timesteps_per_hour
            
            # Generate timestamps for all timesteps
            start_time = datetime(2006, 1, 1, 0, 0)  # Match BTAP's year convention
            timesteps_of_year = []
            minutes_per_timestep = 60 // timesteps_per_hour
            
            for timestep_num in range(number_of_timesteps_of_year):
                timestamp = start_time + timedelta(minutes=timestep_num * minutes_per_timestep)
                timesteps_of_year.append(timestamp.strftime('%Y-%m-%d %H:%M'))
            
            # Collect all variables data
            variables_data = {}
            
            for (rdd_index,) in rdd_indices:
                # Get metadata
                cursor.execute("""
                    SELECT Name, KeyValue, Units
                    FROM ReportDataDictionary
                    WHERE ReportDataDictionaryIndex = ?
                """, (rdd_index,))
                name, key_value, units = cursor.fetchone()
                key_value = key_value or ""
                
                # Get timestep values from ReportVariableData table
                cursor.execute("""
                    SELECT VariableValue
                    FROM ReportVariableData
                    WHERE ReportVariableDataDictionaryIndex = ?
                """, (rdd_index,))
                timestep_values = [row[0] for row in cursor.fetchall()]
                
                # Create unique column identifier
                col_name = f"{name}|{key_value}|{units}"
                variables_data[col_name] = timestep_values
            
            # Write transposed CSV temporarily (timesteps as rows, variables as columns)
            # This matches BTAP's format
            with open(output_csv, 'w', newline='') as f:
                header = ['Index', 'Timestep', 'datapoint_id', 'Name', 'KeyValue', 'Units', 'Value']
                writer = csv.writer(f)
                writer.writerow(header)
                
                for col_name, values in variables_data.items():
                    # Parse column name back to components
                    parts = col_name.split('|')
                    var_name = parts[0]
                    var_key = parts[1] if len(parts) > 1 else ""
                    var_units = parts[2] if len(parts) > 2 else ""
                    
                    # Write one row per timestep for this variable
                    for idx, (timestamp, value) in enumerate(zip(timesteps_of_year[:len(values)], values)):
                        writer.writerow([
                            idx,
                            timestamp,
                            house_name or '',
                            var_name,
                            var_key,
                            var_units,
                            value
                        ])
            
            # Convert to parquet (keeping CSV for checking)
            output_parquet = output_csv.replace('.csv', '.parquet')
            df = pd.read_csv(output_csv, low_memory=False)
            df.to_parquet(output_parquet, index=False)
            # Uncomment the line below to delete CSV after parquet conversion
            os.remove(output_csv)
            
            print(f"  ✓ Extracted {len(variables_data)} timestep variables ({len(timestep_values)} timesteps each, {timesteps_per_hour}/hr) to {os.path.basename(output_parquet)} (CSV also saved)")
            return True
            
    except Exception as e:
        print(f"  Error extracting timestep data: {e}")
        return False


def copy_h2k_output_files(input_dir: str, source_h2k_dir: str = None) -> int:
    """
    Copy h2k-hpxml generated files to each house folder in temporary_output_folder.
    
    Copies the following files for each house:
        - Original .H2K file (from source_h2k_dir)
        - Generated .xml file (HPXML)
        - results_timeseries.csv → converted to hpxml_results_timeseries.parquet
        - results_annual.csv → converted to hpxml_results_annual.parquet
    
    Note: CSV files are converted to Parquet format and the CSV versions are deleted.
    
    Args:
        input_dir: Directory containing output folders from h2k-hpxml
        source_h2k_dir: Directory containing source .H2K files (default: parent dir of input_dir)
        
    Returns:
        Number of houses processed
    """
    import shutil
    
    temp_output_dir = os.path.join(input_dir, "temporary_output_folder")
    
    if not os.path.exists(temp_output_dir):
        os.makedirs(temp_output_dir, exist_ok=True)
        print(f"Created: {temp_output_dir}")
    
    # Default source directory is parent of input_dir (where .H2K files typically are)
    if source_h2k_dir is None:
        source_h2k_dir = os.path.dirname(os.path.abspath(input_dir))
    
    # Find all house folders in input_dir
    house_folders = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path) and item != "temporary_output_folder":
            house_folders.append((item, item_path))
    
    if not house_folders:
        print(f"No house folders found in {input_dir}")
        return 0
    
    copied_count = 0
    
    for house_name, house_path in sorted(house_folders):
        # Create destination folder in temporary_output_folder
        dest_folder = os.path.join(temp_output_dir, house_name)
        os.makedirs(dest_folder, exist_ok=True)
        
        files_copied = []
        
        # 1. Copy .H2K file from source directory
        h2k_source = os.path.join(source_h2k_dir, f"{house_name}.H2K")
        if not os.path.exists(h2k_source):
            h2k_source = os.path.join(source_h2k_dir, f"{house_name}.h2k")
        
        if os.path.exists(h2k_source):
            h2k_dest = os.path.join(dest_folder, os.path.basename(h2k_source))
            shutil.copy2(h2k_source, h2k_dest)
            files_copied.append(os.path.basename(h2k_source))
        
        # 2. Copy .xml file (HPXML) from house folder
        xml_source = os.path.join(house_path, f"{house_name}.xml")
        if os.path.exists(xml_source):
            xml_dest = os.path.join(dest_folder, f"{house_name}.xml")
            shutil.copy2(xml_source, xml_dest)
            files_copied.append(f"{house_name}.xml")
        
        # 3. Copy results CSV files from run/ subfolder with "hpxml_" prefix
        # Convert to Parquet and delete CSV files
        run_folder = os.path.join(house_path, "run")
        if os.path.exists(run_folder):
            result_files = [
                "results_timeseries.csv",
                "results_annual.csv"
            ]
            
            for result_file in result_files:
                source_file = os.path.join(run_folder, result_file)
                if os.path.exists(source_file):
                    # Add "hpxml_" prefix to destination filename
                    dest_filename = f"hpxml_{result_file}"
                    dest_csv = os.path.join(dest_folder, dest_filename)
                    
                    # Copy CSV file
                    shutil.copy2(source_file, dest_csv)
                    
                    # Convert to Parquet
                    dest_parquet = dest_csv.replace('.csv', '.parquet')
                    df = pd.read_csv(dest_csv, low_memory=False)
                    df.to_parquet(dest_parquet, index=False)
                    
                    # Delete CSV file after Parquet conversion
                    os.remove(dest_csv)
                    
                    # Track the Parquet file as copied
                    files_copied.append(dest_filename.replace('.csv', '.parquet'))
        
        if files_copied:
            copied_count += 1
            print(f"  {house_name}: Copied {', '.join(files_copied)}")
        else:
            print(f"  {house_name}: No files found to copy")
    
    return copied_count


def main():
    parser = argparse.ArgumentParser(description="Extract data from EnergyPlus SQL files")
    parser.add_argument('input_dir', help='Directory containing eplusout.sql files')
    parser.add_argument('--hourly', action='store_true', 
                       help='Extract hourly simulation data in BTAP format (one parquet file per building)')
    parser.add_argument('--timestep', action='store_true',
                       help='Extract sub-hourly timestep data in BTAP format (one parquet file per building)')
    parser.add_argument('--timesteps-per-hour', type=int, default=None,
                       help='Override auto-detected timesteps per hour for --timestep option')
    parser.add_argument('--delete-timeseries', action='store_true', #TODO delete this script and in the code that it generates this
                       help='Delete results_timeseries.parquet files from house ID folders in temporary_output_folder')
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Create temporary_output_folder for annual CSV
    temp_output_dir = os.path.join(args.input_dir, "temporary_output_folder")
    os.makedirs(temp_output_dir, exist_ok=True)
    
    # Copy source files (always done by default)
    # Source .H2K files are automatically found in parent directory of input_dir
    print("Copying h2k-hpxml output files to house folders...")
    copied_count = copy_h2k_output_files(args.input_dir, source_h2k_dir=None)
    if copied_count > 0:
        print(f"✓ Copied files for {copied_count} houses\n")
    else:
        print("No files copied\n")
    
    # Delete results_timeseries.parquet files if requested
    if args.delete_timeseries:
        deleted_count = 0
        for item in os.listdir(temp_output_dir):
            item_path = os.path.join(temp_output_dir, item)
            if os.path.isdir(item_path):
                timeseries_file = os.path.join(item_path, "results_timeseries.parquet")
                if os.path.exists(timeseries_file):
                    os.remove(timeseries_file)
                    deleted_count += 1
                    print(f"  Deleted: {item}/results_timeseries.parquet")
        if deleted_count > 0:
            print(f"✓ Deleted {deleted_count} results_timeseries.parquet files\n")
        else:
            print("No results_timeseries.parquet files found to delete\n")
        # Exit after cleanup if no other operations requested
        if not args.hourly and not args.timestep:
            return
    
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
    processed_count = 0
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
        peak_data = {}
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
            
            # Extract peak load data
            peak_data = extract_energy_peak_data(sql_path, floor_area)
        
        # Look for H2K file in parent directory
        h2k_path = os.path.join(parent_dir, f"{house_name}.H2K")
        if not os.path.exists(h2k_path):
            h2k_path = os.path.join(parent_dir, f"{house_name}.h2k")
        
        if os.path.exists(h2k_path):
            house_type = extract_house_type(h2k_path)
            location_city = extract_location_city(h2k_path)
            region = extract_region(h2k_path)
            primary_space_heating_fuel = extract_primary_space_heating_fuel(h2k_path)
            primary_dhw_fuel = extract_primary_dhw_fuel(h2k_path)
            year_built = extract_year_built(h2k_path)
        else:
            house_type = None
            location_city = None
            region = None
            primary_space_heating_fuel = None
            primary_dhw_fuel = None
            year_built = None
        
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
                'vintage': year_built if year_built is not None else '',
                'primary_space_heating_fuel': primary_space_heating_fuel or '',
                'primary_dhw_fuel': primary_dhw_fuel or '',
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
            
            # Add peak load data
            result.update(peak_data)
            
            # Write individual CSV for this house
            house_subdir = os.path.join(temp_output_dir, house_name)
            os.makedirs(house_subdir, exist_ok=True)
            house_csv = os.path.join(house_subdir, "sql_annual.csv")
            
            with open(house_csv, 'w', newline='') as f:
                # Sort columns alphabetically, keeping house_name first
                all_fields = list(result.keys())
                all_fields.remove('house_name')
                fieldnames = ['house_name'] + sorted(all_fields)
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(result)
            
            processed_count += 1
            type_str = f" ({house_type})" if house_type else ""
            net_eui_str = f", Net EUI: {net_site_eui:.3f}" if net_site_eui is not None else ""
            total_eui_str = f", Total EUI: {total_site_eui:.3f}" if total_site_eui is not None else ""
            unmet_cooling_str = f", Unmet Cooling: {unmet_hours_cooling_total:.1f} hrs ({unmet_hours_cooling_occupied:.1f} occupied)" if unmet_hours_cooling_total is not None and unmet_hours_cooling_occupied is not None else ""
            unmet_heating_str = f", Unmet Heating: {unmet_hours_heating_total:.1f} hrs ({unmet_hours_heating_occupied:.1f} occupied)" if unmet_hours_heating_total is not None and unmet_hours_heating_occupied is not None else ""
            print(f"{house_name}: {floor_area:.2f} m²{type_str}{net_eui_str}{total_eui_str} GJ/m²{unmet_cooling_str}{unmet_heating_str} → sql_annual.csv")
        
        # Extract hourly data if requested
        if args.hourly:
            house_subdir = os.path.join(temp_output_dir, house_name)
            os.makedirs(house_subdir, exist_ok=True)
            hourly_csv = os.path.join(house_subdir, "sql_hourly.csv")  # Will be converted to .parquet
            extract_hourly_data(sql_path, hourly_csv, house_name)
        
        # Extract timestep data if requested
        if args.timestep:
            house_subdir = os.path.join(temp_output_dir, house_name)
            os.makedirs(house_subdir, exist_ok=True)
            timestep_csv = os.path.join(house_subdir, "sql_timestep.csv")  # Will be converted to .parquet
            extract_timestep_data(sql_path, timestep_csv, house_name, args.timesteps_per_hour)
    
    # Print summary
    if processed_count > 0:
        print(f"\n✓ Processed {processed_count} buildings - sql_annual.csv saved in each house folder")
    else:
        print("No data extracted")
        sys.exit(1)


if __name__ == "__main__":
    main()