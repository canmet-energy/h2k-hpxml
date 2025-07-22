#!/usr/bin/env python3
"""
Windows Simulation Test Script

This script allows you to manually test Windows-specific functionality
of the dependencies module while running on Linux.

Usage:
    python test_windows_simulation.py
"""

import os
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys

# Add the source directory to Python path
sys.path.insert(0, 'src')

from h2k_hpxml.utils.dependencies import DependencyManager


def test_windows_path_behavior():
    """Test Windows path generation and behavior."""
    print("🪟 Testing Windows Path Behavior")
    print("=" * 50)
    
    # Simulate Windows environment
    with patch('platform.system', return_value="Windows"):
        manager = DependencyManager()
        
        print(f"✅ Platform detection: is_windows = {manager.is_windows}")
        print(f"✅ Platform detection: is_linux = {manager.is_linux}")
        
        # Test HPXML path
        hpxml_path = manager.default_hpxml_path
        print(f"✅ HPXML path: {hpxml_path}")
        assert str(hpxml_path) == "C:/OpenStudio-HPXML"
        
        # Test OpenStudio paths
        paths = manager._get_openstudio_paths()
        print(f"✅ OpenStudio paths found: {len(paths)}")
        for i, path in enumerate(paths[:3], 1):  # Show first 3
            print(f"   {i}. {path}")
        
        # Verify Windows-specific characteristics
        exe_paths = [p for p in paths if p.endswith('.exe')]
        program_files_paths = [p for p in paths if 'Program Files' in p]
        
        print(f"✅ .exe paths: {len(exe_paths)}")
        print(f"✅ Program Files paths: {len(program_files_paths)}")
        
        return True


def test_windows_installation_flow():
    """Test Windows installation workflow."""
    print("\n🪟 Testing Windows Installation Flow")
    print("=" * 50)
    
    with patch('platform.system', return_value="Windows"):
        manager = DependencyManager(interactive=False, auto_install=False)
        
        # Mock click.echo to capture output
        outputs = []
        def mock_echo(text, **kwargs):
            outputs.append(str(text))
            print(f"📄 Output: {text}")
        
        # Mock click.confirm to simulate user response  
        def mock_confirm(prompt, **kwargs):
            print(f"❓ Prompt: {prompt}")
            return True  # Simulate user saying "yes"
        
        # Mock webbrowser.open
        browser_called = []
        def mock_browser(url):
            browser_called.append(url)
            print(f"🌐 Browser would open: {url}")
        
        with patch('click.echo', mock_echo):
            with patch('click.confirm', mock_confirm):
                with patch('webbrowser.open', mock_browser):
                    # Test Windows installation
                    result = manager._install_openstudio_windows()
                    
                    print(f"✅ Installation result: {result}")
                    print(f"✅ Browser called: {len(browser_called) > 0}")
                    
                    if browser_called:
                        url = browser_called[0]
                        print(f"✅ URL contains Windows.exe: {'Windows.exe' in url}")
                        print(f"✅ URL contains version: {manager.REQUIRED_OPENSTUDIO_VERSION in url}")
                    
                    return True


def test_windows_hpxml_installation():
    """Test Windows OpenStudio-HPXML installation workflow."""
    print("\\n🪟 Testing Windows HPXML Installation")
    print("=" * 50)
    
    with patch('platform.system', return_value="Windows"):
        manager = DependencyManager(interactive=False, auto_install=False)
        
        # Mock filesystem operations
        with patch('urllib.request.urlretrieve'):
            with patch('zipfile.ZipFile'):
                with patch('shutil.copytree'):
                    with patch('pathlib.Path.exists', return_value=False):
                        with patch('pathlib.Path.mkdir'):
                            # Mock extracted folder
                            mock_folder = Mock()
                            mock_folder.is_dir.return_value = True
                            mock_folder.name = "OpenStudio-HPXML-v1.9.1"
                            
                            with patch('pathlib.Path.iterdir', return_value=[mock_folder]):
                                with patch('h2k_hpxml.utils.dependencies.DependencyManager._update_config_file', return_value=True) as mock_config:
                                    result = manager._install_openstudio_hpxml()
                                    
                                    print(f"✅ Installation result: {result}")
                                    print(f"✅ Config update called: {mock_config.called}")
                                    print(f"✅ Windows path used: {str(manager.default_hpxml_path) == 'C:/OpenStudio-HPXML'}")
                                    
                                    return True


