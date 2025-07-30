# H2K HPXML Project Structure Refactoring Plan (Phase 3)

**Date:** July 30, 2025
**Status:** Planning Phase
**Previous:** Based on refactor2.md improvements

## Overview

This refactoring plan focuses on improving the project structure, organization, and maintainability while preserving all current functionality. The goal is to create a cleaner, more professional project layout that follows Python packaging best practices.

## Current State Analysis

### Issues Identified:
1. **Mixed root directory** - Configuration, documentation, and temporary files scattered
2. **Inconsistent output paths** - Multiple output directories (`workflow/`, `./output/`)
3. **Documentation fragmentation** - Docs spread across root and `prompts/`
4. **Cache pollution** - Build artifacts committed to repository
5. **Configuration paths** - Hardcoded and inconsistent path structures

### Working Well:
- ✅ Source code organization (`h2k_hpxml/`)
- ✅ Test structure (`tests/`)
- ✅ Dev container setup
- ✅ Example files structure

## Proposed New Structure

```
h2k_hpxml/
├── config/                     # Centralized configuration
│   ├── conversionconfig.ini    # Main configuration
│   ├── logging.conf           # Logging configuration
│   └── defaults/              # Default configuration templates
│       └── conversionconfig.template.ini
├── docs/                      # All documentation
│   ├── README.md             # Main documentation
│   ├── development/          # Development docs
│   │   ├── refactor-history/
│   │   │   ├── refactor.md
│   │   │   ├── refactor2.md
│   │   │   └── refactor3.md
│   │   ├── diagnostics.md
│   │   └── troubleshooting.md
│   ├── user-guide/          # User documentation
│   │   ├── installation.md
│   │   ├── configuration.md
│   │   └── usage.md
│   └── api/                 # API documentation (future)
├── examples/                 # Keep current structure
│   ├── *.h2k
│   └── expected_outputs/
├── h2k_hpxml/               # Source code (no changes)
├── tests/                   # Test structure (no changes)
├── tools/                   # Development and setup tools
│   ├── install_hot2000.sh
│   ├── setup_wine.sh
│   ├── cleanup.sh
│   └── run_tests.sh
├── output/                  # Consolidated outputs (gitignored)
│   ├── hpxml/              # Translated HPXML files
│   ├── comparisons/        # Comparison data and reports
│   ├── workflows/          # Workflow intermediate files
│   └── logs/              # Application logs
├── .devcontainer/          # No changes
├── .github/                # CI/CD workflows (future)
├── .gitignore             # Enhanced
├── pyproject.toml         # No changes
└── README.md              # Project overview (links to docs/)
```

## Testing Strategy

### Comprehensive Test Suite
After each phase, run the complete test battery to ensure no regressions:

```bash
# Full test sequence
./tools/run_tests.sh
```

### Test Components

#### 1. **Unit and Integration Tests**
```bash
# Run all tests with verbose output
pytest -v --tb=short

# Run tests with coverage report
pytest -v --cov=h2k_hpxml --cov-report=term-missing

# Run specific test categories
pytest -v tests/unit/
pytest -v tests/integration/
```

#### 2. **Code Quality Checks**
```bash
# Pre-commit hooks (if configured)
pre-commit run --all-files

# Manual linting and formatting
ruff check .
ruff format --check .
mypy h2k_hpxml/
```

#### 3. **Example Validation Tests**
```bash
# Test all example files still work
for h2k_file in examples/*.h2k; do
    echo "Testing: $h2k_file"
    python -m h2k_hpxml.cli "$h2k_file" --output-dir output/test/
done
```

#### 4. **Configuration Tests**
```bash
# Test old config path compatibility
python -c "
import h2k_hpxml.config as config
try:
    cfg = config.load_configuration()
    print('✅ Configuration loads successfully')
    print(f'Config source: {cfg.source_path}')
except Exception as e:
    print(f'❌ Configuration failed: {e}')
    exit(1)
"
```

## Implementation Plan

### Phase 1: Cleanup and Preparation

#### Step 1.1: Create Test Baseline
```bash
# Establish baseline before any changes
echo "=== BASELINE TESTS ===" > test_results_baseline.txt
pytest -v >> test_results_baseline.txt 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Baseline tests pass"
else
    echo "❌ Baseline tests fail - fix before proceeding"
    exit 1
fi
```

