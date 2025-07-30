#!/bin/bash
# Quality check script for H2K-HPXML project
# Run all code quality tools and report results

set -e

echo "🔍 Running H2K-HPXML Code Quality Checks..."
echo "============================================="

# Change to project root
cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# Function to run a check and report status
run_check() {
    local check_name="$1"
    local command="$2"

    echo ""
    echo -e "${BLUE}Running $check_name...${NC}"
    echo "----------------------------------------"

    if eval "$command"; then
        echo -e "${GREEN}✓ $check_name passed${NC}"
    else
        echo -e "${RED}✗ $check_name failed${NC}"
        OVERALL_STATUS=1
    fi
}

# 1. Check if dependencies are installed
echo -e "${BLUE}Checking development dependencies...${NC}"
if ! python -c "import black, ruff, mypy" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Installing development dependencies...${NC}"
    pip install -e ".[dev]"
fi

# 2. Run Black formatting check
run_check "Black code formatting" "black --check --diff src/ tests/"

# 3. Run Ruff linting
run_check "Ruff linting" "ruff check src/ tests/"

# 4. Run mypy type checking (only on core modules for speed)
run_check "MyPy type checking" "mypy src/h2k_hpxml/core/ src/h2k_hpxml/config/ src/h2k_hpxml/utils/ src/h2k_hpxml/types.py"

# 5. Run basic tests to ensure functionality
run_check "Basic unit tests" "pytest tests/unit/ -v --tb=short"

# Final status report
echo ""
echo "============================================="
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}🎉 All quality checks passed!${NC}"
    echo ""
    echo "Your code meets the quality standards."
else
    echo -e "${RED}❌ Some quality checks failed.${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    echo ""
    echo "Quick fixes:"
    echo "  - Run 'black src/ tests/' to format code"
    echo "  - Run 'ruff check --fix src/ tests/' to fix linting issues"
    echo "  - Check mypy output for type issues"
fi

exit $OVERALL_STATUS
