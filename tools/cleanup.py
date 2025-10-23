#!/usr/bin/env python3
"""
Cross-platform cleanup script for h2k_hpxml project.

Removes Python cache files, tool caches, and temporary files while preserving
directory structure. Works on Windows, Linux, and macOS.
"""

import os
import shutil
import sys
from pathlib import Path


def remove_tree_if_exists(path):
    """Remove directory tree if it exists, ignore errors."""
    try:
        if Path(path).exists():
            shutil.rmtree(path)
            print(f"  Removed: {path}")
            return True
    except (OSError, PermissionError) as e:
        print(f"  Warning: Could not remove {path}: {e}")
    return False


def remove_file_if_exists(path):
    """Remove file if it exists, ignore errors."""
    try:
        if Path(path).exists():
            os.unlink(path)
            return True
    except (OSError, PermissionError) as e:
        print(f"  Warning: Could not remove {path}: {e}")
    return False


def find_and_remove_pattern(root_path, pattern, file_type="file"):
    """Find and remove files or directories matching pattern."""
    removed_count = 0
    try:
        for path in Path(root_path).rglob(pattern):
            try:
                if file_type == "file" and path.is_file():
                    path.unlink()
                    removed_count += 1
                elif file_type == "dir" and path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
            except (OSError, PermissionError):
                # Ignore permission errors, continue cleanup
                pass
    except Exception as e:
        print(f"  Warning: Error searching for {pattern}: {e}")

    return removed_count


def clean_output_directory():
    """Clean output directories while preserving structure."""
    output_dir = Path("output")
    if not output_dir.exists():
        return False

    subdirs = ["hpxml", "comparisons", "workflows", "logs", "test"]
    cleaned_any = False

    for subdir in subdirs:
        subdir_path = output_dir / subdir
        if subdir_path.exists():
            try:
                # Remove contents but keep the directory
                for item in subdir_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                        cleaned_any = True
                    except (OSError, PermissionError):
                        # Continue with other files if one fails
                        pass
                print(f"  Cleaned: {subdir_path}")
            except Exception as e:
                print(f"  Warning: Could not clean {subdir_path}: {e}")

    return cleaned_any


def main():
    """Main cleanup function."""
    print("🧹 Cleaning up h2k_hpxml project...")

    # Get project root (assuming script is in tools/)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    cleanup_count = 0

    # 1. Remove Python cache files
    print("\nRemoving Python cache files...")
    pycache_count = find_and_remove_pattern(".", "__pycache__", "dir")
    pyc_count = find_and_remove_pattern(".", "*.pyc", "file")
    pyo_count = find_and_remove_pattern(".", "*.pyo", "file")

    if pycache_count or pyc_count or pyo_count:
        print(
            f"  Removed {pycache_count} __pycache__ dirs, {pyc_count} .pyc files, {pyo_count} .pyo files"
        )
        cleanup_count += pycache_count + pyc_count + pyo_count

    # 2. Remove test and build caches
    print("\nRemoving tool caches...")
    cache_dirs = [
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".coverage",
        "build",
        "dist",
        "*.egg-info",
    ]

    cache_removed = 0
    for cache_dir in cache_dirs:
        if "*" in cache_dir:
            # Handle glob patterns
            cache_removed += find_and_remove_pattern(".", cache_dir, "dir")
        else:
            if remove_tree_if_exists(cache_dir):
                cache_removed += 1

    if cache_removed:
        cleanup_count += cache_removed

    # 3. Clean output directory but keep structure
    print("\nCleaning output directories...")
    if clean_output_directory():
        print("  ✅ Cleaned output directories (structure preserved)")
        cleanup_count += 1
    else:
        print("  No output directory found or nothing to clean")

    # 4. Remove test result files
    print("\nRemoving temporary files...")
    temp_patterns = [
        "test_results_*.txt",
        "*.tmp",
        "*.temp",
        "*.bak",
        ".DS_Store",  # macOS
        "Thumbs.db",  # Windows
        "desktop.ini",  # Windows
    ]

    temp_removed = 0
    for pattern in temp_patterns:
        temp_removed += find_and_remove_pattern(".", pattern, "file")

    if temp_removed:
        print(f"  Removed {temp_removed} temporary files")
        cleanup_count += temp_removed

    # 5. Clean up any temporary test directories
    print("\nRemoving temporary test directories...")
    temp_dir_patterns = ["tmp*", "temp*", "tests/temp", "tests/tmp*"]

    temp_dirs_removed = 0
    for pattern in temp_dir_patterns:
        temp_dirs_removed += find_and_remove_pattern(".", pattern, "dir")

    if temp_dirs_removed:
        print(f"  Removed {temp_dirs_removed} temporary directories")
        cleanup_count += temp_dirs_removed

    # Final summary
    print(f"\n✅ Cleanup complete! Removed {cleanup_count} items")

    if cleanup_count == 0:
        print("   (Project was already clean)")


if __name__ == "__main__":
    main()