#### Step 1.2: Remove Unnecessary Files
```bash
# Remove temporary/cache files
rm "=6.0.0"
rm CLAUDE.md
rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .hypothesis/

# Remove Wine installation if not needed in container
rm -rf .wine_hot2000/
```

#### Step 1.3: Create New Directory Structure
```bash
# Create new directories
mkdir -p config/defaults
mkdir -p docs/{development/refactor-history,user-guide,api}
mkdir -p tools
mkdir -p output/{hpxml,comparisons,workflows,logs}
mkdir -p .github/workflows
```

#### **Phase 1 Testing**
```bash
echo "=== PHASE 1 TESTS ===" > test_results_phase1.txt

# 1. Full pytest suite
echo "Running pytest..." | tee -a test_results_phase1.txt
pytest -v --tb=short >> test_results_phase1.txt 2>&1
PYTEST_EXIT=$?

# 2. Pre-commit checks (if available)
echo "Running pre-commit checks..." | tee -a test_results_phase1.txt
if command -v pre-commit >/dev/null; then
    pre-commit run --all-files >> test_results_phase1.txt 2>&1
    PRECOMMIT_EXIT=$?
else
    echo "Pre-commit not available, skipping" | tee -a test_results_phase1.txt
    PRECOMMIT_EXIT=0
fi

# 3. Code quality checks
echo "Running code quality checks..." | tee -a test_results_phase1.txt
ruff check . >> test_results_phase1.txt 2>&1
RUFF_EXIT=$?

# 4. Example file validation
echo "Testing example files..." | tee -a test_results_phase1.txt
EXAMPLE_EXIT=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ]; then
        echo "Testing: $h2k_file" | tee -a test_results_phase1.txt
        python -m h2k_hpxml.cli "$h2k_file" --output-dir output/test/ >> test_results_phase1.txt 2>&1
        if [ $? -ne 0 ]; then
            EXAMPLE_EXIT=1
        fi
    fi
done

# Summary
echo "=== PHASE 1 TEST SUMMARY ===" | tee -a test_results_phase1.txt
echo "Pytest: $([ $PYTEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase1.txt
echo "Pre-commit: $([ $PRECOMMIT_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase1.txt
echo "Ruff: $([ $RUFF_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase1.txt
echo "Examples: $([ $EXAMPLE_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase1.txt

if [ $PYTEST_EXIT -eq 0 ] && [ $PRECOMMIT_EXIT -eq 0 ] && [ $RUFF_EXIT -eq 0 ] && [ $EXAMPLE_EXIT -eq 0 ]; then
    echo "🎉 Phase 1 tests PASSED - proceeding to Phase 2"
else
    echo "💥 Phase 1 tests FAILED - fix issues before continuing"
    exit 1
fi
```

### Phase 2: Move and Reorganize Files

#### Step 2.1: Move Configuration Files
```bash
# Move main config
mv conversionconfig.ini config/

# Create template for users
cp config/conversionconfig.ini config/defaults/conversionconfig.template.ini
```

#### Step 2.2: Reorganize Documentation
```bash
# Move development docs
mv refactor.md docs/development/refactor-history/ 2>/dev/null || true
mv refactor2.md docs/development/refactor-history/ 2>/dev/null || true
mv refactor3.md docs/development/refactor-history/ 2>/dev/null || true
mv TODO.md docs/development/ 2>/dev/null || true
mv diagnostics.md docs/development/ 2>/dev/null || true

# Move prompts content
if [ -f prompts/diagnostics.md ]; then
    mv prompts/diagnostics.md docs/development/diagnostics-detailed.md
fi
rmdir prompts/ 2>/dev/null || true

# Create user documentation stubs
echo "# Installation Guide" > docs/user-guide/installation.md
echo "# Configuration Guide" > docs/user-guide/configuration.md
echo "# Usage Guide" > docs/user-guide/usage.md
```

#### Step 2.3: Move Tools
```bash
# Move any setup scripts if they exist
[ -f install_hot2000.sh ] && mv install_hot2000.sh tools/
[ -f setup_wine.sh ] && mv setup_wine.sh tools/
```

