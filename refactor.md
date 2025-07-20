# H2K-HPXML Refactoring Plan

## Overview
Refactoring the H2K-HPXML project to follow modern Python packaging best practices with proper src/ layout, pyproject.toml configuration, and improved project structure.

## Current Issues
- No `pyproject.toml` or `setup.py` - not properly packaged
- Main package `h2ktohpxml` at root level (flat layout)
- CLI scripts in `bin/` with manual path manipulation
- Analysis tools and config files scattered at root
- No proper package metadata or dependencies management

## Target Structure
```
h2k_hpxml/
├── pyproject.toml              # Modern packaging configuration
├── README.md
├── LICENSE
├── CHANGELOG.md
├── src/
│   └── h2k_hpxml/             # Main package (renamed from h2ktohpxml)
│       ├── __init__.py
│       ├── __main__.py        # For python -m h2k_hpxml
│       ├── cli/               # CLI commands
│       │   ├── __init__.py
│       │   ├── main.py        # Main CLI entry point
│       │   ├── convert.py     # h2k2hpxml functionality  
│       │   └── resilience.py  # Resilience analysis
│       ├── core/              # Core translation engine
│       │   ├── __init__.py
│       │   ├── translator.py  # Main h2ktohpxml logic
│       │   └── model.py       # Model handling
│       ├── components/        # Building components
│       │   ├── __init__.py
│       │   ├── enclosure/     # Building envelope
│       │   ├── systems/       # HVAC systems
│       │   ├── baseloads/     # Loads and appliances
│       │   └── program_mode/  # Special modes
│       ├── analysis/          # Analysis tools
│       │   ├── __init__.py
│       │   └── annual.py
│       ├── utils/             # Utilities
│       │   ├── __init__.py
│       │   ├── weather.py
│       │   ├── units.py
│       │   └── h2k.py
│       ├── resources/         # Static resources
│       │   ├── config/        # JSON configs
│       │   ├── templates/     # HPXML templates
│       │   └── weather/       # Weather data
│       └── workflows/         # Simulation workflows
│           ├── __init__.py
│           └── runner.py      # OpenStudio workflow
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── utils/
├── docs/
├── examples/
└── scripts/                   # Development/maintenance scripts
    ├── clean_test_data.py
    └── compare.py
```

## Refactoring Plan

### Phase 1: Setup Modern Packaging
- [ ] Create `pyproject.toml` with project metadata and dependencies
- [ ] Create `src/` directory structure
- [ ] Move `h2ktohpxml/` → `src/h2k_hpxml/core/` (keeping internal structure identical)
- [ ] Update basic imports to use new package name

### Phase 2: CLI Restructuring (Priority: Validate before module reorganization)
- [ ] Create `src/h2k_hpxml/cli/` module structure
- [ ] Convert `bin/h2k2hpxml.py` to proper CLI module
- [ ] Convert `bin/resilience.py` to proper CLI module  
- [ ] Add CLI entry points in `pyproject.toml`
- [ ] Test CLI functionality and golden file generation
- [ ] Verify tests produce same results as current implementation

### Phase 3: Component Reorganization
- [ ] Move building components to logical groupings:
  - `enclosure/`, `systems/`, `baseloads/` → `src/h2k_hpxml/components/`
  - `utils/` → `src/h2k_hpxml/utils/`
  - `config/`, `templates/` → `src/h2k_hpxml/resources/`
- [ ] Update internal imports within reorganized modules

### Phase 4: Analysis & Workflows
- [ ] Move `analysis/` → `src/h2k_hpxml/analysis/`
- [ ] Create `src/h2k_hpxml/workflows/` for simulation logic from `main.py` and `run.py`
- [ ] Move root scripts (`clean_test_data.py`, `compare.py`) to `scripts/` directory

### Phase 5: Final Updates
- [ ] Update all import statements throughout codebase
- [ ] Update configuration file paths
- [ ] Update test imports and fixtures
- [ ] Update CLAUDE.md documentation
- [ ] Update README.md with new structure and installation instructions

## Changes Made

### 2025-07-20 - Pre-Refactoring Baseline
- Created refactor.md to track progress
- Ran tests to establish baseline: **3 passed, 1 skipped** ✅

### Phase 1 Progress - COMPLETED ✅
- [x] Created pyproject.toml with modern packaging configuration
- [x] Created src/h2k_hpxml/ directory structure  
- [x] Moved h2ktohpxml/ → src/h2k_hpxml/core/ (keeping internal structure identical)
- [x] Copied analysis/ → src/h2k_hpxml/analysis/
- [x] Created main package __init__.py with backward compatibility
- [x] Tested: **3 passed, 1 skipped** ✅ (same results as baseline)

### Phase 2 Progress - COMPLETED ✅
- [x] Created src/h2k_hpxml/cli/ module structure
- [x] Converted bin/h2k2hpxml.py → src/h2k_hpxml/cli/convert.py with proper entry points
- [x] Converted bin/resilience.py → src/h2k_hpxml/cli/resilience.py with proper entry points
- [x] Created __main__.py for python -m h2k_hpxml support
- [x] Fixed config file path resolution in weather.py
- [x] CLI entry points configured in pyproject.toml (h2k2hpxml, h2k-resilience)
- [x] Updated tests to use new CLI: `python -m h2k_hpxml.cli.convert` instead of `bin/h2k2hpxml.py`
- [x] Tested CLI functionality: `python -m h2k_hpxml.cli.convert --help` works ✅
- [x] Removed deprecated bin/ directory ✅
- [x] Moved main.py, run.py → src/h2k_hpxml/workflows/
- [x] Moved clean_test_data.py, compare.py → scripts/
- [x] Tested: **3 passed, 1 skipped** ✅ (same results as baseline)

## Notes
- Prioritizing CLI restructuring (Phase 2) before component reorganization (Phase 3) to ensure test infrastructure works correctly
- Golden file generation must produce identical results before proceeding with module reorganization
- Using src/ layout for better testing practices and modern Python packaging standards