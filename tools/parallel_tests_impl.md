# Regression Test Parallelization Implementation Plan

## Overview
Parallelize the regression tests to improve execution speed by running each H2K file test independently across multiple CPU cores.

## Current State Analysis
- **Test Structure**: Single monolithic test function processing 7 H2K files sequentially
- **Test Independence**: Each H2K file is processed completely independently
- **Performance Bottleneck**: Sequential execution of compute-intensive simulations

## ✅ IMPLEMENTATION COMPLETED

All phases have been successfully implemented:

## Implementation Plan

### ✅ Phase 1: Add pytest-xdist Dependency
1. ✅ Updated `pyproject.toml` to include `pytest-xdist>=3.0.0` in dev dependencies
2. ✅ This enables the `-n` flag for parallel test execution

### ✅ Phase 2: Refactor test_regression.py
1. ✅ Created `get_h2k_test_files()` helper function to extract test files from baseline summary
2. ✅ Used `@pytest.mark.parametrize` to create individual test cases per H2K file
3. ✅ Created `test_regression_parallel()` function with extracted logic from original loop
4. ✅ Added proper test isolation with unique temp directories using UUID
5. ✅ Created helper functions `_test_energy_validation()` and `_test_hpxml_validation()` 
6. ✅ Maintained backward compatibility with `test_regression_sequential()` (marked as deprecated)

### ✅ Phase 3: Update Test Utilities
1. ✅ Ensured thread-safe file operations (each test uses unique base_name for files)
2. ✅ Implemented unique temp directories per test using `uuid.uuid4()` to avoid conflicts
3. ✅ Maintained backward compatibility for sequential execution

### ✅ Phase 4: Update Documentation and Tools
1. ✅ Added `--parallel` flag support for parallel test execution (now use `pytest -n auto`)
2. ✅ Added parallel testing documentation to `CLAUDE.md` with usage examples
3. ✅ Updated `tools/README.md` with parallel testing section and performance benefits

## Benefits
- **Performance**: ~3-7x speedup depending on CPU cores
- **Better Isolation**: Each test runs in separate process
- **Clearer Reporting**: Individual test results per H2K file
- **Backward Compatible**: Can still run sequentially when needed

## Usage After Implementation
```bash
# Run tests in parallel (auto-detect cores)
pytest tests/integration/test_regression.py -n auto

# Run with specific number of workers
pytest tests/integration/test_regression.py -n 4

# Run sequentially (as before)
pytest tests/integration/test_regression.py
```

## Adding New Tests Remains Simple
1. Add H2K file to `examples/` folder
2. Run `python tools/generate_baseline_data.py` 
3. Tests automatically include the new file

No changes to the workflow for adding new test files!