# Refactor differences

## Background
The refactor branch made lots of changes that are being considered to be merged into the main branch. However, when we did a large analysis of the files in the /workspaces/h2k-hpxml/housing-archetypes/data/h2k_files/existing-stock/sd_sa folder, we have noticed differences in the outputs. In particular, the files that are in failure status. The results from the main branch are in this folder /workspaces/h2k-hpxml/housing-archetypes/data/h2k_files/existing-stock/sd_sa/output_old. The results from the current refactor branch are in this folder /workspaces/h2k-hpxml/housing-archetypes/data/h2k_files/existing-stock/sd_sa/output_new.

## Analysis Summary

- **Total failures in main branch:** 392
- **Total failures in refactor branch:** 404
- **Net change:** +12 failures
- **Files with different errors between branches:** 3
- **Persistent failures (same in both branches):** 389

## NEW failures in refactor (12 files)

These files passed in main but fail in refactor:

1. ERS-EX-21334.H2K
2. ERS-EX-21335.H2K
3. ERS-EX-21342.H2K
4. ERS-EX-21351.H2K
5. ERS-EX-21433.H2K
6. ERS-EX-21438.H2K
7. ERS-EX-21440.H2K
8. ERS-EX-21441.H2K
9. ERS-EX-25447.H2K
10. ERS-EX-27378.H2K
11. ERS-EX-53795.H2K
12. ERS-EX-64453.H2K

**Common error:** `'NoneType' object has no attribute 'get'` in systems processing

## Files with DIFFERENT errors between branches (3 files)

These files fail in both branches but with different error messages:

### 1. ERS-EX-21337.H2K
- **Main error:** `Element 'CoolingSensibleHeatFraction': The value '0' must be greater than '0.5'`
- **Refactor error:** `'NoneType' object has no attribute 'get'` in systems processing

### 2. ERS-EX-3088.H2K
- **Main error:** `Warning: No space cooling specified, the model will not include space cooling energy use`
- **Refactor error:** `'NoneType' object has no attribute 'get'` in systems processing

### 3. ERS-EX-4662.H2K
- **Main error:** `Warning: No space cooling specified, the model will not include space cooling energy use`
- **Refactor error:** `'NoneType' object has no attribute 'get'` in systems processing
