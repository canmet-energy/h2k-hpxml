"""
Test utilities for common functionality across test modules.

This module provides shared utilities to reduce code duplication
and maintain consistency across test files.
"""

# Import commonly used functions for easy access
from .cleanup_utils import clean_all_test_data
from .cleanup_utils import clean_for_baseline_generation

# Other cleanup functions removed - only used by external scripts, not tests
from .comparison_utils import calculate_percentage_difference

# generate_comparison_summary, format_comparison_report, validate_comparison_data removed - unused
from .comparison_utils import compare_energy_values
from .file_utils import get_baseline_file_path
from .file_utils import get_baseline_hpxml_path
from .file_utils import get_baseline_hpxml_summary_path
from .file_utils import get_baseline_summary_path
from .file_utils import get_comparison_file_path
from .file_utils import get_comparison_hpxml_path
from .file_utils import get_comparison_hpxml_summary_path
from .file_utils import get_comparison_summary_path
from .file_utils import load_baseline_file
from .file_utils import load_baseline_summary
from .file_utils import load_comparison_file
from .file_utils import load_comparison_summary
from .file_utils import save_baseline_file
from .file_utils import save_baseline_summary
from .file_utils import save_comparison_file
from .file_utils import save_comparison_summary

# ensure_golden_directories, backup_golden_files, validate_golden_file_structure removed - unused
from .hpxml_utils import compare_hpxml_files
from .hpxml_utils import create_hpxml_summary

# validate_hpxml_structure, normalize_hpxml_for_comparison removed - unused
from .hpxml_utils import extract_hpxml_key_elements
from .sql_utils import extract_annual_energy_data

# count_energy_records, validate_energy_data, inspect_sqlite_database removed - unused
from .workflow_utils import find_hpxml_file
from .workflow_utils import find_sql_file
from .workflow_utils import get_h2k_example_files

# validate_workflow_outputs, explore_output_directory removed - unused
from .workflow_utils import run_h2k_workflow
