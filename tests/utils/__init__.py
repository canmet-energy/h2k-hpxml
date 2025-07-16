"""
Test utilities for common functionality across test modules.

This module provides shared utilities to reduce code duplication
and maintain consistency across test files.
"""

# Import commonly used functions for easy access
from .sql_utils import (
    extract_annual_energy_data,
    count_energy_records,
    validate_energy_data,
    inspect_sqlite_database
)

from .workflow_utils import (
    run_h2k_workflow,
    find_sql_file,
    find_hpxml_file,
    validate_workflow_outputs,
    get_h2k_example_files,
    explore_output_directory
)

from .file_utils import (
    get_baseline_file_path,
    get_comparison_file_path,
    get_baseline_summary_path,
    get_comparison_summary_path,
    get_baseline_hpxml_path,
    get_comparison_hpxml_path,
    get_baseline_hpxml_summary_path,
    get_comparison_hpxml_summary_path,
    ensure_golden_directories,
    backup_golden_files,
    load_baseline_file,
    save_baseline_file,
    load_comparison_file,
    save_comparison_file,
    load_baseline_summary,
    save_baseline_summary,
    load_comparison_summary,
    save_comparison_summary,
    validate_golden_file_structure
)

from .comparison_utils import (
    compare_energy_values,
    generate_comparison_summary,
    format_comparison_report,
    calculate_percentage_difference,
    validate_comparison_data
)

from .hpxml_utils import (
    extract_hpxml_key_elements,
    compare_hpxml_files,
    validate_hpxml_structure,
    create_hpxml_summary,
    normalize_hpxml_for_comparison
)

from .cleanup_utils import (
    clean_temp_directory,
    clean_comparison_files,
    clean_pytest_cache,
    clean_pycache,
    clean_all_test_data,
    clean_for_baseline_generation
)

__all__ = [
    # SQL utilities
    'extract_annual_energy_data',
    'count_energy_records', 
    'validate_energy_data',
    'inspect_sqlite_database',
    
    # Workflow utilities
    'run_h2k_workflow',
    'find_sql_file',
    'find_hpxml_file',
    'validate_workflow_outputs',
    'get_h2k_example_files',
    'explore_output_directory',
    
    # File utilities
    'get_baseline_file_path',
    'get_comparison_file_path',
    'get_baseline_summary_path',
    'get_comparison_summary_path',
    'get_baseline_hpxml_path',
    'get_comparison_hpxml_path',
    'get_baseline_hpxml_summary_path',
    'get_comparison_hpxml_summary_path',
    'ensure_golden_directories',
    'backup_golden_files',
    'load_baseline_file',
    'save_baseline_file',
    'load_comparison_file',
    'save_comparison_file',
    'load_baseline_summary',
    'save_baseline_summary',
    'load_comparison_summary',
    'save_comparison_summary',
    'validate_golden_file_structure',
    
    # Comparison utilities
    'compare_energy_values',
    'generate_comparison_summary',
    'format_comparison_report',
    'calculate_percentage_difference',
    'validate_comparison_data',
    
    # HPXML utilities
    'extract_hpxml_key_elements',
    'compare_hpxml_files',
    'validate_hpxml_structure',
    'create_hpxml_summary',
    'normalize_hpxml_for_comparison',
    
    # Cleanup utilities
    'clean_temp_directory',
    'clean_comparison_files',
    'clean_pytest_cache',
    'clean_pycache',
    'clean_all_test_data',
    'clean_for_baseline_generation'
]
