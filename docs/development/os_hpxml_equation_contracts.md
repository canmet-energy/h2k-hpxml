# OS-HPXML equation contracts

Several H2K-HPXML modules mirror numeric logic from the installed
OpenStudio-HPXML workflow (Ruby sources under `HPXMLtoOpenStudio/resources/`).
When NREL releases a new OS-HPXML version, those literals or formulas may change.

## How drift is detected

Contract verification lives in **pytest**, not in `os-setup`:

| Layer | Role |
|-------|------|
| [`os_hpxml_equation_contract.json`](../../src/h2k_hpxml/resources/os_hpxml_equation_contract.json) | Pinned constants + Python oracle vectors for v1.12.0 |
| [`equation_contract.py`](../../src/h2k_hpxml/utils/dependencies/equation_contract.py) | Scans OS Ruby sources and runs oracles |
| [`test_equation_contract.py`](../../tests/unit/test_equation_contract.py) | Unit tests (mock install) + integration test (real install) |

Run after bumping OS-HPXML or changing mirrored Python:

```bash
pytest tests/unit/test_equation_contract.py -v
pytest tests/unit/test_equation_contract.py -m equation_contract -v
```

The integration test skips automatically when OpenStudio-HPXML is not installed.

`os-setup --check-only` still confirms binaries exist; equation parity is validated explicitly.

## Upgrading OpenStudio-HPXML

1. Install the target release and update [`dependency_versions.json`](../../src/h2k_hpxml/resources/dependency_versions.json) and `pyproject.toml`.
2. Run `pytest tests/unit/test_equation_contract.py -m equation_contract -v`.
3. Diff the Ruby files listed in the contract manifest against the prior release.
4. Update Python mirrors (`hot_water_usage.py`, `baseload_appliances.py`, `epw_mains_temperature.py`, etc.).
5. Update `os_hpxml_equation_contract.json` constants and oracle expected values.
6. Re-run the full test suite.

## Covered contracts (v1.12.0)

- Operational fixture and distribution waste gpd (`hotwater_appliances.rb`)
- Clothes washer / dishwasher label coefficients (`hotwater_appliances.rb`)
- Mains inlet temperature algorithm (`weather.rb`)
- RECS equivalent-bedroom regressions (`defaults.rb`)

Dryer/range inverse and pipe-length ratio are deferred until those paths are fully wired.
