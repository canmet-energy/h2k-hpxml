"""
File management utilities for test data and golden files.

This module provides common functions for:
- Managing golden file paths and structures
- Creating backup directories
- Reading/writing JSON test data
- Path resolution and validation
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple


# Golden file directory structure
GOLDEN_FILES_BASE = "tests/fixtures/expected_outputs/golden_files"
BASELINE_DIR = os.path.join(GOLDEN_FILES_BASE, "baseline")
COMPARISON_DIR = os.path.join(GOLDEN_FILES_BASE, "comparison")
BACKUP_BASE_DIR = os.path.join(GOLDEN_FILES_BASE, "backup")


def get_baseline_summary_path() -> str:
    """Get path to baseline energy summary file."""
    return os.path.join(BASELINE_DIR, "baseline_energy_summary.json")


def get_comparison_summary_path() -> str:
    """Get path to comparison energy summary file."""
    return os.path.join(COMPARISON_DIR, "comparison_energy_summary.json")


def get_baseline_file_path(base_name: str) -> str:
    """Get path to individual baseline file."""
    return os.path.join(BASELINE_DIR, f"baseline_{base_name}.json")


def get_comparison_file_path(base_name: str) -> str:
    """Get path to individual comparison file."""
    return os.path.join(COMPARISON_DIR, f"comparison_{base_name}.json")


def ensure_golden_directories() -> None:
    """Ensure all golden file directories exist."""
    for directory in [BASELINE_DIR, COMPARISON_DIR]:
        os.makedirs(directory, exist_ok=True)


def create_backup_directory() -> str:
    """
    Create a timestamped backup directory.
    
    Returns:
        Path to the created backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_BASE_DIR, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def backup_golden_files() -> Optional[str]:
    """
    Create backup of existing golden files before overwriting.
    
    Returns:
        Path to backup directory if backup was created, None if no files to backup
    """
    if not os.path.exists(BASELINE_DIR):
        print("No baseline directory found, no backup needed")
        return None
    
    # Check if there are any files to backup
    baseline_files = [f for f in os.listdir(BASELINE_DIR) if f.endswith('.json')]
    if not baseline_files:
        print("No baseline files found, no backup needed")
        return None
    
    # Create backup directory
    backup_dir = create_backup_directory()
    
    # Copy all baseline files to backup
    files_backed_up = 0
    for file_name in baseline_files:
        src_path = os.path.join(BASELINE_DIR, file_name)
        dst_path = os.path.join(backup_dir, file_name)
        try:
            shutil.copy2(src_path, dst_path)
            files_backed_up += 1
        except Exception as e:
            print(f"Warning: Failed to backup {file_name}: {e}")
    
    print(f"✅ Backed up {files_backed_up} baseline files to: {backup_dir}")
    return backup_dir


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from file with error handling.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data or None if error
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Save JSON data to file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False


def load_baseline_summary() -> Optional[Dict[str, Any]]:
    """Load baseline energy summary."""
    return load_json_file(get_baseline_summary_path())


def save_baseline_summary(data: Dict[str, Any]) -> bool:
    """Save baseline energy summary."""
    return save_json_file(data, get_baseline_summary_path())


def load_comparison_summary() -> Optional[Dict[str, Any]]:
    """Load comparison energy summary."""
    return load_json_file(get_comparison_summary_path())


def save_comparison_summary(data: Dict[str, Any]) -> bool:
    """Save comparison energy summary."""
    return save_json_file(data, get_comparison_summary_path())


def load_baseline_file(base_name: str) -> Optional[Dict[str, Any]]:
    """Load individual baseline file."""
    return load_json_file(get_baseline_file_path(base_name))


def save_baseline_file(base_name: str, data: Dict[str, Any]) -> bool:
    """Save individual baseline file."""
    return save_json_file(data, get_baseline_file_path(base_name))


def load_comparison_file(base_name: str) -> Optional[Dict[str, Any]]:
    """Load individual comparison file."""
    return load_json_file(get_comparison_file_path(base_name))


def save_comparison_file(base_name: str, data: Dict[str, Any]) -> bool:
    """Save individual comparison file."""
    return save_json_file(data, get_comparison_file_path(base_name))


def get_baseline_file_list() -> List[str]:
    """Get list of available baseline files."""
    if not os.path.exists(BASELINE_DIR):
        return []
    
    baseline_files = []
    for file_name in os.listdir(BASELINE_DIR):
        if file_name.startswith('baseline_') and file_name.endswith('.json') and file_name != 'baseline_energy_summary.json':
            # Extract base name (remove baseline_ prefix and .json suffix)
            base_name = file_name[9:-5]  # Remove 'baseline_' and '.json'
            baseline_files.append(base_name)
    
    return sorted(baseline_files)


def validate_golden_file_structure() -> Tuple[bool, List[str]]:
    """
    Validate that golden file structure is complete and consistent.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check that directories exist
    for directory in [BASELINE_DIR, COMPARISON_DIR]:
        if not os.path.exists(directory):
            issues.append(f"Missing directory: {directory}")
    
    # Check that baseline summary exists
    baseline_summary_path = get_baseline_summary_path()
    if not os.path.exists(baseline_summary_path):
        issues.append(f"Missing baseline summary: {baseline_summary_path}")
        return False, issues
    
    # Load baseline summary and check consistency
    baseline_summary = load_baseline_summary()
    if not baseline_summary:
        issues.append("Failed to load baseline summary")
        return False, issues
    
    if "results" not in baseline_summary:
        issues.append("Baseline summary missing 'results' section")
        return False, issues
    
    # Check that individual baseline files exist for each entry in summary
    for file_name in baseline_summary["results"].keys():
        baseline_file_path = get_baseline_file_path(file_name)
        if not os.path.exists(baseline_file_path):
            issues.append(f"Missing baseline file: {baseline_file_path}")
    
    return len(issues) == 0, issues


def create_file_structure_summary() -> Dict[str, Any]:
    """Create a summary of the current golden file structure."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "directories": {},
        "file_counts": {},
        "total_size_bytes": 0
    }
    
    for dir_name, dir_path in [
        ("baseline", BASELINE_DIR),
        ("comparison", COMPARISON_DIR)
    ]:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
            total_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
            
            summary["directories"][dir_name] = {
                "path": dir_path,
                "files": files,
                "count": len(files),
                "total_size_bytes": total_size
            }
            summary["file_counts"][dir_name] = len(files)
            summary["total_size_bytes"] += total_size
        else:
            summary["directories"][dir_name] = {
                "path": dir_path,
                "exists": False
            }
            summary["file_counts"][dir_name] = 0
    
    return summary
