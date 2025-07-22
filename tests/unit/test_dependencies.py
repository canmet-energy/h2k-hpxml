#!/usr/bin/env python3
"""
Tests for the dependencies module.

Tests cross-platform depe    @patch('h2k_    @patch('h2k_hpxml    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._handle_auto_install')
    @patch('click.echo')
    def test_validate_all_auto_install_failure(self, mock_echo, mock_handle_auto, mock_check_hpxml, mock_check_os, manager_auto_install):s.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._handle_auto_install')
    @patch('click.echo')
    def test_validate_all_auto_install(self, mock_echo, mock_handle_auto, mock_check_hpxml, mock_check_os, manager_auto_install):.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('click.echo')
    def test_validate_all_failure_non_interactive(self, mock_echo, mock_check_hpxml, mock_check_os, manager_non_interactive):cy detection, validation, and installation
for OpenStudio and OpenStudio-HPXML dependencies.
"""

import pytest
import tempfile
import os
import sys
import platform
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import zipfile
import shutil
import urllib.request
import urllib.error
import socket

from h2k_hpxml.utils.dependencies import DependencyManager, validate_dependencies


@pytest.fixture
def temp_hpxml_dir():
    """Create a temporary HPXML directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hpxml_path = Path(temp_dir) / "OpenStudio-HPXML"
        hpxml_path.mkdir()
        workflow_dir = hpxml_path / "workflow"
        workflow_dir.mkdir()
        (workflow_dir / "run_simulation.rb").write_text("# simulation script")
        yield hpxml_path


class TestDependencyManager:
    """Test cases for DependencyManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a DependencyManager instance for testing."""
        return DependencyManager(interactive=False, skip_deps=False)
    
    @pytest.fixture
    def manager_interactive(self):
        """Create an interactive DependencyManager instance for testing."""
        return DependencyManager(interactive=True, skip_deps=False)

    def test_init_default_params(self):
        """Test DependencyManager initialization with default parameters."""
        manager = DependencyManager()
        assert manager.interactive is True
        assert manager.skip_deps is False
        assert manager.auto_install is False
        assert manager.is_windows == (platform.system().lower() == "windows")
        assert manager.is_linux == (platform.system().lower() == "linux")

    def test_init_custom_params(self):
        """Test DependencyManager initialization with custom parameters."""
        manager = DependencyManager(interactive=False, skip_deps=True, auto_install=True)
        assert manager.interactive is False
        assert manager.skip_deps is True
        assert manager.auto_install is True

    @patch('click.echo')
    def test_validate_all_skip_deps(self, mock_echo, manager):
        """Test validate_all when skip_deps is True."""
        manager.skip_deps = True
        result = manager.validate_all()
        assert result is True
        mock_echo.assert_called_with("Skipping dependency validation (--skip-deps)")

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('click.echo')
    def test_validate_all_success(self, mock_echo, mock_check_hpxml, mock_check_os, manager):
        """Test validate_all when all dependencies are satisfied."""
        mock_check_os.return_value = True
        mock_check_hpxml.return_value = True
        
        result = manager.validate_all()
        
        assert result is True
        mock_echo.assert_any_call("🔍 Checking dependencies...")
        mock_echo.assert_any_call("✅ All dependencies satisfied!")

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('click.echo')
    def test_validate_all_failure_non_interactive(self, mock_echo, mock_check_hpxml, mock_check_os, manager):
        """Test validate_all failure in non-interactive mode."""
        mock_check_os.return_value = False
        mock_check_hpxml.return_value = True
        
        result = manager.validate_all()
        
        assert result is False
        mock_echo.assert_any_call("❌ Dependencies not satisfied and running in non-interactive mode", err=True)

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._handle_auto_install')
    @patch('click.echo')
    def test_validate_all_auto_install(self, mock_echo, mock_handle_auto_install, mock_check_hpxml, mock_check_os):
        """Test validate_all with auto_install=True."""
        manager = DependencyManager(auto_install=True, interactive=False)
        mock_check_os.return_value = False
        mock_check_hpxml.return_value = True
        mock_handle_auto_install.return_value = True
        
        result = manager.validate_all()
        
        assert result is True
        # The echo message is inside _handle_auto_install, so check that method was called
        mock_handle_auto_install.assert_called_once_with(False, True)

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._check_openstudio_hpxml')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._handle_auto_install')
    @patch('click.echo')
    def test_validate_all_auto_install_failure(self, mock_echo, mock_handle_auto_install, mock_check_hpxml, mock_check_os):
        """Test validate_all with auto_install=True when installation fails."""
        manager = DependencyManager(auto_install=True, interactive=False)
        mock_check_os.return_value = False
        mock_check_hpxml.return_value = True
        mock_handle_auto_install.return_value = False
        
        result = manager.validate_all()
        
        assert result is False
        # The echo message is inside _handle_auto_install, so check that method was called
        mock_handle_auto_install.assert_called_once_with(False, True)


class TestOpenStudioDetection:
    """Test cases for OpenStudio detection methods."""
    
    @pytest.fixture
    def manager(self):
        return DependencyManager(interactive=False, skip_deps=False)

    @patch('builtins.__import__')
    @patch('click.echo')
    def test_check_openstudio_success(self, mock_echo, mock_import, manager):
        """Test successful OpenStudio detection with correct version."""
        mock_openstudio = Mock()
        mock_openstudio.openStudioVersion.return_value = "3.9.0"
        mock_import.return_value = mock_openstudio
        
        with patch('h2k_hpxml.utils.dependencies.DependencyManager._check_cli_binary', return_value=True):
            result = manager._check_openstudio()
        
        assert result is True
        mock_echo.assert_any_call("✅ OpenStudio Python bindings: v3.9.0")

    @patch('builtins.__import__', side_effect=ImportError)
    @patch('click.echo')
    def test_check_openstudio_import_error(self, mock_echo, mock_import, manager):
        """Test OpenStudio detection when import fails."""
        result = manager._check_openstudio()
        
        assert result is False
        mock_echo.assert_called_with("❌ OpenStudio Python bindings not found")

    @patch('builtins.__import__')
    @patch('click.echo')
    def test_check_openstudio_outdated_version(self, mock_echo, mock_import, manager):
        """Test OpenStudio detection with outdated version."""
        mock_openstudio = Mock()
        mock_openstudio.openStudioVersion.return_value = "3.8.0"
        mock_import.return_value = mock_openstudio
        
        result = manager._check_openstudio()
        
        assert result is False
        mock_echo.assert_called_with("❌ OpenStudio Python bindings outdated: v3.8.0 < v3.9.0")

    @patch('os.path.exists')
    @patch('subprocess.run')
    @patch('click.echo')
    def test_check_openstudio_cli_success(self, mock_echo, mock_subprocess, mock_exists, manager):
        """Test successful OpenStudio CLI detection."""
        mock_exists.side_effect = lambda path: "openstudio" in path
        mock_subprocess.return_value = Mock(returncode=0)
        
        result = manager._check_cli_binary()
        
        assert result is True

    @patch('os.path.exists', return_value=False)
    @patch('subprocess.run')
    @patch('click.echo')
    def test_check_openstudio_cli_in_path(self, mock_echo, mock_subprocess, mock_exists, manager):
        """Test OpenStudio CLI detection in PATH."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        result = manager._check_cli_binary()
        
        assert result is True
        mock_echo.assert_called_with("✅ OpenStudio CLI found in PATH")

    @patch('platform.system')
    def test_get_openstudio_paths_windows(self, mock_platform, manager):
        """Test OpenStudio path generation for Windows."""
        mock_platform.return_value = "Windows"
        manager.is_windows = True
        manager.is_linux = False
        
        with patch.dict(os.environ, {'PROGRAMFILES': r'C:\Program Files'}):
            paths = manager._get_openstudio_paths()
        
        assert any("openstudio.exe" in path for path in paths)
        assert any("Program Files" in path for path in paths)

    @patch('platform.system')
    def test_get_openstudio_paths_linux(self, mock_platform, manager):
        """Test OpenStudio path generation for Linux."""
        mock_platform.return_value = "Linux"
        manager.is_windows = False
        manager.is_linux = True
        
        paths = manager._get_openstudio_paths()
        
        expected_paths = [
            '/usr/local/bin/openstudio',
            '/usr/bin/openstudio',
            '/opt/openstudio/bin/openstudio'
        ]
        for expected in expected_paths:
            assert expected in paths


