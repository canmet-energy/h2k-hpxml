"""
SQLite database for tracking H2K to HPXML processing results.

This module provides a ResultsDatabase class for recording the success/failure
status of each H2K file processed, along with timing, errors, and metadata.
"""

import os
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class ResultsDatabase:
    """
    SQLite database for recording H2K to HPXML conversion results.

    Attributes:
        db_path (str): Path to the SQLite database file
        conn (sqlite3.Connection): Database connection
    """

    def __init__(self, db_path: str):
        """
        Initialize the results database.

        Args:
            db_path: Path where the SQLite database should be created
        """
        self.db_path = db_path
        self.conn = None
        self._lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Create database and schema if it doesn't exist."""
        # Allow connection to be used across threads with proper locking
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")

        cursor = self.conn.cursor()

        # Create main results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                filename TEXT,
                directory TEXT,
                status TEXT CHECK(status IN ('Success', 'Failure')) NOT NULL,

                -- Timing information
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,

                -- Output information
                hpxml_output_path TEXT,

                -- Error/warning information
                error_message TEXT,
                error_type TEXT,
                error_category TEXT,
                warnings TEXT,

                -- Processing metadata
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                worker_id INTEGER
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON processing_results(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_error_type
            ON processing_results(error_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_directory
            ON processing_results(directory)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filename
            ON processing_results(filename)
        """)

        self.conn.commit()

    def _categorize_error(self, error_message: str) -> tuple[str, str]:
        """
        Categorize error message into type and category.

        Args:
            error_message: Full error message text

        Returns:
            Tuple of (error_type, error_category)
            error_type: Specific element/issue (e.g., "Area", "AssemblyEffectiveRValue")
            error_category: General category (e.g., "Validation", "HVAC", "Enclosure")
        """
        if not error_message:
            return None, None

        # Validation errors (must be > 0)
        if "must be greater than '0'" in error_message or "must be greater than 0" in error_message:
            match = re.search(r"Element '(\w+)'", error_message)
            if match:
                element = match.group(1)
                category_map = {
                    'Area': 'Enclosure',
                    'AssemblyEffectiveRValue': 'Enclosure',
                    'EnergyFactor': 'Systems',
                    'TankVolume': 'Systems',
                    'SensibleRecoveryEfficiency': 'Ventilation',
                    'CoolingSensibleHeatFraction': 'HVAC',
                    'Value': 'Validation'
                }
                category = category_map.get(element, 'Validation')
                return f"{element}_GreaterThanZero", category

        # Heat pump switchover temperature
        if "Switchover temperature should only be used for a heat pump with fossil fuel backup" in error_message:
            return "HeatPump_SwitchoverTemperature", "HVAC"

        # ERV/HRV effectiveness
        if "ERV/HRV sensible effectiveness" in error_message and "should be between 0 and 1" in error_message:
            return "ERV_HRV_EffectivenessRange", "Ventilation"

        # Multiple heating systems
        if "Multiple heating systems found attached to distribution system" in error_message:
            return "MultipleHeatingSystems", "HVAC"

        # Missing floor/slab
        if "There must be at least one floor or slab adjacent to conditioned space" in error_message:
            return "MissingFloorSlab", "Enclosure"

        # Ventilation fan missing UsedFor element
        if "Expected 1 element(s) for xpath: UsedForWholeBuildingVentilation" in error_message:
            return "VentilationFan_MissingUsedFor", "Ventilation"

        # Location mismatch
        if "location is specified" in error_message and "but no surfaces were found adjacent to this space type" in error_message:
            match = re.search(r'location is specified as "([^"]+)"', error_message)
            location = match.group(1) if match else "unknown"
            return f"LocationMismatch_{location.replace(' ', '_')}", "Enclosure"

        # Weather file errors
        if "Could not find a CWEC2020.zip file" in error_message or "weather" in error_message.lower():
            return "WeatherFile_NotFound", "Weather"

        # Schema validation errors
        if "This element is not expected" in error_message:
            return "Schema_UnexpectedElement", "Validation"

        if "is not a valid value" in error_message:
            return "Schema_InvalidValue", "Validation"

        # Translation errors
        if "Failed to process" in error_message:
            if "systems and loads" in error_message:
                return "Translation_SystemsLoads", "Systems"
            if "weather data" in error_message:
                return "Translation_Weather", "Weather"
            return "Translation_Error", "Translation"

        # Default
        return "Uncategorized", "Other"

    def record_start(self, filepath: str, worker_id: Optional[int] = None) -> int:
        """
        Record the start of processing for a file.

        Args:
            filepath: Path to the H2K file being processed
            worker_id: Optional worker/thread ID for parallel processing

        Returns:
            Database record ID for this processing run
        """
        cursor = self.conn.cursor()

        path_obj = Path(filepath)
        filename = path_obj.name
        directory = str(path_obj.parent)
        start_time = datetime.now()

        cursor.execute("""
            INSERT INTO processing_results
            (filepath, filename, directory, status, start_time, worker_id)
            VALUES (?, ?, ?, 'Success', ?, ?)
        """, (filepath, filename, directory, start_time, worker_id))

        self.conn.commit()
        return cursor.lastrowid

    def record_success(
        self,
        filepath: str,
        hpxml_output_path: str,
        start_time: Optional[datetime] = None,
        warnings: Optional[str] = None,
        worker_id: Optional[int] = None
    ):
        """
        Record a successful H2K to HPXML conversion.

        Args:
            filepath: Path to the H2K file
            hpxml_output_path: Path to the generated HPXML file
            start_time: When processing started (for duration calculation)
            warnings: Any warnings generated during processing
            worker_id: Optional worker/thread ID
        """
        with self._lock:
            cursor = self.conn.cursor()

            path_obj = Path(filepath)
            filename = path_obj.name
            directory = str(path_obj.parent)
            end_time = datetime.now()

            duration = None
            if start_time:
                duration = (end_time - start_time).total_seconds()

            cursor.execute("""
                INSERT INTO processing_results
                (filepath, filename, directory, status, start_time, end_time,
                 duration_seconds, hpxml_output_path, warnings, worker_id)
                VALUES (?, ?, ?, 'Success', ?, ?, ?, ?, ?, ?)
            """, (filepath, filename, directory, start_time, end_time,
                  duration, hpxml_output_path, warnings, worker_id))

            self.conn.commit()

    def record_failure(
        self,
        filepath: str,
        error_message: str,
        start_time: Optional[datetime] = None,
        warnings: Optional[str] = None,
        worker_id: Optional[int] = None
    ):
        """
        Record a failed H2K to HPXML conversion.

        Args:
            filepath: Path to the H2K file
            error_message: Error message or stack trace
            start_time: When processing started (for duration calculation)
            warnings: Any warnings generated before failure
            worker_id: Optional worker/thread ID
        """
        with self._lock:
            cursor = self.conn.cursor()

            path_obj = Path(filepath)
            filename = path_obj.name
            directory = str(path_obj.parent)
            end_time = datetime.now()

            duration = None
            if start_time:
                duration = (end_time - start_time).total_seconds()

            # Categorize the error
            error_type, error_category = self._categorize_error(error_message)

            cursor.execute("""
                INSERT INTO processing_results
                (filepath, filename, directory, status, start_time, end_time,
                 duration_seconds, error_message, error_type, error_category,
                 warnings, worker_id)
                VALUES (?, ?, ?, 'Failure', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filepath, filename, directory, start_time, end_time, duration,
                  error_message, error_type, error_category, warnings, worker_id))

            self.conn.commit()

    def get_summary(self) -> dict:
        """
        Get summary statistics of processing results.

        Returns:
            Dictionary with summary statistics
        """
        with self._lock:
            cursor = self.conn.cursor()

            # Total counts
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN status = 'Failure' THEN 1 ELSE 0 END) as failures
                FROM processing_results
            """)
            total, successes, failures = cursor.fetchone()

            # Error type counts
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM processing_results
                WHERE status = 'Failure' AND error_type IS NOT NULL
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 10
            """)
            top_errors = cursor.fetchall()

            # Error category counts
            cursor.execute("""
                SELECT error_category, COUNT(*) as count
                FROM processing_results
                WHERE status = 'Failure' AND error_category IS NOT NULL
                GROUP BY error_category
                ORDER BY count DESC
            """)
            error_categories = cursor.fetchall()

            return {
                'total': total,
                'successes': successes,
                'failures': failures,
                'success_rate': (successes / total * 100) if total > 0 else 0,
                'top_error_types': top_errors,
                'error_categories': error_categories
            }

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