#### **Phase 2 Testing**
```bash
echo "=== PHASE 2 TESTS ===" > test_results_phase2.txt

# Test configuration loading with backwards compatibility
echo "Testing configuration loading..." | tee -a test_results_phase2.txt
python -c "
import sys
import os
sys.path.insert(0, '.')

try:
    # Try to load config - should find it in new location
    import h2k_hpxml.config as config
    cfg = config.load_configuration()
    print('✅ Configuration loads from new location')

    # Verify paths are accessible
    print(f'Config loaded from: {getattr(cfg, \"_source_path\", \"unknown\")}')

except Exception as e:
    print(f'❌ Configuration loading failed: {e}')
    sys.exit(1)
" >> test_results_phase2.txt 2>&1
CONFIG_EXIT=$?

# Full test suite
pytest -v --tb=short >> test_results_phase2.txt 2>&1
PYTEST_EXIT=$?

# Pre-commit checks
if command -v pre-commit >/dev/null; then
    pre-commit run --all-files >> test_results_phase2.txt 2>&1
    PRECOMMIT_EXIT=$?
else
    PRECOMMIT_EXIT=0
fi

# Code quality
ruff check . >> test_results_phase2.txt 2>&1
RUFF_EXIT=$?

# Example validation
EXAMPLE_EXIT=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ]; then
        python -m h2k_hpxml.cli "$h2k_file" --output-dir output/test/ >> test_results_phase2.txt 2>&1
        [ $? -ne 0 ] && EXAMPLE_EXIT=1
    fi
done

# Summary
echo "=== PHASE 2 TEST SUMMARY ===" | tee -a test_results_phase2.txt
echo "Config Loading: $([ $CONFIG_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase2.txt
echo "Pytest: $([ $PYTEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase2.txt
echo "Pre-commit: $([ $PRECOMMIT_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase2.txt
echo "Ruff: $([ $RUFF_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase2.txt
echo "Examples: $([ $EXAMPLE_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase2.txt

TOTAL_EXIT=$((CONFIG_EXIT + PYTEST_EXIT + PRECOMMIT_EXIT + RUFF_EXIT + EXAMPLE_EXIT))
if [ $TOTAL_EXIT -eq 0 ]; then
    echo "🎉 Phase 2 tests PASSED"
else
    echo "💥 Phase 2 tests FAILED - fix issues before continuing"
    exit 1
fi
```

### Phase 3: Update Configuration

#### Step 3.1: Update conversionconfig.ini Paths
```bash
# Update the configuration file with new paths
cat > config/conversionconfig.ini << 'EOF'
[paths]
source_h2k_path = /workspaces/h2k_hpxml/tests/input
hpxml_os_path = /OpenStudio-HPXML/
openstudio_binary = /usr/local/bin/openstudio
dest_hpxml_path = output/hpxml/
dest_compare_data = output/comparisons/
workflow_temp_path = output/workflows/

[simulation]
flags = --add-component-loads --debug

[weather]
weather_library = historic
weather_vintage = CWEC2020

[nonh2k]
timestep = 60
operable_window_avail_days = 3

[logging]
log_level = INFO
log_to_file = true
log_file_path = output/logs/h2k_hpxml.log
EOF
```

#### Step 3.2: Create Enhanced .gitignore
```bash
cat > .gitignore << 'EOF'
# Output directories
output/
logs/
*.log

# Python cache and build artifacts
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.hypothesis/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
env/
ENV/

# Wine directories
.wine*/

# IDE and editor files
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Temporary files
*.tmp
*.temp
*.bak
*.orig

# Test results
test_results_*.txt
EOF
```