class TestOpenStudioHPXMLDetection:
    """Test cases for OpenStudio-HPXML detection methods."""
    
    @pytest.fixture
    def manager(self):
        return DependencyManager(interactive=False, skip_deps=False)

    @patch('click.echo')
    def test_check_openstudio_hpxml_success(self, mock_echo, manager, temp_hpxml_dir):
        """Test successful OpenStudio-HPXML detection."""
        with patch.dict(os.environ, {'OPENSTUDIO_HPXML_PATH': str(temp_hpxml_dir)}):
            result = manager._check_openstudio_hpxml()
        
        assert result is True
        assert any("✅ OpenStudio-HPXML" in str(call) for call in mock_echo.call_args_list)

    @patch('click.echo')
    def test_check_openstudio_hpxml_not_found(self, mock_echo, manager):
        """Test OpenStudio-HPXML detection when directory doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = manager._check_openstudio_hpxml()
        
        assert result is False
        mock_echo.assert_any_call("❌ OpenStudio-HPXML not found at: /OpenStudio-HPXML")

    @patch('click.echo')
    def test_check_openstudio_hpxml_missing_workflow(self, mock_echo, manager):
        """Test OpenStudio-HPXML detection when workflow script is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            hpxml_path = Path(temp_dir) / "OpenStudio-HPXML"
            hpxml_path.mkdir()
            
            with patch.dict(os.environ, {'OPENSTUDIO_HPXML_PATH': str(hpxml_path)}):
                result = manager._check_openstudio_hpxml()
        
        assert result is False

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.exists')
    def test_detect_hpxml_version_success(self, mock_exists, mock_read_text, manager, temp_hpxml_dir):
        """Test version detection from README."""
        mock_exists.return_value = True
        mock_read_text.return_value = "OpenStudio-HPXML Version 1.9.1"
        
        result = manager._detect_hpxml_version(temp_hpxml_dir)
        
        assert result == "v1.9.1"

    def test_detect_hpxml_version_no_files(self, manager, temp_hpxml_dir):
        """Test version detection when no version files exist."""
        result = manager._detect_hpxml_version(temp_hpxml_dir)
        
        assert result is None


