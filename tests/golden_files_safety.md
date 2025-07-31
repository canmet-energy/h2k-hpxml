# Golden Files Safety System

## Overview

This document describes the comprehensive safety system implemented to protect golden baseline files from accidental overwriting during testing.

## Problem

Golden files contain reference data used for regression testing. Accidentally running baseline generation tests could overwrite these critical files, leading to loss of historical test data.

## Safety Mechanisms Implemented

### 1. Pytest Markers
- Baseline generation tests are marked with `@pytest.mark.baseline_generation`
- This provides clear identification of potentially destructive tests

### 2. Custom Command Line Flag
- Added `--run-baseline` flag to pytest configuration
- Baseline generation tests only run when this flag is explicitly provided
- Default behavior: baseline generation tests are skipped

### 3. Automatic Test Skipping
- Without `--run-baseline` flag, baseline tests show: `SKIPPED (Need --run-baseline flag to run baseline generation)`
- This ensures accidental `pytest` runs don't modify golden files

### 4. Interactive User Confirmation
- When baseline generation tests run, they require user confirmation
- Users must type 'yes' to proceed with potentially destructive operations
- Provides a final safety check before modifying golden files

### 5. Automatic Backups
- Before generating new baselines, the system creates timestamped backups
- Backup location: `tests/fixtures/expected_outputs/golden_files/backup_YYYYMMDD_HHMMSS/`
- Allows recovery if something goes wrong

### 6. Directory Organization
- Golden files are stored in dedicated `golden_files/` directory structure:
  - `golden_files/baseline/` - Reference baseline files
  - `golden_files/comparison/` - Current test run results
  - `golden_files/backup_*/` - Timestamped backups

## Usage

### Normal Testing (Safe)
```bash
# This will skip baseline generation and use existing golden files
pytest tests/
pytest tests/integration/test_regression.py
```

### Baseline Generation (Protected)
```bash
# This will prompt for confirmation and create backups
pytest tests/integration/test_generate_baseline.py --run-baseline
```

### Verification
```bash
# Check that golden files exist and are valid
pytest tests/unit/test_validate_eplusout_sql.py
```

## File Structure

```
tests/fixtures/expected_outputs/golden_files/
├── baseline/                    # Protected golden baseline files
│   ├── baseline_energy_summary.json
│   ├── baseline_WizardHouse.json
│   ├── baseline_WizardHouse_0.13.json
│   └── ...
├── comparison/                  # Current test run results
│   ├── comparison_energy_summary.json
│   ├── comparison_WizardHouse.json
│   └── ...
└── backup_20250715_155240/     # Timestamped backups
    ├── baseline_energy_summary.json
    └── ...
```

## Safety Features Summary

1. **Multi-layer Protection**: Multiple safety mechanisms work together
2. **Explicit Intent**: Users must explicitly request baseline generation
3. **User Confirmation**: Interactive prompts prevent accidents
4. **Automatic Backups**: Data loss prevention
5. **Clear Documentation**: This document and inline comments
6. **Test Validation**: Unit tests verify golden file integrity

## Best Practices

1. **Never run baseline generation casually** - Only when intentionally updating test references
2. **Verify changes** - Review what changed in golden files before committing
3. **Backup verification** - Check that backups were created successfully
4. **Team coordination** - Communicate baseline updates to team members
5. **Version control** - Commit golden file changes with clear messages

## Recovery

If golden files are accidentally modified:

1. **Check for backups**: Look in `golden_files/backup_*/` directories
2. **Use git history**: `git checkout HEAD -- tests/fixtures/expected_outputs/golden_files/`
3. **Regenerate if needed**: Run baseline generation with proper safety protocols

## Technical Implementation

- **conftest.py**: Pytest configuration for flags and markers
- **test_generate_baseline.py**: Protected baseline generation with confirmations and backups
- **test_energy_comparison.py**: Uses golden files for regression testing
- **test_validate_eplusout_sql.py**: Validates golden file integrity

This safety system ensures that golden files are protected while maintaining the ability to update them when necessary for legitimate testing needs.