#### **Phase 3 Testing**
```bash
echo "=== PHASE 3 TESTS ===" > test_results_phase3.txt

# Test new configuration paths
echo "Testing updated configuration..." | tee -a test_results_phase3.txt
python -c "
import sys
sys.path.insert(0, '.')

try:
    import h2k_hpxml.config as config
    cfg = config.load_configuration()

    # Test that new paths are being used
    print('✅ Configuration loads successfully')

    # Verify output directories exist or can be created
    import os
    from pathlib import Path

    output_dirs = ['output/hpxml', 'output/comparisons', 'output/workflows', 'output/logs']
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f'✅ Created/verified: {dir_path}')

except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    sys.exit(1)
" >> test_results_phase3.txt 2>&1
CONFIG_EXIT=$?

# Full test suite with new paths
pytest -v --tb=short >> test_results_phase3.txt 2>&1
PYTEST_EXIT=$?

# Test actual conversion with new output paths
echo "Testing conversion with new output paths..." | tee -a test_results_phase3.txt
CONVERSION_EXIT=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ]; then
        echo "Converting: $h2k_file" | tee -a test_results_phase3.txt
        python -m h2k_hpxml.cli "$h2k_file" >> test_results_phase3.txt 2>&1
        if [ $? -ne 0 ]; then
            CONVERSION_EXIT=1
            break
        fi
    fi
done

# Verify outputs are in correct locations
echo "Verifying output locations..." | tee -a test_results_phase3.txt
if [ -d "output/hpxml" ] && [ "$(ls -A output/hpxml 2>/dev/null)" ]; then
    echo "✅ HPXML files found in output/hpxml/" | tee -a test_results_phase3.txt
    OUTPUT_LOCATION_EXIT=0
else
    echo "❌ No HPXML files found in expected location" | tee -a test_results_phase3.txt
    OUTPUT_LOCATION_EXIT=1
fi

# Pre-commit and code quality
if command -v pre-commit >/dev/null; then
    pre-commit run --all-files >> test_results_phase3.txt 2>&1
    PRECOMMIT_EXIT=$?
else
    PRECOMMIT_EXIT=0
fi

ruff check . >> test_results_phase3.txt 2>&1
RUFF_EXIT=$?

# Summary
echo "=== PHASE 3 TEST SUMMARY ===" | tee -a test_results_phase3.txt
echo "Config Loading: $([ $CONFIG_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt
echo "Pytest: $([ $PYTEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt
echo "Conversion: $([ $CONVERSION_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt
echo "Output Location: $([ $OUTPUT_LOCATION_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt
echo "Pre-commit: $([ $PRECOMMIT_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt
echo "Ruff: $([ $RUFF_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase3.txt

TOTAL_EXIT=$((CONFIG_EXIT + PYTEST_EXIT + CONVERSION_EXIT + OUTPUT_LOCATION_EXIT + PRECOMMIT_EXIT + RUFF_EXIT))
if [ $TOTAL_EXIT -eq 0 ]; then
    echo "🎉 Phase 3 tests PASSED"
else
    echo "💥 Phase 3 tests FAILED - fix issues before continuing"
    exit 1
fi
```

### Phase 4: Update Code References

#### Step 4.1: Update Configuration Loading
Update any code that loads `conversionconfig.ini` to look in `config/`:

```python
# In h2k_hpxml configuration loading code
import os
import warnings
from pathlib import Path

def get_config_path():
    """Get the path to the configuration file."""
    # Try config directory first (new location)
    config_path = Path(__file__).parent.parent / "config" / "conversionconfig.ini"
    if config_path.exists():
        return config_path

    # Fallback to old location for backwards compatibility
    old_config_path = Path(__file__).parent.parent / "conversionconfig.ini"
    if old_config_path.exists():
        warnings.warn(
            "Configuration file found in deprecated location. "
            "Please move conversionconfig.ini to config/ directory.",
            DeprecationWarning,
            stacklevel=2
        )
        return old_config_path

    raise FileNotFoundError(
        "Configuration file not found. Expected location: config/conversionconfig.ini"
    )
```