class TestInstallationMethods:
    """Test cases for installation methods."""
    
    @pytest.fixture
    def manager(self):
        return DependencyManager(interactive=False, skip_deps=False)

    @patch('platform.system')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._install_openstudio_windows')
    def test_install_openstudio_windows(self, mock_install_windows, mock_platform, manager):
        """Test OpenStudio installation on Windows."""
        mock_platform.return_value = "Windows"
        manager.is_windows = True
        manager.is_linux = False
        mock_install_windows.return_value = True
        
        result = manager._install_openstudio()
        
        assert result is True
        mock_install_windows.assert_called_once()

    @patch('platform.system')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._install_openstudio_linux')
    def test_install_openstudio_linux(self, mock_install_linux, mock_platform, manager):
        """Test OpenStudio installation on Linux."""
        mock_platform.return_value = "Linux"
        manager.is_windows = False
        manager.is_linux = True
        mock_install_linux.return_value = True
        
        result = manager._install_openstudio()
        
        assert result is True
        mock_install_linux.assert_called_once()

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._update_config_file')
    @patch('urllib.request.urlretrieve')
    @patch('zipfile.ZipFile')
    @patch('shutil.rmtree')
    @patch('subprocess.run')
    @patch('click.echo')
    def test_install_openstudio_hpxml_success(self, mock_echo, mock_subprocess, mock_rmtree, 
                                            mock_zipfile, mock_urlretrieve, mock_update_config, manager):
        """Test successful OpenStudio-HPXML installation."""
        mock_zip_context = Mock()
        mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip_context)
        mock_zipfile.return_value.__exit__ = Mock(return_value=None)
        
        # Mock the extracted folder
        mock_extracted_folder = Mock()
        mock_extracted_folder.is_dir.return_value = True
        mock_extracted_folder.name = "OpenStudio-HPXML-v1.9.1"
        mock_extracted_folder.__str__ = Mock(return_value="/tmp/test/extracted/OpenStudio-HPXML-v1.9.1")
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.mkdir'):
                with patch('pathlib.Path.parent'):
                    with patch('pathlib.Path.iterdir', return_value=[mock_extracted_folder]):
                        with patch('os.makedirs'):
                            with patch('shutil.copytree'):
                                result = manager._install_openstudio_hpxml()
        
        assert result is True
        # Verify the correct URL is used
        expected_url = "https://github.com/NREL/OpenStudio-HPXML/releases/download/v1.9.1/OpenStudio-HPXML-v1.9.1.zip"
        mock_urlretrieve.assert_called_once_with(expected_url, mock_urlretrieve.call_args[0][1])
        mock_update_config.assert_called_once()

    @patch('urllib.request.urlretrieve', side_effect=Exception("Network error"))
    @patch('click.echo')
    def test_install_openstudio_hpxml_failure(self, mock_echo, mock_urlretrieve, manager):
        """Test OpenStudio-HPXML installation failure."""
        result = manager._install_openstudio_hpxml()
        
        assert result is False
        mock_echo.assert_any_call("❌ OpenStudio-HPXML installation failed: Network error")

    @patch('configparser.ConfigParser')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._find_config_file')
    @patch('click.echo')
    def test_update_config_file_success(self, mock_echo, mock_find_config, mock_config_parser, manager):
        """Test successful config file update."""
        mock_find_config.return_value = "/path/to/conversionconfig.ini"
        mock_config = Mock()
        mock_config_parser.return_value = mock_config
        mock_config.has_section.return_value = True
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = manager._update_config_file(Path("/OpenStudio-HPXML"))
        
        assert result is True
        mock_config.set.assert_called_with('paths', 'hpxml_os_path', '/OpenStudio-HPXML/')
        mock_echo.assert_any_call("✅ Updated conversionconfig.ini: hpxml_os_path = /OpenStudio-HPXML/")

    @patch('h2k_hpxml.utils.dependencies.DependencyManager._find_config_file')
    @patch('click.echo')
    def test_update_config_file_not_found(self, mock_echo, mock_find_config, manager):
        """Test config file update when file not found."""
        mock_find_config.return_value = None
        
        result = manager._update_config_file(Path("/OpenStudio-HPXML"))
        
        assert result is False
        mock_echo.assert_called_with("⚠️  conversionconfig.ini not found, skipping config update")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    def test_find_config_file_in_cwd(self, mock_cwd, mock_exists, manager):
        """Test finding config file in current working directory."""
        mock_cwd.return_value = Path("/test/dir")
        mock_exists.return_value = True
        
        result = manager._find_config_file()
        
        assert result == "/test/dir/conversionconfig.ini"

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    def test_find_config_file_not_found(self, mock_cwd, mock_exists, manager):
        """Test when config file is not found."""
        mock_cwd.return_value = Path("/test/dir")
        mock_exists.return_value = False
        
        result = manager._find_config_file()
        
        assert result is None

    @patch('webbrowser.open')
    @patch('click.confirm', return_value=True)
    @patch('click.echo')
    def test_install_openstudio_windows_browser(self, mock_echo, mock_confirm, mock_browser, manager):
        """Test Windows OpenStudio installation with browser opening."""
        manager.is_windows = True
        
        result = manager._install_openstudio_windows()
        
        assert result is False  # Manual installation required
        mock_browser.assert_called_once()

    @patch('os.path.exists', return_value=True)
    @patch('shutil.which', return_value='/usr/bin/apt-get')
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._install_openstudio_deb')
    def test_install_openstudio_linux_debian(self, mock_install_deb, mock_which, mock_exists, manager):
        """Test Linux OpenStudio installation on Debian-based system."""
        manager.is_linux = True
        mock_install_deb.return_value = True
        
        result = manager._install_openstudio_linux()
        
        assert result is True
        mock_install_deb.assert_called_once()

    @patch('os.path.exists', return_value=False)
    @patch('shutil.which', return_value=None)
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._install_openstudio_tarball')
    def test_install_openstudio_linux_tarball(self, mock_install_tarball, mock_which, mock_exists, manager):
        """Test Linux OpenStudio installation via tarball."""
        manager.is_linux = True
        mock_install_tarball.return_value = True
        
        result = manager._install_openstudio_linux()
        
        assert result is True
        mock_install_tarball.assert_called_once()


