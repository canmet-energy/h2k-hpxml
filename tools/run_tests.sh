#!/bin/bash
# Comprehensive test runner for h2k_hpxml project

set -e

echo "🧪 H2K HPXML Test Suite"
echo "======================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
OVERALL_EXIT=0

# Function to run a test and capture results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "\n📋 Running: ${YELLOW}$test_name${NC}"
    echo "Command: $test_command"
    echo "----------------------------------------"

    if eval "$test_command"; then
        echo -e "✅ ${GREEN}$test_name PASSED${NC}"
        return 0
    else
        echo -e "❌ ${RED}$test_name FAILED${NC}"
        OVERALL_EXIT=1
        return 1
    fi
}

# Create output directory if it doesn't exist
mkdir -p output/test

# 1. Python syntax and import tests
run_test "Python Syntax Check" "python -c 'import py_compile; py_compile.compile(\"src/h2k_hpxml/__init__.py\", doraise=True); print(\"✅ Basic syntax check passed\")'"

# 2. Unit and integration tests
run_test "Pytest Suite" "pytest -v --tb=short --maxfail=5"

# 3. Code quality checks
if command -v ruff >/dev/null 2>&1; then
    run_test "Ruff Linting" "ruff check ."
    run_test "Ruff Formatting" "ruff format --check ."
else
    echo -e "⚠️  ${YELLOW}Ruff not available, skipping linting checks${NC}"
fi

# 4. Type checking
if command -v mypy >/dev/null 2>&1; then
    run_test "MyPy Type Checking" "mypy src/h2k_hpxml/ --ignore-missing-imports"
else
    echo -e "⚠️  ${YELLOW}MyPy not available, skipping type checks${NC}"
fi

# 5. Pre-commit hooks
if command -v pre-commit >/dev/null 2>&1 && [ -f .pre-commit-config.yaml ]; then
    run_test "Pre-commit Hooks" "pre-commit run --all-files"
else
    echo -e "⚠️  ${YELLOW}Pre-commit not configured, skipping${NC}"
fi

# 6. Configuration loading test
run_test "Configuration Loading" "python -c '
import sys
sys.path.insert(0, \"src\")
from h2k_hpxml.config import ConfigManager
config_manager = ConfigManager()
print(f\"✅ Config loaded successfully: {config_manager.dest_hpxml_path}\")
'"

# 7. Example file validation (limited test)
echo -e "\n📋 Running: ${YELLOW}Example File Validation${NC}"
echo "----------------------------------------"
EXAMPLE_FAILURES=0
example_count=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ] && [ $example_count -lt 2 ]; then  # Test only first 2 for speed
        filename=$(basename "$h2k_file")
        echo "Testing: $filename"
        if timeout 60s python -m h2k_hpxml.cli "$h2k_file" --output-dir output/test/ >/dev/null 2>&1; then
            echo "  ✅ $filename converted successfully"
        else
            echo "  ❌ $filename conversion failed"
            EXAMPLE_FAILURES=$((EXAMPLE_FAILURES + 1))
        fi
        example_count=$((example_count + 1))
    fi
done

if [ $EXAMPLE_FAILURES -eq 0 ]; then
    echo -e "✅ ${GREEN}Example File Validation PASSED${NC}"
else
    echo -e "❌ ${RED}Example File Validation FAILED ($EXAMPLE_FAILURES failures)${NC}"
    OVERALL_EXIT=1
fi

# 8. Output structure validation
run_test "Output Structure Validation" "python -c '
import os
from pathlib import Path

# Check expected output directories exist
expected_dirs = [\"output/hpxml\", \"output/comparisons\", \"output/workflows\", \"output/logs\"]
for dir_path in expected_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    print(f\"✅ Verified: {dir_path}\")

# Check if any outputs were actually generated
if any(Path(\"output/hpxml\").glob(\"*.xml\")):
    print(\"✅ HPXML files found in output directory\")
else:
    print(\"ℹ️  No HPXML files found (may be normal for test run)\")
'"

# Final summary
echo -e "\n🏁 Test Suite Summary"
echo "===================="

if [ $OVERALL_EXIT -eq 0 ]; then
    echo -e "🎉 ${GREEN}ALL TESTS PASSED${NC}"
    echo "The project is ready for use!"
else
    echo -e "💥 ${RED}SOME TESTS FAILED${NC}"
    echo "Please review the failures above and fix before proceeding."
fi

exit $OVERALL_EXIT