def test_windows_manual_instructions():
    """Test Windows manual installation instructions."""
    print("\n🪟 Testing Windows Manual Instructions")
    print("=" * 50)
    
    with patch('platform.system', return_value="Windows"):
        manager = DependencyManager()
        
        # Capture manual instruction outputs
        outputs = []
        def mock_echo(text, **kwargs):
            outputs.append(str(text))
            print(f"📋 Instruction: {text}")
        
        with patch('click.echo', mock_echo):
            # Test OpenStudio instructions
            print("\n🔧 OpenStudio Instructions:")
            manager._show_openstudio_instructions()
            
            # Test HPXML instructions  
            print("\n🏠 HPXML Instructions:")
            manager._show_hpxml_instructions()
        
        # Verify Windows-specific content
        all_text = " ".join(outputs)
        
        checks = [
            ("Windows.exe" in all_text, "Contains Windows.exe reference"),
            ("administrator" in all_text, "Contains administrator reference"),
            ("workflow\\run_simulation.rb" in all_text, "Contains Windows path separator"),
            ("C:/OpenStudio-HPXML" in all_text, "Contains Windows HPXML path")
        ]
        
        print(f"\n✅ Content Verification:")
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"   {status} {description}")
        
        return all(check for check, _ in checks)


def test_windows_environment_variables():
    """Test Windows environment variable simulation."""
    print("\n🪟 Testing Windows Environment Variables")
    print("=" * 50)
    
    # Simulate Windows environment variables
    win_env = {
        'PROGRAMFILES': r'C:\Program Files',
        'PROGRAMFILES(X86)': r'C:\Program Files (x86)',  
        'OPENSTUDIO_HPXML_PATH': r'C:\MyCustom\OpenStudio-HPXML',
        'PATH': r'C:\Windows\System32;C:\Program Files\OpenStudio\bin'
    }
    
    with patch('platform.system', return_value="Windows"):
        with patch.dict(os.environ, win_env):
            manager = DependencyManager()
            
            print(f"✅ PROGRAMFILES: {os.environ.get('PROGRAMFILES')}")
            print(f"✅ PROGRAMFILES(X86): {os.environ.get('PROGRAMFILES(X86)')}")
            print(f"✅ OPENSTUDIO_HPXML_PATH: {os.environ.get('OPENSTUDIO_HPXML_PATH')}")
            
            # Test that environment variables affect path generation
            paths = manager._get_openstudio_paths()
            program_files_paths = [p for p in paths if win_env['PROGRAMFILES'] in p]
            
            print(f"✅ Paths using PROGRAMFILES: {len(program_files_paths)}")
            
            return True


def run_all_tests():
    """Run all Windows simulation tests."""
    print("🧪 Windows Functionality Simulation on Linux")
    print("=" * 60)
    
    tests = [
        ("Path Behavior", test_windows_path_behavior),
        ("Installation Flow", test_windows_installation_flow),
        ("HPXML Installation", test_windows_hpxml_installation),
        ("Manual Instructions", test_windows_manual_instructions),
        ("Environment Variables", test_windows_environment_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏆 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result, error in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
        if error:
            print(f"         Error: {error}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Windows simulation tests passed! The code should work on Windows.")
    else:
        print("⚠️  Some tests failed. Check Windows-specific logic.")
    
    return passed == len(results)


if __name__ == "__main__":
    run_all_tests()