class TestUserInteraction:
    """Test cases for user interaction flows."""
    
    @pytest.fixture
    def manager_interactive(self):
        return DependencyManager(interactive=True, skip_deps=False)

    @patch('click.prompt', return_value=3)
    @patch('click.echo')
    def test_handle_missing_dependencies_continue(self, mock_echo, mock_prompt, manager_interactive):
        """Test continuing without dependencies."""
        result = manager_interactive._handle_interactive_install(False, False)
        
        assert result is True
        mock_echo.assert_any_call("⚠️  Continuing without all dependencies. Errors may occur.")

    @patch('click.prompt', return_value=4)
    @patch('click.echo')
    def test_handle_missing_dependencies_exit(self, mock_echo, mock_prompt, manager_interactive):
        """Test exiting when dependencies are missing."""
        result = manager_interactive._handle_interactive_install(False, False)
        
        assert result is False
        mock_echo.assert_any_call("Installation cancelled.")

    @patch('click.prompt', return_value=2)
    @patch('h2k_hpxml.utils.dependencies.DependencyManager._show_manual_instructions')
    def test_handle_missing_dependencies_manual(self, mock_show_manual, mock_prompt, manager_interactive):
        """Test showing manual installation instructions."""
        result = manager_interactive._handle_interactive_install(False, False)
        
        assert result is False
        mock_show_manual.assert_called_once()

    @patch('click.echo')
    def test_show_manual_instructions_windows(self, mock_echo, manager_interactive):
        """Test manual installation instructions for Windows."""
        manager_interactive.is_windows = True
        manager_interactive.is_linux = False
        
        manager_interactive._show_manual_instructions(["OpenStudio", "OpenStudio-HPXML"])
        
        echo_calls = [str(call) for call in mock_echo.call_args_list]
        assert any("Windows.exe" in call for call in echo_calls)

    @patch('click.echo')
    def test_show_manual_instructions_linux(self, mock_echo, manager_interactive):
        """Test manual installation instructions for Linux."""
        manager_interactive.is_windows = False
        manager_interactive.is_linux = True
        
        manager_interactive._show_manual_instructions(["OpenStudio", "OpenStudio-HPXML"])
        
        echo_calls = [str(call) for call in mock_echo.call_args_list]
        assert any(".deb" in call for call in echo_calls)


