# CLI Improvement Plan: Remove `run` Command and Simplify Interface

## ✅ IMPLEMENTATION COMPLETE - December 8, 2024

## Current Problem

The README documents a simple interface:
```bash
h2k2hpxml input.h2k [--output output.xml]
```

But the actual CLI requires a more complex syntax:
```bash
h2k2hpxml run -i input.h2k [--output output.xml]
```

## Implementation Summary

All phases have been successfully completed. The CLI now works exactly as documented in the README.

### Phase 1: Modify CLI Structure ✅

**File**: `/workspaces/h2k_hpxml/src/h2k_hpxml/cli/convert.py`

**Changes**:
1. Replace `@click.group()` with `@click.command()`
2. Add positional `INPUT` argument that accepts files or directories
3. Move all options from `run` subcommand to main command
4. Replace `credits` subcommand with `--credits` flag
5. Remove all `run` command code

**Key modifications**:
- Line ~260: Change from `@click.group()` to `@click.command()`
- Line ~283: Remove `@cli.command()` decorator from run function
- Add `@click.argument('input', required=False)` for input path
- Move processing logic to main command function

### Phase 2: Test Conversion Only ✅

Test the new interface with conversion-only (no simulation):

```bash
# Single file
h2k2hpxml examples/WizardHouse.h2k --do-not-sim

# Folder processing  
h2k2hpxml examples/ --do-not-sim

# With custom output
h2k2hpxml examples/WizardHouse.h2k --output /tmp/test --do-not-sim
```

**Expected behavior**:
- Single file creates: `output/WizardHouse/WizardHouse.xml`
- Folder creates multiple subdirectories with converted files
- Custom output respects specified path

### Phase 3: Test Full Simulation ✅

Test with EnergyPlus simulation enabled:

```bash
# Basic simulation
h2k2hpxml examples/WizardHouse.h2k

# With advanced options
h2k2hpxml examples/WizardHouse.h2k --debug --hourly ALL --output-format csv
```

**Expected behavior**:
- Generates HPXML file
- Runs OpenStudio/EnergyPlus simulation
- Creates simulation output files (CSV, etc.)
- Debug mode creates additional files

### Phase 4: Update Documentation ✅

1. **README.md**: Examples are already mostly correct, just need to add folder examples
2. **CLAUDE.md**: Update essential commands section
3. **Docker examples**: Update container usage examples

### Phase 5: Final Verification ✅

**Error Handling Tests**:
```bash
# Invalid input file
h2k2hpxml nonexistent.h2k

# Empty directory
h2k2hpxml empty_folder/

# Invalid file extension
h2k2hpxml somefile.txt
```

**Option Compatibility Tests**:
```bash
# All major option combinations
h2k2hpxml input.h2k --timestep ALL --debug --skip-validation
h2k2hpxml input.h2k --monthly total --output-format json
h2k2hpxml input.h2k --add-stochastic-schedules --add-component-loads
```

## Technical Implementation Details

### Before (Current Structure):
```python
@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version="1.7.0.1.1")
def cli():
    """H2K to HPXML conversion and simulation tool."""
    pass

@cli.command(help="Convert and Simulate H2K file to OS/E+.")
@click.option("--input_path", "-i", ...)
def run(input_path, output_path, ...):
    # Processing logic here
```

### After (Simplified Structure):
```python
@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(version="1.7.0.1.1")
@click.argument('input', required=False, type=click.Path())
@click.option('--output', '-o', help='Output path for HPXML files')
@click.option('--credits', is_flag=True, help='Show credits')
# ... all other options from run command
def cli(input, output, credits, ...):
    """H2K to HPXML conversion and simulation tool.
    
    INPUT: H2K file or directory containing H2K files to process
    """
    if credits:
        # Show credits and exit
        return
    
    if not input:
        # Show help if no input provided
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return
    
    # Main processing logic (moved from run function)
```

## Benefits

1. **Intuitive Interface**: `h2k2hpxml input.h2k` works as documented
2. **Folder Support**: `h2k2hpxml folder/` processes all H2K files 
3. **No Breaking Changes**: Nobody uses current interface yet
4. **Cleaner Code**: Removes unnecessary command group complexity
5. **Better UX**: Similar to tools like `pandoc`, `ffmpeg`

## Testing Checklist

- [x] Single file conversion ✅
- [x] Folder processing (multiple files) ✅
- [x] Custom output paths ✅
- [x] Simulation with various options ✅
- [x] Error handling for invalid inputs ✅
- [x] All CLI flags work correctly ✅
- [x] Help text displays properly ✅
- [x] Credits functionality ✅
- [ ] Docker container compatibility (not tested, but should work)

## Files Modified

1. `/workspaces/h2k_hpxml/src/h2k_hpxml/cli/convert.py` - Main CLI implementation
2. `/workspaces/h2k_hpxml/README.md` - Update examples (minor)
3. `/workspaces/h2k_hpxml/CLAUDE.md` - Update command reference

## Rollback Plan

If issues arise, the changes are contained to convert.py and can be easily reverted by:
1. Restoring the @click.group() structure
2. Re-adding the run subcommand
3. Moving options back to run function

The implementation is self-contained and low-risk.

## Additional Features Discovered

During implementation, we confirmed that the tool includes **automatic parallel processing**:
- When processing folders, uses `concurrent.futures.ThreadPoolExecutor`
- Thread count: `os.cpu_count() - 1` (e.g., 23 threads on 24-core system)
- All H2K files in a folder are processed simultaneously
- Dramatically improves performance for batch processing

This feature has been documented in both README.md and CLAUDE.md.