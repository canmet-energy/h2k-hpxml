#!/usr/bin/env python3
"""
Demonstrate how example file discovery would work on Windows.
"""

from pathlib import Path
import platform

def simulate_windows_discovery():
    """Simulate how example discovery works on Windows."""
    print("🪟 Windows Example File Discovery Simulation")
    print("=" * 50)
    
    # Simulate what __file__ would be on Windows
    simulated_windows_paths = [
        # uv project environment  
        r"C:\Users\john\.virtualenvs\my-project\Lib\site-packages\h2k_hpxml\examples\__init__.py",
        
        # Global uv installation
        r"C:\Users\john\AppData\Local\uv\cache\tools\h2k-hpxml\Lib\site-packages\h2k_hpxml\examples\__init__.py",
        
        # System pip installation  
        r"C:\Python312\Lib\site-packages\h2k_hpxml\examples\__init__.py",
        
        # User pip installation
        r"C:\Users\john\AppData\Roaming\Python\Python312\site-packages\h2k_hpxml\examples\__init__.py"
    ]
    
    for i, simulated_file in enumerate(simulated_windows_paths, 1):
        print(f"\n{i}. Simulated Windows installation:")
        print(f"   __file__ = {simulated_file}")
        
        # Show how Path(__file__).parent works
        examples_dir = Path(simulated_file).parent
        print(f"   Examples dir = {examples_dir}")
        
        # Show individual example file paths  
        example_files = [
            "WizardHouse.h2k",
            "ERS-EX-10000.H2K", 
            "WizardHouse_0.13.h2k"
        ]
        
        print(f"   Example files would be at:")
        for example in example_files:
            example_path = examples_dir / example
            print(f"     • {example_path}")


def show_actual_discovery():
    """Show how the actual discovery works on current platform."""
    print(f"\n🖥️  Actual Discovery on {platform.system()}")
    print("=" * 50)
    
    try:
        from h2k_hpxml.examples import get_examples_directory, get_wizard_house
        
        # Show the actual mechanism
        import h2k_hpxml.examples
        actual_file = h2k_hpxml.examples.__file__
        print(f"Actual __file__: {actual_file}")
        
        examples_dir = get_examples_directory()  
        print(f"Examples directory: {examples_dir}")
        
        wizard_house = get_wizard_house()
        print(f"WizardHouse.h2k: {wizard_house}")
        
        # Test path operations
        if wizard_house:
            print(f"File exists: {wizard_house.exists()}")
            print(f"File size: {wizard_house.stat().st_size if wizard_house.exists() else 'N/A'} bytes")
            
            # Show Windows-style path (even on Linux for demo)
            windows_style = str(wizard_house).replace('/', '\\')
            print(f"Windows-style path: {windows_style}")
        
    except ImportError as e:
        print(f"❌ Could not import h2k_hpxml.examples: {e}")


def main():
    print("H2K-HPXML Example File Discovery Demo")
    print("=" * 60)
    
    simulate_windows_discovery()
    show_actual_discovery()
    
    print(f"\n✅ Key Points:")
    print(f"  • Uses Python's __file__ variable (always available)")
    print(f"  • Works on any platform (Windows, macOS, Linux)")  
    print(f"  • pathlib.Path handles path separators automatically")
    print(f"  • Files are packaged INTO the wheel/installation")
    print(f"  • No external downloads or configuration needed")
    print(f"  • Works with any Python environment (venv, conda, uv, etc.)")


if __name__ == "__main__":
    main()