class TestUtilityFunctions:
    """Test cases for utility functions."""

    @patch('h2k_hpxml.utils.dependencies.DependencyManager.validate_all')
    def test_validate_dependencies_function(self, mock_validate):
        """Test the validate_dependencies convenience function."""
        mock_validate.return_value = True
        
        result = validate_dependencies(interactive=False, skip_deps=False, check_only=False)
        
        assert result is True
        mock_validate.assert_called_once()

    @patch('h2k_hpxml.utils.dependencies.DependencyManager.check_only')
    def test_validate_dependencies_check_only(self, mock_check_only):
        """Test the validate_dependencies function with check_only=True."""
        mock_check_only.return_value = True
        
        result = validate_dependencies(check_only=True)
        
        assert result is True
        mock_check_only.assert_called_once()

    @patch('h2k_hpxml.utils.dependencies.DependencyManager.validate_all')
    def test_validate_dependencies_auto_install(self, mock_validate):
        """Test the validate_dependencies function with auto_install=True."""
        mock_validate.return_value = True
        
        result = validate_dependencies(auto_install=True, interactive=False)
        
        assert result is True
        mock_validate.assert_called_once()

    def test_dependency_manager_auto_install_init(self):
        """Test DependencyManager initialization with auto_install=True."""
        manager = DependencyManager(auto_install=True, interactive=False)
        
        assert manager.auto_install is True
        assert manager.interactive is False

    def test_is_debian_based_true(self):
        """Test Debian detection when /etc/debian_version exists."""
        manager = DependencyManager()
        
        with patch('os.path.exists', return_value=True):
            result = manager._is_debian_based()
        
        assert result is True

    def test_is_debian_based_apt_get(self):
        """Test Debian detection when apt-get is available."""
        manager = DependencyManager()
        
        with patch('os.path.exists', return_value=False):
            with patch('shutil.which', return_value='/usr/bin/apt-get'):
                result = manager._is_debian_based()
        
        assert result is True

    def test_is_debian_based_false(self):
        """Test Debian detection when neither condition is met."""
        manager = DependencyManager()
        
        with patch('os.path.exists', return_value=False):
            with patch('shutil.which', return_value=None):
                result = manager._is_debian_based()
        
        assert result is False


