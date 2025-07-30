#!/bin/bash
# Quality fix script for H2K-HPXML project
# Automatically fix code quality issues where possible

set -e

echo "🔧 Running H2K-HPXML Code Quality Fixes..."
echo "==========================================="

# Change to project root
cd "$(dirname "$0")/.."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a fix and report status
run_fix() {
    local fix_name="$1"
    local command="$2"

    echo ""
    echo -e "${BLUE}Running $fix_name...${NC}"
    echo "----------------------------------------"

    if eval "$command"; then
        echo -e "${GREEN}✓ $fix_name completed${NC}"
    else
        echo -e "${YELLOW}⚠ $fix_name had issues (check output above)${NC}"
    fi
}

# 1. Check if dependencies are installed
echo -e "${BLUE}Checking development dependencies...${NC}"
if ! python -c "import black, ruff" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Installing development dependencies...${NC}"
    pip install -e ".[dev]"
fi

# 2. Run Black formatting (fixes automatically)
run_fix "Black code formatting" "black src/ tests/"

# 3. Run Ruff with auto-fix
run_fix "Ruff linting with auto-fix" "ruff check --fix src/ tests/"

# 4. Run import sorting with ruff
run_fix "Import sorting" "ruff check --select I --fix src/ tests/"

echo ""
echo "==========================================="
echo -e "${GREEN}🎉 Automated fixes completed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the changes made by the formatters"
echo "  2. Run './scripts/quality_check.sh' to verify all issues are resolved"
echo "  3. Address any remaining type checking or complex linting issues manually"
echo "  4. Commit your changes"