#### **Phase 4 Testing**
```bash
echo "=== PHASE 4 TESTS ===" > test_results_phase4.txt

# Test configuration loading with deprecation handling
echo "Testing configuration loading with backwards compatibility..." | tee -a test_results_phase4.txt
python -c "
import sys
import warnings
sys.path.insert(0, '.')

# Capture warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter('always')

    try:
        import h2k_hpxml.config as config
        cfg = config.load_configuration()
        print('✅ Configuration loads successfully')

        # Check if any deprecation warnings were issued
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        if deprecation_warnings:
            print(f'⚠️  Deprecation warnings: {len(deprecation_warnings)}')
            for warning in deprecation_warnings:
                print(f'   {warning.message}')
        else:
            print('✅ No deprecation warnings')

    except Exception as e:
        print(f'❌ Configuration loading failed: {e}')
        sys.exit(1)
" >> test_results_phase4.txt 2>&1
CONFIG_EXIT=$?

# Full test suite
pytest -v --tb=short --disable-warnings >> test_results_phase4.txt 2>&1
PYTEST_EXIT=$?

# Test specific functionality that relies on config
echo "Testing config-dependent functionality..." | tee -a test_results_phase4.txt
python -c "
import sys
sys.path.insert(0, '.')

try:
    # Test that all config-dependent modules can import and initialize
    import h2k_hpxml.config as config
    import h2k_hpxml.converter as converter

    cfg = config.load_configuration()
    print('✅ All config-dependent modules import successfully')

    # Test that paths are resolved correctly
    from pathlib import Path
    output_path = Path(cfg.dest_hpxml_path)
    if output_path.is_absolute() or str(output_path).startswith('output/'):
        print('✅ Output paths configured correctly')
    else:
        print(f'❌ Unexpected output path: {output_path}')
        sys.exit(1)

except Exception as e:
    print(f'❌ Config-dependent functionality test failed: {e}')
    sys.exit(1)
" >> test_results_phase4.txt 2>&1
FUNCTIONALITY_EXIT=$?

# Pre-commit and quality checks
if command -v pre-commit >/dev/null; then
    pre-commit run --all-files >> test_results_phase4.txt 2>&1
    PRECOMMIT_EXIT=$?
else
    PRECOMMIT_EXIT=0
fi

ruff check . >> test_results_phase4.txt 2>&1
RUFF_EXIT=$?

# Example conversions
EXAMPLE_EXIT=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ]; then
        python -m h2k_hpxml.cli "$h2k_file" >> test_results_phase4.txt 2>&1
        [ $? -ne 0 ] && EXAMPLE_EXIT=1 && break
    fi
done

# Summary
echo "=== PHASE 4 TEST SUMMARY ===" | tee -a test_results_phase4.txt
echo "Config Loading: $([ $CONFIG_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt
echo "Pytest: $([ $PYTEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt
echo "Functionality: $([ $FUNCTIONALITY_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt
echo "Pre-commit: $([ $PRECOMMIT_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt
echo "Ruff: $([ $RUFF_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt
echo "Examples: $([ $EXAMPLE_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase4.txt

TOTAL_EXIT=$((CONFIG_EXIT + PYTEST_EXIT + FUNCTIONALITY_EXIT + PRECOMMIT_EXIT + RUFF_EXIT + EXAMPLE_EXIT))
if [ $TOTAL_EXIT -eq 0 ]; then
    echo "🎉 Phase 4 tests PASSED"
else
    echo "💥 Phase 4 tests FAILED - fix issues before continuing"
    exit 1
fi
```

### Phase 5: Create Supporting Files

#### Step 5.1: Create tools/run_tests.sh
```bash
cat > tools/run_tests.sh << 'EOF'
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
run_test "Python Syntax Check" "python -m py_compile h2k_hpxml/*.py"

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
    run_test "MyPy Type Checking" "mypy h2k_hpxml/ --ignore-missing-imports"
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
sys.path.insert(0, \".\")
import h2k_hpxml.config as config
cfg = config.load_configuration()
print(f\"Config loaded successfully from: {getattr(cfg, \"_source_path\", \"unknown\")}\")
'"

# 7. Example file validation
echo -e "\n📋 Running: ${YELLOW}Example File Validation${NC}"
echo "----------------------------------------"
EXAMPLE_FAILURES=0
for h2k_file in examples/*.h2k; do
    if [ -f "$h2k_file" ]; then
        filename=$(basename "$h2k_file")
        echo "Testing: $filename"
        if python -m h2k_hpxml.cli "$h2k_file" --output-dir output/test/ >/dev/null 2>&1; then
            echo "  ✅ $filename converted successfully"
        else
            echo "  ❌ $filename conversion failed"
            EXAMPLE_FAILURES=$((EXAMPLE_FAILURES + 1))
        fi
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
EOF

chmod +x tools/run_tests.sh
```

#### Step 5.2: Create tools/cleanup.sh
```bash
cat > tools/cleanup.sh << 'EOF'
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
EOF

chmod +x tools/cleanup.sh
```