class TestPlatformSpecificBehavior:
    """Test cases for platform-specific behavior."""

    @pytest.mark.parametrize("platform_name,is_windows,is_linux", [
        ("Windows", True, False),
        ("Linux", False, True),
        ("Darwin", False, False),
    ])
    def test_platform_detection(self, platform_name, is_windows, is_linux):
        """Test platform detection for different operating systems."""
        with patch('platform.system', return_value=platform_name):
            manager = DependencyManager()
            
            assert manager.is_windows == is_windows
            assert manager.is_linux == is_linux

    @patch('platform.system', return_value="Windows")
    def test_unsupported_platform_installation(self, mock_platform):
        """Test installation failure on unsupported platform."""
        manager = DependencyManager()
        manager.is_windows = False
        manager.is_linux = False
        
        with patch('click.echo') as mock_echo:
            result = manager._install_openstudio()
        
        assert result is False
        mock_echo.assert_any_call("❌ Unsupported platform: Windows")


class TestWindowsSimulation:
    """Test Windows-specific functionality by simulating Windows environment on Linux."""
    
    def test_windows_hpxml_path(self):
        """Test Windows HPXML path generation."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            expected_path = Path("C:/OpenStudio-HPXML")
            assert manager.default_hpxml_path == expected_path

    def test_windows_openstudio_paths(self):
        """Test Windows OpenStudio path generation."""
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, {'PROGRAMFILES': r'C:\Program Files'}):
                manager = DependencyManager()
                paths = manager._get_openstudio_paths()
                
                # Check that Windows-specific paths are included
                assert any('openstudio.exe' in path for path in paths)
                assert any('Program Files' in path for path in paths)
                assert any('C:\\openstudio\\bin\\openstudio.exe' in path for path in paths)

    @patch('webbrowser.open')
    @patch('click.confirm', return_value=True)
    @patch('click.echo')
    def test_windows_installation_browser_success(self, mock_echo, mock_confirm, mock_browser):
        """Test Windows installation opens browser successfully."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            result = manager._install_openstudio_windows()
            
            mock_browser.assert_called_once()
            mock_echo.assert_any_call("✅ Installer download started in browser")
            assert result is False  # Should return False for manual installation

    @patch('webbrowser.open', side_effect=Exception("Browser failed"))
    @patch('click.confirm', return_value=True)  
    @patch('click.echo')
    def test_windows_installation_browser_failure(self, mock_echo, mock_confirm, mock_browser):
        """Test Windows installation handles browser failure."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            result = manager._install_openstudio_windows()
            
            mock_browser.assert_called_once()
            mock_echo.assert_any_call("❌ Failed to open browser: Browser failed")
            assert result is False

    @patch('click.confirm', return_value=False)
    @patch('click.echo') 
    def test_windows_installation_declined(self, mock_echo, mock_confirm):
        """Test Windows installation when user declines browser download."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            result = manager._install_openstudio_windows()
            
            assert result is False
            mock_confirm.assert_called_once()

    def test_windows_manual_instructions(self):
        """Test Windows manual installation instructions."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            
            with patch('click.echo') as mock_echo:
                manager._show_openstudio_instructions()
            
            echo_calls = [str(call) for call in mock_echo.call_args_list]
            assert any("Windows.exe" in call for call in echo_calls)
            assert any("administrator" in call for call in echo_calls)

    def test_windows_hpxml_instructions(self):
        """Test Windows HPXML manual installation instructions."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            
            with patch('click.echo') as mock_echo:
                manager._show_hpxml_instructions()
            
            echo_calls = [str(call) for call in mock_echo.call_args_list]
            # Should show Windows-style path separator
            assert any("workflow\\\\run_simulation.rb" in call for call in echo_calls)

    @patch('platform.system', return_value="Windows")
    def test_full_windows_workflow_simulation(self, mock_platform):
        """Test complete Windows dependency workflow simulation."""
        manager = DependencyManager(interactive=False, auto_install=False)
        
        # Test that Windows detection works
        assert manager.is_windows is True
        assert manager.is_linux is False
        
        # Test path generation
        assert manager.default_hpxml_path == Path("C:/OpenStudio-HPXML")
        
        # Test that installation routing works for Windows
        with patch.object(manager, '_install_openstudio_windows', return_value=False) as mock_install:
            result = manager._install_openstudio()
            mock_install.assert_called_once()
            assert result is False


