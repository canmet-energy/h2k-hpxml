# Repository Guidelines

## Project Structure & Module Organization
- `src/h2k_hpxml/` holds the translators, CLI entry points, and shared resources; mirror new domains within existing subpackages.
- `tests/` mirrors the package layout with `unit/`, `integration/`, and reusable `fixtures/` for regression data and expected HPXML files.
- Supporting assets live in `docs/`, `examples/`, `scripts/`, `tools/`, and `config/`; keep generated runs under `output/` or `h2k_demo_output/`.

## Build, Test, and Development Commands
- `uv pip install -e '.[dev]'` inside an activated virtual environment installs development extras and exposes the `h2k-*` scripts.
- `h2k-deps --setup --auto-install` fetches OpenStudio/HPXML toolchain dependencies and patches PATHs before running translators or tests.
- `pytest`, `pytest tests/unit/`, and `pytest tests/integration/` drive checks; add `--run-baseline` only when intentionally updating golden data.
- `ruff check src/ tests/`, `black src/ tests/`, and `mypy src/h2k_hpxml/core/` keep style, formatting, and typing regressions in check.

## Coding Style & Naming Conventions
- Target Python 3.12 with 4-space indentation, snake_case for modules/functions, PascalCase for classes, and UPPER_CASE constants; align new CLI names with `h2k_hpxml.cli`.
- Black enforces 100-character lines; prefer formatter-driven wrapping and avoid manual stylistic deviations without justification.
- Ruff enforces pycodestyle, pyupgrade, bugbear, and import-order rules; keep ignores local, documented, and update resource filenames in lowercase under `h2k_hpxml/resources`.

## Testing Guidelines
- Pytest configuration lives in `pyproject.toml`; discover tests via `test_*.py` modules, `Test*` classes, and `test_*` functions.
- Apply markers such as `integration`, `regression`, `resilience`, `baseline`, `slow`, `windows`, `linux`, and `cross_platform` to control execution matrices.
- Place new fixtures or baselines under `tests/fixtures`; check regenerated references into version control with a short rationale in the PR.

## Commit & Pull Request Guidelines
- Prefer concise Conventional Commit prefixes (`feat:`, `fix:`, `chore:`) as seen in recent history, adding scope where it clarifies intent.
- Reference issues, summarize behavioral changes, and list validation commands in PR descriptions; call out baseline or resource updates explicitly.
- Attach representative CLI output or screenshots for workflow-impacting changes and update relevant docs alongside code adjustments.

## Agent & Automation Notes
- Review `CLAUDE.md` for repository architecture, command catalogs, and troubleshooting playbooks tailored to assistants.
- Reuse patterns from `tools/cleanup.py` for automation scripts and avoid mutating archetype or weather sources; stage generated artifacts under `output/`.
