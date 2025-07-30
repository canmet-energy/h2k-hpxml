#!/bin/bash
# Clean up generated files and caches

echo "🧹 Cleaning up h2k_hpxml project..."

# Remove Python cache
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove test and build caches
echo "Removing tool caches..."
rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .hypothesis/ 2>/dev/null || true

# Clean output directory but keep structure
if [ -d "output" ]; then
    echo "Cleaning output directories..."
    rm -rf output/hpxml/* 2>/dev/null || true
    rm -rf output/comparisons/* 2>/dev/null || true
    rm -rf output/workflows/* 2>/dev/null || true
    rm -rf output/logs/* 2>/dev/null || true
    echo "✅ Cleaned output directories (structure preserved)"
fi

# Remove test result files
rm -f test_results_*.txt 2>/dev/null || true

# Remove any temporary files
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