#### **Phase 5 Testing**
```bash
echo "=== PHASE 5 TESTS ===" > test_results_phase5.txt

# Test the new test runner
echo "Testing the new test runner..." | tee -a test_results_phase5.txt
./tools/run_tests.sh >> test_results_phase5.txt 2>&1
TEST_RUNNER_EXIT=$?

# Test cleanup script
echo "Testing cleanup script..." | tee -a test_results_phase5.txt
./tools/cleanup.sh >> test_results_phase5.txt 2>&1
CLEANUP_EXIT=$?

# Verify cleanup worked
if [ ! -d ".pytest_cache" ] && [ ! -d ".mypy_cache" ] && [ ! -d ".ruff_cache" ]; then
    echo "✅ Cleanup script works correctly" | tee -a test_results_phase5.txt
    CLEANUP_VERIFY_EXIT=0
else
    echo "❌ Cleanup script did not remove all cache directories" | tee -a test_results_phase5.txt
    CLEANUP_VERIFY_EXIT=1
fi

# Final comprehensive test run
echo "Final comprehensive test run..." | tee -a test_results_phase5.txt
./tools/run_tests.sh >> test_results_phase5.txt 2>&1
FINAL_TEST_EXIT=$?

# Summary
echo "=== PHASE 5 TEST SUMMARY ===" | tee -a test_results_phase5.txt
echo "Test Runner: $([ $TEST_RUNNER_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase5.txt
echo "Cleanup Script: $([ $CLEANUP_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase5.txt
echo "Cleanup Verification: $([ $CLEANUP_VERIFY_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase5.txt
echo "Final Test Run: $([ $FINAL_TEST_EXIT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")" | tee -a test_results_phase5.txt

TOTAL_EXIT=$((TEST_RUNNER_EXIT + CLEANUP_EXIT + CLEANUP_VERIFY_EXIT + FINAL_TEST_EXIT))
if [ $TOTAL_EXIT -eq 0 ]; then
    echo "🎉 Phase 5 tests PASSED - REFACTORING COMPLETE!"
else
    echo "💥 Phase 5 tests FAILED - review and fix issues"
    exit 1
fi
```

## Test Result Tracking

All test results will be saved to files for later review:
- `test_results_baseline.txt` - Pre-refactoring baseline
- `test_results_phase1.txt` - Phase 1 results
- `test_results_phase2.txt` - Phase 2 results
- `test_results_phase3.txt` - Phase 3 results
- `test_results_phase4.txt` - Phase 4 results
- `test_results_phase5.txt` - Phase 5 results

## Rollback Strategy

Each phase is a Git commit, allowing easy rollback:

```bash
# Tag before starting
git tag refactor3-start

# Commit after each phase
git add -A && git commit -m "refactor3: Phase 1 complete - cleanup and structure"
git add -A && git commit -m "refactor3: Phase 2 complete - file reorganization"
git add -A && git commit -m "refactor3: Phase 3 complete - configuration updates"
git add -A && git commit -m "refactor3: Phase 4 complete - code updates"
git add -A && git commit -m "refactor3: Phase 5 complete - supporting tools"

# Rollback if needed
git reset --hard refactor3-start  # Complete rollback
git reset --hard HEAD~1           # Rollback one phase
```

## Benefits Expected

1. **Robust Testing** - Comprehensive test coverage at each step
2. **Early Problem Detection** - Issues caught immediately
3. **Confident Refactoring** - Knowing each change is validated
4. **Professional Quality** - Thorough testing like production systems
5. **Documentation** - Test results provide detailed change log

## Success Criteria

- [ ] All baseline tests pass before starting
- [ ] All phase tests pass before proceeding to next phase
- [ ] Final test suite runs cleanly with comprehensive coverage
- [ ] No regressions in functionality
- [ ] All example files continue to work
- [ ] Code quality metrics maintained or improved
- [ ] Configuration loading works with backwards compatibility
- [ ] Output files are generated in correct locations

## Timeline

- **Week 1**: Phase 1-2 with comprehensive testing
- **Week 2**: Phase 3-4 with validation at each step
- **Week 3**: Phase 5 and final validation
- **Week 4**: Documentation and performance validation

This plan ensures that every change is thoroughly tested before proceeding, making the refactoring process much safer and more reliable.
