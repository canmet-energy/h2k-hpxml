"""
Cleanup utilities for test data and temporary files.

This module provides functions for cleaning up test outputs, temporary files,
and comparison data to ensure fresh test runs.
"""

import os
import shutil
from typing import List, Tuple


def clean_temp_directory() -> Tuple[bool, List[str]]:
    """
    Clean the entire tests/temp directory.
    
    Returns:
        Tuple of (success, list_of_cleaned_items)
    """
    temp_dir = "tests/temp"
    cleaned_items = []
    
    if not os.path.exists(temp_dir):
        return True, ["temp directory doesn't exist - nothing to clean"]
    
    try:
        # List what we're about to clean
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                cleaned_items.append(f"directory: {item}/")
            else:
                cleaned_items.append(f"file: {item}")
        
        # Remove everything in temp directory
        shutil.rmtree(temp_dir)
        
        # Recreate empty temp directory
        os.makedirs(temp_dir, exist_ok=True)
        
        return True, cleaned_items
        
    except Exception as e:
        return False, [f"Error cleaning temp directory: {str(e)}"]


def clean_comparison_files() -> Tuple[bool, List[str]]:
    """
    Clean comparison files and directories.
    
    Returns:
        Tuple of (success, list_of_cleaned_items)
    """
    comparison_dir = "tests/fixtures/expected_outputs/golden_files/comparison"
    cleaned_items = []
    
    if not os.path.exists(comparison_dir):
        return True, ["comparison directory doesn't exist - nothing to clean"]
    
    try:
        # List what we're about to clean
        for item in os.listdir(comparison_dir):
            item_path = os.path.join(comparison_dir, item)
            if os.path.isdir(item_path):
                cleaned_items.append(f"comparison directory: {item}/")
                shutil.rmtree(item_path)
            else:
                cleaned_items.append(f"comparison file: {item}")
                os.remove(item_path)
        
        return True, cleaned_items
        
    except Exception as e:
        return False, [f"Error cleaning comparison files: {str(e)}"]


def clean_pytest_cache() -> Tuple[bool, List[str]]:
    """
    Clean pytest cache files.
    
    Returns:
        Tuple of (success, list_of_cleaned_items)
    """
    cache_dirs = [
        ".pytest_cache",
        "tests/.pytest_cache",
        "tests/fixtures/expected_outputs/.pytest_cache"
    ]
    
    cleaned_items = []
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                cleaned_items.append(f"pytest cache: {cache_dir}")
            except Exception as e:
                cleaned_items.append(f"Error cleaning {cache_dir}: {str(e)}")
    
    if not cleaned_items:
        cleaned_items.append("No pytest cache directories found")
    
    return True, cleaned_items


def clean_pycache() -> Tuple[bool, List[str]]:
    """
    Clean Python __pycache__ directories.
    
    Returns:
        Tuple of (success, list_of_cleaned_items)
    """
    cleaned_items = []
    
    # Walk through directory tree to find __pycache__ directories
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                cleaned_items.append(f"pycache: {pycache_path}")
            except Exception as e:
                cleaned_items.append(f"Error cleaning {pycache_path}: {str(e)}")
    
    if not cleaned_items:
        cleaned_items.append("No __pycache__ directories found")
    
    return True, cleaned_items


def clean_all_test_data() -> Tuple[bool, List[str]]:
    """
    Clean all test data including temp files, comparison files, and caches.
    
    This function provides a comprehensive cleanup for fresh test runs.
    
    Returns:
        Tuple of (success, list_of_all_cleaned_items)
    """
    all_cleaned = []
    all_success = True
    
    print("🧹 Starting comprehensive test data cleanup...")
    
    # Clean temp directory
    success, items = clean_temp_directory()
    all_cleaned.extend([f"TEMP: {item}" for item in items])
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned temp directory ({len(items)} items)")
    else:
        print(f"❌ Failed to clean temp directory")
    
    # Clean comparison files
    success, items = clean_comparison_files()
    all_cleaned.extend([f"COMPARISON: {item}" for item in items])
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned comparison files ({len(items)} items)")
    else:
        print(f"❌ Failed to clean comparison files")
    
    # Clean pytest cache
    success, items = clean_pytest_cache()
    all_cleaned.extend([f"PYTEST_CACHE: {item}" for item in items])
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned pytest cache ({len(items)} items)")
    else:
        print(f"❌ Failed to clean pytest cache")
    
    # Clean Python cache
    success, items = clean_pycache()
    all_cleaned.extend([f"PYCACHE: {item}" for item in items])
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned Python cache ({len(items)} items)")
    else:
        print(f"❌ Failed to clean Python cache")
    
    print(f"🎯 Cleanup complete! Total items cleaned: {len(all_cleaned)}")
    
    return all_success, all_cleaned


def clean_for_baseline_generation() -> Tuple[bool, List[str]]:
    """
    Specialized cleanup for baseline generation.
    
    This cleans only what's necessary for fresh baseline generation
    while preserving existing baseline files.
    
    Returns:
        Tuple of (success, list_of_cleaned_items)
    """
    all_cleaned = []
    all_success = True
    
    print("🧹 Cleaning for fresh baseline generation...")
    
    # Clean temp directory (simulation outputs)
    success, items = clean_temp_directory()
    all_cleaned.extend(items)
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned simulation temp files ({len(items)} items)")
    
    # Clean comparison files (test results)
    success, items = clean_comparison_files()
    all_cleaned.extend(items)
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned comparison test results ({len(items)} items)")
    
    # Clean pytest cache
    success, items = clean_pytest_cache()
    all_cleaned.extend(items)
    all_success = all_success and success
    if success:
        print(f"✅ Cleaned pytest cache ({len(items)} items)")
    
    print(f"🎯 Baseline cleanup complete! Ready for fresh golden file generation.")
    
    return all_success, all_cleaned