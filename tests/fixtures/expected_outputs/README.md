# Expected Outputs Directory Structure

This directory contains organized test outputs for the H2K-HPXML regression testing framework.

## Directory Structure

```
tests/fixtures/expected_outputs/
├── golden_files/              # Golden master files for regression testing
│   ├── baseline/             # Reference outputs from stable code versions
│   │   ├── baseline_energy_summary.json       # Index of all baseline files
│   │   └── baseline_*.json                   # Individual baseline files per H2K simulation
│   └── comparison/           # Test results comparing current runs against baseline
│       ├── comparison_summary.json           # Index of all comparison results
│       └── comparison_*.json                 # Individual comparison reports per simulation
├── other_tests/              # Reserved for future test types
└── [simulation_outputs]/     # Individual H2K simulation run directories
    ├── run/                  # EnergyPlus simulation outputs
    │   ├── eplusout.sql      # SQLite database with energy results
    │   ├── eplusout.err      # Error log
    │   └── [other outputs]
    └── *.xml                 # HPXML file for the simulation
```

## File Types

### Golden Files (`golden_files/`)
- **Purpose**: Regression testing reference data
- **When Updated**: Only when intentional code changes are made and verified
- **Version Control**: These files should be committed to track approved changes

### Baseline Files (`golden_files/baseline/`)
- **Content**: Energy data extracted from stable code runs
- **Format**: JSON with hierarchical energy breakdown
- **Usage**: Reference point for detecting unintended changes

### Comparison Files (`golden_files/comparison/`)
- **Content**: Test results comparing current runs against baseline  
- **Format**: JSON with pass/fail status and detailed differences
- **Usage**: Identifying what changed and by how much
- **Version Control**: **Gitignored** - regenerated each test run

### Simulation Outputs
- **Content**: Complete EnergyPlus simulation results
- **Temporary**: Created during test runs, can be cleaned up
- **Key Files**: `eplusout.sql` (energy data), `eplusout.err` (errors)

## Usage

1. **Generate new golden files** (only when code is stable):
   ```bash
   python -m pytest tests/integration/test_generate_baseline.py -v -s --run-baseline
   ```

2. **Run regression tests** (compare against golden files):
   ```bash
   python -m pytest tests/integration/test_regression.py -v -s
   ```

3. **Full test suite**:
   ```bash
   python -m pytest tests/integration/ -v
   ```

## File Naming Convention

- `baseline_*.json`: Golden master files for each H2K simulation
- `comparison_*.json`: Test results for each simulation comparison
- `*_summary.json`: Index files providing overview of all results

## Maintenance

- **Golden files** should only be updated when intentional changes are verified
- **Comparison files** are regenerated each test run
- **Simulation outputs** can be cleaned up periodically to save space
- **other_tests/** directory is reserved for future expansion
