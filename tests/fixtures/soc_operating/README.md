# SOC operating-condition parity fixtures

Curated H2K files and H2K reference values used to verify that translated HPXML models
produce **baseload electricity** and **hot water volume** close to H2K SOC results after
OpenStudio-HPXML simulation.

H2K and HPXML will not match exactly; tolerances are stored in `expectations.json`.

## Contents

- `h2k/` — SOC test house and MURB files (house, attached, mobile, single-MURB, 2- and 4-unit whole-MURB)
- `expectations.json` — H2K reference values and default max relative errors per metric

## Running parity tests

Requires OpenStudio CLI and OpenStudio-HPXML (same as regression tests). **Not run by default.**

```bash
pytest tests/integration/test_operating_parity.py --run-operating-parity -v
```

Run after major changes to operating conditions, baseload appliances, or hot water logic.

## Updating expectations

When operating-condition logic is intentionally changed and verified:

1. Run `tools/compare.py` against the fixture folder (or re-run parity tests and inspect output).
2. Update `expectations.json` reference values (`*_h2k` fields) if H2K inputs changed.
3. Adjust `default_max_rel_error` only if the acceptable H2K↔HPXML gap has changed.

Current default tolerances (relative error vs H2K reference):

| Metric | Max rel. error |
|--------|----------------|
| `hot_water_usage_Lperday` | 0.5% |
| `baseloads_elec_GJ` | 2% |