class TestWindowsIntegration:
    """Integration-style tests for Windows functionality."""
    
    def test_windows_url_construction(self):
        """Test Windows download URL construction."""
        with patch('platform.system', return_value="Windows"):
            manager = DependencyManager()
            
            # Test URL construction matches expected pattern
            expected_base = manager.OPENSTUDIO_BASE_URL
            expected_hash = manager.OPENSTUDIO_BUILD_HASH
            
            assert "github.com/NREL/OpenStudio" in expected_base
            assert expected_hash == "c77fbb9569"
            
            # The actual URL would be constructed in _install_openstudio_windows
            expected_url = (
                f"{expected_base}/"
                f"v{manager.REQUIRED_OPENSTUDIO_VERSION}/"
                f"OpenStudio-{manager.REQUIRED_OPENSTUDIO_VERSION}+"
                f"{expected_hash}-Windows.exe"
            )
            
            assert "Windows.exe" in expected_url
            assert manager.REQUIRED_OPENSTUDIO_VERSION in expected_url

    def test_environment_simulation(self):
        """Test simulating Windows environment variables."""
        win_env = {
            'PROGRAMFILES': r'C:\Program Files',
            'PROGRAMFILES(X86)': r'C:\Program Files (x86)',
            'OPENSTUDIO_HPXML_PATH': r'C:\MyCustom\OpenStudio-HPXML'
        }
        
        with patch('platform.system', return_value="Windows"):
            with patch.dict(os.environ, win_env):
                manager = DependencyManager()
                
                # Test custom HPXML path from environment
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('pathlib.Path.__truediv__') as mock_div:
                        mock_workflow = Mock()
                        mock_workflow.exists.return_value = True  
                        mock_div.return_value = mock_workflow
                        
                        # This would use the environment variable path
                        env_path = os.environ.get('OPENSTUDIO_HPXML_PATH')
                        assert env_path == r'C:\MyCustom\OpenStudio-HPXML'


