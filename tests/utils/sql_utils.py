"""
SQL database utilities for extracting energy data from EnergyPlus outputs.

This module provides common functions for:
- Extracting annual energy data from eplusout.sql files
- Database inspection and structure analysis
- Standardized data extraction methods
"""

import os
import sqlite3
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple


def inspect_sqlite_database(sql_path: str) -> None:
    """Inspect SQLite database structure for debugging."""
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()

            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            print(f"\n=== Database structure for {os.path.basename(sql_path)} ===")
            print(f"Available tables: {tables}")

            # For each table, show schema and sample data
            for table in tables[:5]:  # Limit to first 5 tables to avoid clutter
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"\nTable '{table}' columns:")
                    for col in columns:
                        print(f"  {col[1]} ({col[2]})")

                    # Show row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  Row count: {count}")

                except Exception as table_error:
                    print(f"  Error inspecting table {table}: {table_error}")

    except Exception as e:
        print(f"Error inspecting database {sql_path}: {e}")


def extract_from_standard_energyplus(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Extract energy data from standard EnergyPlus report format."""
    energy_data = {}

    try:
        # Get meter data
        meter_query = """
        SELECT rdd.Name, rdd.Units, rdd.KeyValue, SUM(rd.Value) as TotalValue
        FROM ReportDataDictionary rdd
        JOIN ReportData rd ON rdd.ReportDataDictionaryIndex = rd.ReportDataDictionaryIndex
        WHERE rdd.IsMeter = 1
          AND rdd.ReportingFrequency = 'Run Period'
          AND rdd.Name NOT LIKE '%Peak%'
          AND rdd.Name NOT LIKE '%Maximum%'
          AND rdd.Name NOT LIKE '%Minimum%'
        GROUP BY rdd.Name, rdd.Units, rdd.KeyValue
        HAVING SUM(rd.Value) > 0
        ORDER BY rdd.Name
        """

        cursor.execute(meter_query)
        meter_results = cursor.fetchall()
        print(f"Meter data query found {len(meter_results)} records")

        for row in meter_results:
            name, units, key_value, total_value = row

            # Use the end-use category as the top-level key
            category = name.split(":")[0] if ":" in name else name
            if category not in energy_data:
                energy_data[category] = {}

            # Use the meter name as the sub-key
            meter_key = name.split(":", 1)[1] if ":" in name else name
            energy_data[category][meter_key] = {
                "value": float(total_value),
                "units": units,
                "key_value": key_value,
            }

    except Exception as e:
        print(f"Error extracting meter data: {e}")

    # Extract tabular data
    try:
        energy_data.update(extract_from_tabular_data(cursor))
    except Exception as e:
        print(f"Error extracting tabular data: {e}")

    return energy_data


def extract_from_tabular_data(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Extract energy data from TabularData table with proper string joins."""
    tabular_data = {}

    try:
        # Check if the database uses the new index-based format
        cursor.execute("PRAGMA table_info(TabularData)")
        columns_info = cursor.fetchall()
        available_columns = [col[1] for col in columns_info]
        print(f"Available TabularData columns: {available_columns}")

        if "ReportNameIndex" in available_columns:
            # New format: join with Strings table to get actual text values
            tabular_query = """
            SELECT
                s1.Value as ReportName,
                s2.Value as TableName,
                s3.Value as RowName,
                s4.Value as ColumnName,
                td.Value,
                s5.Value as Units
            FROM TabularData td
            JOIN Strings s1 ON td.ReportNameIndex = s1.StringIndex
            JOIN Strings s2 ON td.TableNameIndex = s2.StringIndex
            JOIN Strings s3 ON td.RowNameIndex = s3.StringIndex
            JOIN Strings s4 ON td.ColumnNameIndex = s4.StringIndex
            LEFT JOIN Strings s5 ON td.UnitsIndex = s5.StringIndex
            WHERE s1.Value IN (
                'AnnualBuildingUtilityPerformanceSummary',
                'EnergyMeters',
                'Demand End Use Components Summary',
                'End Use Energy Consumption'
            )
            AND s4.Value NOT LIKE '%Peak%'
            AND s4.Value NOT LIKE '%Maximum%'
            AND s4.Value NOT LIKE '%Minimum%'
            AND td.Value IS NOT NULL
            AND TRIM(td.Value) != ''
            AND CAST(TRIM(td.Value) AS REAL) > 0
            ORDER BY s1.Value, s2.Value, s3.Value, s4.Value
            """
        else:
            # Old format: direct column access
            tabular_query = """
            SELECT ReportName, TableName, RowName, ColumnName, Value, Units
            FROM TabularData
            WHERE ReportName IN (
                'AnnualBuildingUtilityPerformanceSummary',
                'EnergyMeters',
                'Demand End Use Components Summary',
                'End Use Energy Consumption'
            )
            AND ColumnName NOT LIKE '%Peak%'
            AND ColumnName NOT LIKE '%Maximum%'
            AND ColumnName NOT LIKE '%Minimum%'
            AND Value IS NOT NULL
            AND TRIM(Value) != ''
            AND CAST(Value AS REAL) > 0
            ORDER BY ReportName, TableName, RowName, ColumnName
            """

        cursor.execute(tabular_query)
        tabular_results = cursor.fetchall()
        print(f"Tabular data query found {len(tabular_results)} records")

        for row in tabular_results:
            report_name, table_name, row_name, column_name, value, units = row

            # Build nested structure
            if report_name not in tabular_data:
                tabular_data[report_name] = {}
            if table_name not in tabular_data[report_name]:
                tabular_data[report_name][table_name] = {}
            if row_name not in tabular_data[report_name][table_name]:
                tabular_data[report_name][table_name][row_name] = {}

            # Store the data (clean up value string and convert to float)
            clean_value = str(value).strip()
            try:
                numeric_value = float(clean_value)
                tabular_data[report_name][table_name][row_name][column_name] = {
                    "value": numeric_value,
                    "units": units if units else "",
                }
            except ValueError:
                print(
                    f"Skipping non-numeric value: '{clean_value}' for {report_name}/{table_name}/{row_name}/{column_name}"
                )

    except Exception as e:
        print(f"Error extracting tabular data: {e}")

    return tabular_data


def extract_from_hpxml_reports(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Extract energy data from OpenStudio-HPXML report format."""
    energy_data = {}

    try:
        # Try to extract from ComponentSummaryReport table
        cursor.execute("SELECT * FROM ComponentSummaryReport LIMIT 5")
        results = cursor.fetchall()
        print(f"Found {len(results)} records in ComponentSummaryReport")

        # This would need to be customized based on actual HPXML report structure
        # For now, return empty structure
        energy_data["HPXML_Reports"] = {
            "note": "HPXML format detected but extraction not yet implemented"
        }

    except Exception as e:
        print(f"Error extracting HPXML data: {e}")

    return energy_data


def extract_from_generic_tables(cursor: sqlite3.Cursor, tables: List[str]) -> Dict[str, Any]:
    """Extract energy data from any available tables as fallback."""
    energy_data = {}

    for table in tables:
        try:
            # Get sample data from each table
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cursor.fetchall()

            if sample_data:
                energy_data[f"Generic_{table}"] = {
                    "sample_records": len(sample_data),
                    "note": f"Data found in {table} but no specific extraction method available",
                }

        except Exception as e:
            print(f"Error sampling table {table}: {e}")

    return energy_data


def extract_annual_energy_data(sql_path: str) -> Dict[str, Any]:
    """
    Extract annual energy end-use data from eplusout.sql.

    This is the main entry point for energy data extraction.
    It automatically detects the database format and uses the appropriate
    extraction method.

    Args:
        sql_path: Path to the eplusout.sql file

    Returns:
        Dictionary containing extracted energy data
    """
    try:
        with sqlite3.connect(sql_path) as conn:
            cursor = conn.cursor()

            # First inspect the database to understand its structure
            inspect_sqlite_database(sql_path)

            # Get available tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            energy_data = {}

            # Different databases have different schemas, try to adapt
            if "ReportDataDictionary" in tables and "ReportData" in tables:
                # Standard EnergyPlus output format
                print("\nUsing standard EnergyPlus report format...")
                energy_data = extract_from_standard_energyplus(cursor)

            elif "ComponentSummaryReport" in tables:
                # OpenStudio-HPXML format
                print("\nUsing OpenStudio-HPXML report format...")
                energy_data = extract_from_hpxml_reports(cursor)

            else:
                # Try to find any energy-related data in available tables
                print(f"\nTrying to extract energy data from available tables: {tables}")
                energy_data = extract_from_generic_tables(cursor, tables)

            print(f"Final energy data structure has {len(energy_data)} categories")
            return energy_data

    except Exception as e:
        print(f"Error extracting energy data from {sql_path}: {e}")
        return {}


def count_energy_records(energy_data: Dict[str, Any]) -> int:
    """Count the total number of energy value records in the data structure."""
    count = 0

    def count_recursive(data):
        nonlocal count
        if isinstance(data, dict):
            if "value" in data:
                count += 1
            else:
                for value in data.values():
                    count_recursive(value)

    count_recursive(energy_data)
    return count


def validate_energy_data(energy_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that energy data contains meaningful values.

    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not energy_data:
        return False, "No energy data found"

    record_count = count_energy_records(energy_data)
    if record_count == 0:
        return False, "No energy value records found in data structure"

    if record_count < 5:
        return (
            False,
            f"Only {record_count} energy records found, expected more for a complete simulation",
        )

    return True, f"Validation passed: {record_count} energy records found"
