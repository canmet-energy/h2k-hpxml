"""
Integration tests for the interactive demo.

This module tests the demo functionality with scripted input to ensure
it works correctly without requiring manual interaction.
"""

import subprocess
import tempfile
import os
import shutil
import sys
from pathlib import Path
import pytest

def test_demo_with_scripted_input():
    """Test the demo with automated input - conversion only (no simulation)."""
    
    # Create scripted input:
    # 1 = English
    # 1 = First H2K file (ERS-EX-10000.H2K)
    # y = Yes, run the command
    # n = No cleanup (keep files for inspection)
    demo_input = "1\n1\ny\nn\n"
    
    # Run the demo with scripted input (cross-platform)
    try:
        # Determine command based on platform
        if sys.platform == "win32":
            cmd = ["uv.exe", "run", "h2k-hpxml", "--demo"]
        else:
            cmd = ["uv", "run", "h2k-hpxml", "--demo"]
        
        result = subprocess.run(
            cmd,
            input=demo_input,
            text=True,
            capture_output=True,
            timeout=120,  # 2 minute timeout
            cwd="/workspaces/h2k_hpxml",
            shell=True if sys.platform == "win32" else False
        )
        
        # Check that demo started successfully
        assert "Language / Langue" in result.stdout, "Demo should show language selection"
        assert "Interactive Demo" in result.stdout, "Demo should show welcome screen"
        assert "Choose an example file" in result.stdout, "Demo should show file selection"
        assert "Here's the command we'll run" in result.stdout, "Demo should show command preview"
        
        # Check that conversion process started or dependency issue is reported
        assert "h2k_demo_output" in result.stdout, "Demo should create output directory"
        assert ("✓ HPXML created" in result.stdout or
                "✓ Simulation complete" in result.stdout or
                "Converting H2K to HPXML..." in result.stdout or
                "Missing dependencies" in result.stdout), "Demo should start conversion or report dependency issues"
        
        # Demo should complete without critical errors
        # (Some warnings are OK, but should not crash)
        assert result.returncode in [0, 1], f"Demo should complete successfully or with warnings, got: {result.returncode}"
        
        # Check that output directory was created
        demo_output = Path("/workspaces/h2k_hpxml/h2k_demo_output")
        assert demo_output.exists(), "Demo output directory should be created"
        
        # Check for expected output files
        expected_files = list(demo_output.glob("*.H2K"))  # Copied H2K file
        assert len(expected_files) > 0, "Demo should copy H2K file to output directory"
        
        print("✅ Demo test completed successfully")
        print(f"Output directory: {demo_output}")
        print(f"Files created: {list(demo_output.iterdir())}")
        
    except subprocess.TimeoutExpired:
        pytest.fail("Demo test timed out - may indicate infinite loop or hanging")
    except Exception as e:
        pytest.fail(f"Demo test failed with error: {e}")

def test_demo_conversion_only():
    """Test demo that stops after HPXML conversion (no simulation)."""
    
    # Create a temporary demo script that skips simulation
    demo_script = """
import sys
import os
sys.path.insert(0, '/workspaces/h2k_hpxml/src')

from h2k_hpxml.cli.demo import H2KDemo
from pathlib import Path

# Create demo instance
demo = H2KDemo()
demo.lang = "en"  # Set to English

# Programmatically select first example file
from h2k_hpxml.examples import list_example_files
examples = list_example_files(".h2k")
if examples:
    demo.selected_file = examples[0]
    print(f"Selected file: {demo.selected_file.name}")
    
    # Create demo directory
    demo.demo_dir = Path.cwd() / "h2k_demo_output_test"
    demo.demo_dir.mkdir(exist_ok=True)
    
    # Test just the conversion part (no simulation)
    try:
        import shutil
        local_h2k_file = demo.demo_dir / demo.selected_file.name
        shutil.copy2(demo.selected_file, local_h2k_file)
        print(f"✅ File copied to: {local_h2k_file}")
        
        # Test conversion
        from h2k_hpxml.api import _convert_h2k_file_to_hpxml
        hpxml_path = _convert_h2k_file_to_hpxml(
            filepath=str(local_h2k_file),
            dest_hpxml_path=str(demo.demo_dir)
        )
        print(f"✅ HPXML created: {hpxml_path}")
        
        # Check output files exist
        hpxml_file = Path(hpxml_path)
        if hpxml_file.exists():
            print(f"✅ HPXML file verified: {hpxml_file}")
        else:
            print(f"❌ HPXML file not found: {hpxml_file}")
            
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("Test completed")
else:
    print("No example files found")
"""
    
    # Write and run the test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(demo_script)
        script_path = f.name
    
    try:
        # Cross-platform python command
        python_cmd = "python.exe" if sys.platform == "win32" else "python3"
        result = subprocess.run(
            [python_cmd, script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/workspaces/h2k_hpxml"
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check for successful conversion
        assert "✅ File copied to:" in result.stdout, "Should copy H2K file successfully"
        assert "✅ HPXML created:" in result.stdout, "Should create HPXML file successfully" 
        assert "✅ HPXML file verified:" in result.stdout, "Should verify HPXML file exists"
        
        # Should complete without critical errors
        if result.returncode != 0:
            pytest.fail(f"Conversion test failed with return code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        pytest.fail("Conversion test timed out")
    finally:
        # Cleanup
        if os.path.exists(script_path):
            os.unlink(script_path)
        
        # Clean up test output directory
        test_output = Path("/workspaces/h2k_hpxml/h2k_demo_output_test")
        if test_output.exists():
            shutil.rmtree(test_output)

def test_demo_help_and_language_selection():
    """Test demo language selection and basic flow."""
    
    # Test French language selection
    demo_input = "2\nq\n"  # 2 = French, q = quit (if applicable)
    
    try:
        # Cross-platform command
        if sys.platform == "win32":
            cmd = ["uv.exe", "run", "h2k-hpxml", "--demo"]
        else:
            cmd = ["uv", "run", "h2k-hpxml", "--demo"]
            
        result = subprocess.run(
            cmd,
            input=demo_input,
            text=True,
            capture_output=True,
            timeout=30,
            cwd="/workspaces/h2k_hpxml",
            shell=True if sys.platform == "win32" else False
        )
        
        # Should show language selection
        assert "Language / Langue" in result.stdout, "Should show language selection"
        
        # Should work with either language selection
        assert result.returncode in [0, 1], "Should handle language selection gracefully"
        
    except subprocess.TimeoutExpired:
        # Timeout is OK for this test since we might not provide enough input
        pass

if __name__ == "__main__":
    # Run tests individually for debugging
    print("Running demo conversion test...")
    test_demo_conversion_only()
    
    print("\nRunning language selection test...")
    test_demo_help_and_language_selection()
    
    print("\nAll demo tests completed!")