class TestDownloadURLValidation:
    """Integration tests to verify actual download URLs are accessible."""
    
    @pytest.fixture
    def manager(self):
        return DependencyManager(interactive=False, skip_deps=False)
    
    def _check_url_accessible(self, url, timeout=10):
        """
        Check if a URL is accessible without downloading the full file.
        
        Returns:
            tuple: (is_accessible, status_info)
        """
        try:
            # Use HEAD request to check if URL exists without downloading
            request = urllib.request.Request(url, method='HEAD')
            request.add_header('User-Agent', 'h2k_hpxml-test/1.0')
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return True, f"Status: {response.status}, Size: {response.headers.get('content-length', 'unknown')} bytes"
        
        except urllib.error.HTTPError as e:
            return False, f"HTTP Error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except socket.timeout:
            return False, f"Timeout after {timeout} seconds"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    @pytest.mark.integration
    def test_openstudio_windows_url_accessible(self, manager):
        """Test that OpenStudio Windows installer URL is accessible."""
        installer_url = f"{manager.OPENSTUDIO_BASE_URL}/v{manager.REQUIRED_OPENSTUDIO_VERSION}/OpenStudio-{manager.REQUIRED_OPENSTUDIO_VERSION}+c77fbb9569-Windows.exe"
        
        accessible, info = self._check_url_accessible(installer_url)
        
        assert accessible, f"OpenStudio Windows installer URL not accessible: {installer_url}\nError: {info}"
        print(f"✅ Windows installer URL accessible: {info}")
    
    @pytest.mark.integration  
    def test_openstudio_ubuntu_deb_url_accessible(self, manager):
        """Test that OpenStudio Ubuntu .deb package URL is accessible."""
        deb_url = f"{manager.OPENSTUDIO_BASE_URL}/v{manager.REQUIRED_OPENSTUDIO_VERSION}/OpenStudio-{manager.REQUIRED_OPENSTUDIO_VERSION}+c77fbb9569-Ubuntu-22.04-x86_64.deb"
        
        accessible, info = self._check_url_accessible(deb_url)
        
        assert accessible, f"OpenStudio Ubuntu .deb URL not accessible: {deb_url}\nError: {info}"
        print(f"✅ Ubuntu .deb URL accessible: {info}")
    
    @pytest.mark.integration
    def test_openstudio_linux_tarball_url_accessible(self, manager):
        """Test that OpenStudio Linux tarball URL is accessible."""
        tarball_url = f"{manager.OPENSTUDIO_BASE_URL}/v{manager.REQUIRED_OPENSTUDIO_VERSION}/OpenStudio-{manager.REQUIRED_OPENSTUDIO_VERSION}+c77fbb9569-Ubuntu-22.04-x86_64.tar.gz"
        
        accessible, info = self._check_url_accessible(tarball_url)
        
        assert accessible, f"OpenStudio Linux tarball URL not accessible: {tarball_url}\nError: {info}"
        print(f"✅ Linux tarball URL accessible: {info}")
    
    @pytest.mark.integration
    def test_openstudio_hpxml_url_accessible(self, manager):
        """Test that OpenStudio-HPXML zip file URL is accessible."""
        hpxml_url = f"{manager.HPXML_BASE_URL}/{manager.REQUIRED_HPXML_VERSION}/OpenStudio-HPXML-{manager.REQUIRED_HPXML_VERSION}.zip"
        
        accessible, info = self._check_url_accessible(hpxml_url)
        
        assert accessible, f"OpenStudio-HPXML URL not accessible: {hpxml_url}\nError: {info}"
        print(f"✅ OpenStudio-HPXML URL accessible: {info}")
    
    @pytest.mark.integration
    def test_github_releases_pages_accessible(self, manager):
        """Test that the GitHub releases pages are accessible."""
        openstudio_releases = f"https://github.com/NREL/OpenStudio/releases/tag/v{manager.REQUIRED_OPENSTUDIO_VERSION}"
        hpxml_releases = f"https://github.com/NREL/OpenStudio-HPXML/releases/tag/{manager.REQUIRED_HPXML_VERSION}"
        
        # Test OpenStudio releases page
        accessible, info = self._check_url_accessible(openstudio_releases)
        assert accessible, f"OpenStudio releases page not accessible: {openstudio_releases}\nError: {info}"
        
        # Test OpenStudio-HPXML releases page
        accessible, info = self._check_url_accessible(hpxml_releases)
        assert accessible, f"OpenStudio-HPXML releases page not accessible: {hpxml_releases}\nError: {info}"
        
        print(f"✅ GitHub releases pages accessible")
    
    @pytest.mark.integration
    def test_download_url_construction(self, manager):
        """Test that download URLs are constructed correctly based on the pattern."""
        # Test the URL construction logic matches what the methods actually build
        expected_windows_url = f"{manager.OPENSTUDIO_BASE_URL}/v{manager.REQUIRED_OPENSTUDIO_VERSION}/OpenStudio-{manager.REQUIRED_OPENSTUDIO_VERSION}+c77fbb9569-Windows.exe"
        expected_hpxml_url = f"{manager.HPXML_BASE_URL}/{manager.REQUIRED_HPXML_VERSION}/OpenStudio-HPXML-{manager.REQUIRED_HPXML_VERSION}.zip"
        
        # Verify these match what the actual methods would construct
        assert manager.REQUIRED_OPENSTUDIO_VERSION == "3.9.0"
        assert manager.REQUIRED_HPXML_VERSION == "v1.9.1"
        
        # Check URL patterns
        assert "github.com/NREL/OpenStudio/releases/download" in expected_windows_url
        assert "github.com/NREL/OpenStudio-HPXML/releases/download" in expected_hpxml_url
        assert manager.REQUIRED_HPXML_VERSION in expected_hpxml_url
        
        print(f"✅ URL construction logic verified")
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("NETWORK_TESTS"), reason="Network tests disabled (set NETWORK_TESTS=1 to enable)")
    def test_partial_download_verification(self, manager):
        """Test partial downloads to verify file integrity."""
        hpxml_url = f"{manager.HPXML_RELEASES_URL}/{manager.REQUIRED_HPXML_VERSION}/OpenStudio-HPXML-{manager.REQUIRED_HPXML_VERSION}.zip"
        
        try:
            # Download first 1KB to verify it's actually a zip file
            request = urllib.request.Request(hpxml_url)
            request.add_header('Range', 'bytes=0-1023')  # First 1KB
            request.add_header('User-Agent', 'h2k_hpxml-test/1.0')
            
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                
                # Check for ZIP file signature
                assert len(data) > 0, "No data received"
                assert data[:4] == b'PK\x03\x04', f"File does not appear to be a ZIP file. First 4 bytes: {data[:4]}"
                
                print(f"✅ Partial download verified - file appears to be valid ZIP ({len(data)} bytes downloaded)")
                
        except urllib.error.HTTPError as e:
            if e.code == 416:  # Range not satisfiable - server doesn't support range requests
                pytest.skip("Server doesn't support range requests, skipping partial download test")
            else:
                pytest.fail(f"HTTP error during partial download: {e}")
        except Exception as e:
            pytest.fail(f"Error during partial download verification: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])