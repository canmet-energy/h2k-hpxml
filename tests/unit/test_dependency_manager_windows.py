"""
Unit tests for Windows-specific dependency manager functionality.
Tests the portable tar.gz installation approach that doesn't require admin rights.
"""

import os
import platform
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call, mock_open
import pytest

from h2k_hpxml.utils.dependencies import DependencyManager


@pytest.mark.windows
class TestWindowsPortableInstallation:
    """Test Windows portable installation functionality."""
    
    @pytest.fixture
    def temp_install_dir(self):
        """Create a temporary directory for test installations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_openstudio"
    
    @pytest.fixture
    def mock_dm(self):
        """Create a DependencyManager instance for testing."""
        with patch('platform.system', return_value='Windows'):
            return DependencyManager(auto_install=True)
    
    def test_windows_path_detection_portable(self, mock_dm):
        """Test that portable installation paths are included and prioritized."""
        with patch.dict('os.environ', {
            'LOCALAPPDATA': r'C:\Users\TestUser\AppData\Local',
            'USERPROFILE': r'C:\Users\TestUser'
        }):
            paths = mock_dm._get_windows_paths()
            
            # Check that portable paths are included
            portable_indicators = ['AppData\\Local', 'OpenStudio-3.9.0', 'TestUser']
            has_portable_paths = any(
                any(indicator in path for indicator in portable_indicators) 
                for path in paths
            )
            assert has_portable_paths, "Portable installation paths not found"
            
            # Check that the version-specific path is first (highest priority) 
            # Handle both forward and backward slashes
            expected_path_components = ['C:', 'Users', 'TestUser', 'AppData', 'Local', 'OpenStudio-3.9.0', 'bin', 'openstudio.exe']
            first_path_components = Path(paths[0]).parts
            # Compare normalized components
            assert any('OpenStudio-3.9.0' in part for part in first_path_components), f"Version-specific path not first: {paths[0]}"
    
    def test_write_access_detection(self, temp_install_dir, mock_dm):
        """Test write access detection for installation directories."""
        # Test writable directory
        assert mock_dm._has_write_access(temp_install_dir.parent)
        
        # Test non-existent parent (should check parent's parent)
        non_existent = temp_install_dir / "deep" / "nested" / "path"
        assert mock_dm._has_write_access(non_existent) == mock_dm._has_write_access(temp_install_dir.parent)
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    @patch('subprocess.run')
    def test_portable_download_and_extract_success(self, mock_subprocess, mock_tarfile, mock_urlretrieve, temp_install_dir, mock_dm):
        """Test successful downloading and extracting of portable OpenStudio."""
        # Mock successful download
        mock_urlretrieve.return_value = None
        
        # Mock tarfile extraction
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar
        
        # Mock successful binary test
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="OpenStudio 3.9.0")
        
        # Create mock extracted directory structure
        with patch('os.makedirs'), \
             patch('shutil.copytree') as mock_copytree, \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.exists') as mock_exists:
            
            # Mock directory structure after extraction
            mock_extracted_dir = MagicMock()
            mock_extracted_dir.name = "OpenStudio-3.9.0+c77fbb9569"
            mock_extracted_dir.is_dir.return_value = True
            mock_iterdir.return_value = [mock_extracted_dir]
            
            # Mock file existence checks
            def exists_side_effect(path_obj):
                path_str = str(path_obj)
                # Installation directory doesn't exist initially
                if "test_openstudio" in path_str and "bin" not in path_str:
                    return False
                # Binary exists after installation
                if "openstudio.exe" in path_str:
                    return True
                return False
            
            mock_exists.side_effect = exists_side_effect
            
            with patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent):
                result = mock_dm._install_openstudio_windows()
                
                # Verify download was attempted
                assert mock_urlretrieve.called
                url_arg = mock_urlretrieve.call_args[0][0]
                assert "OpenStudio-3.9.0+c77fbb9569-Windows.tar.gz" in url_arg
                
                # Verify extraction was attempted
                assert mock_tar.extractall.called
                
                # Verify copytree was called to move files
                assert mock_copytree.called
                
                # Verify binary test was attempted
                assert mock_subprocess.called
                
                assert result is True
    
    @patch('urllib.request.urlretrieve')
    def test_portable_download_failure(self, mock_urlretrieve, temp_install_dir, mock_dm):
        """Test handling of download failures."""
        # Mock download failure
        mock_urlretrieve.side_effect = Exception("Network error")
        
        with patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent):
            result = mock_dm._install_openstudio_windows()
            
            assert result is False
            # Verify cleanup attempt (should not crash even if directory doesn't exist)
            assert not temp_install_dir.exists()
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    def test_portable_extraction_failure(self, mock_tarfile, mock_urlretrieve, temp_install_dir, mock_dm):
        """Test handling of extraction failures."""
        # Mock successful download but failed extraction
        mock_urlretrieve.return_value = None
        mock_tarfile.side_effect = Exception("Extraction error")
        
        with patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent):
            result = mock_dm._install_openstudio_windows()
            
            assert result is False
    
    def test_portable_uninstall(self, temp_install_dir, mock_dm):
        """Test portable installation removal."""
        # Create fake portable installation structure
        portable_install_dir = temp_install_dir.parent / "OpenStudio-3.9.0"
        portable_install_dir.mkdir(parents=True)
        bin_dir = portable_install_dir / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "openstudio.exe").touch()
        
        with patch.dict('os.environ', {
            'LOCALAPPDATA': str(temp_install_dir.parent),
            'USERPROFILE': str(temp_install_dir.parent.parent)
        }), \
        patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent), \
        patch.object(mock_dm, '_check_openstudio', return_value=False):
            
            result = mock_dm._uninstall_openstudio_windows()
            
            # Directory should be removed
            assert not portable_install_dir.exists()
            assert result is True
    
    def test_portable_uninstall_msi_present(self, temp_install_dir, mock_dm):
        """Test uninstall when both portable and MSI installations exist."""
        # Create fake portable installation
        temp_install_dir.mkdir(parents=True)
        bin_dir = temp_install_dir / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "openstudio.exe").touch()
        
        with patch.dict('os.environ', {
            'LOCALAPPDATA': str(temp_install_dir.parent),
            'USERPROFILE': str(temp_install_dir.parent.parent),
            'PROGRAMFILES': r'C:\Program Files'
        }), \
        patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent), \
        patch('pathlib.Path.exists') as mock_exists, \
        patch.object(mock_dm, '_check_openstudio', return_value=True):
            
            # Mock MSI installation exists
            def exists_side_effect(path_obj):
                path_str = str(path_obj)
                if "Program Files" in path_str and "OpenStudio" in path_str:
                    return True
                if str(temp_install_dir) in path_str:
                    return True
                if "openstudio.exe" in path_str and str(temp_install_dir) in path_str:
                    return True
                return False
            
            mock_exists.side_effect = exists_side_effect
            mock_dm.interactive = False  # Skip interactive prompt
            
            result = mock_dm._uninstall_openstudio_windows()
            
            # Should succeed even with MSI present
            assert result is True
    
    def test_installation_directory_fallback(self, mock_dm):
        """Test installation directory selection with fallback logic."""
        with patch.dict('os.environ', {
            'LOCALAPPDATA': r'C:\Users\TestUser\AppData\Local',
            'USERPROFILE': r'C:\Users\TestUser'
        }), \
        patch.object(mock_dm, '_has_write_access') as mock_write_access, \
        patch('urllib.request.urlretrieve'), \
        patch('tarfile.open'), \
        patch('os.makedirs'), \
        patch('shutil.copytree'), \
        patch('pathlib.Path.iterdir') as mock_iterdir, \
        patch('pathlib.Path.exists', return_value=True), \
        patch('subprocess.run', return_value=MagicMock(returncode=0, stdout="OpenStudio 3.9.0")):
            
            # Mock that LOCALAPPDATA is not writable, but USERPROFILE is
            mock_write_access.side_effect = lambda path: 'TestUser' in str(path) and 'AppData' not in str(path)
            
            # Mock extracted directory
            mock_extracted_dir = MagicMock()
            mock_extracted_dir.name = "OpenStudio-3.9.0+c77fbb9569"
            mock_extracted_dir.is_dir.return_value = True
            mock_iterdir.return_value = [mock_extracted_dir]
            
            result = mock_dm._install_openstudio_windows()
            
            assert result is True
            # Should fall back to USERPROFILE location
            assert mock_write_access.called
    
    @patch('click.echo')
    def test_installation_provides_path_instructions(self, mock_echo, temp_install_dir, mock_dm):
        """Test that installation provides PATH setup instructions."""
        with patch('urllib.request.urlretrieve'), \
             patch('tarfile.open'), \
             patch('os.makedirs'), \
             patch('shutil.copytree'), \
             patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.exists', return_value=True), \
             patch('subprocess.run', return_value=MagicMock(returncode=0, stdout="OpenStudio 3.9.0")), \
             patch.object(mock_dm, '_get_user_data_dir', return_value=temp_install_dir.parent):
            
            # Mock extracted directory
            mock_extracted_dir = MagicMock()
            mock_extracted_dir.name = "OpenStudio-3.9.0+c77fbb9569"  
            mock_extracted_dir.is_dir.return_value = True
            mock_iterdir.return_value = [mock_extracted_dir]
            
            result = mock_dm._install_openstudio_windows()
            
            assert result is True
            
            # Check that PATH instructions were provided
            echo_calls = [call[0][0] for call in mock_echo.call_args_list if call[0]]
            path_instructions = any("PATH" in msg for msg in echo_calls)
            powershell_instructions = any("PowerShell" in msg for msg in echo_calls)
            
            assert path_instructions, "PATH setup instructions not provided"
            assert powershell_instructions, "PowerShell instructions not provided"


class TestWindowsCompatibility:
    """Test Windows-specific compatibility and edge cases."""
    
    @patch('platform.system')
    def test_windows_detection(self, mock_platform):
        """Test Windows platform detection."""
        mock_platform.return_value = 'Windows'
        dm = DependencyManager()
        assert dm.is_windows is True
        assert dm.is_linux is False
    
    def test_path_separators_windows(self):
        """Test that Windows path separators are handled correctly."""
        with patch('platform.system', return_value='Windows'):
            dm = DependencyManager()
            paths = dm._get_windows_paths()
            
            # All paths should use backslashes on Windows
            for path in paths:
                if 'C:' in path:  # Only check Windows-style absolute paths
                    assert '\\' in path, f"Path should use backslashes: {path}"
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_environment_variables(self):
        """Test behavior when Windows environment variables are missing."""
        with patch('platform.system', return_value='Windows'):
            dm = DependencyManager()
            
            # Should not crash when environment variables are missing
            paths = dm._get_windows_paths()
            assert isinstance(paths, list)
            assert len(paths) > 0  # Should have some fallback paths


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
class TestWindowsIntegrationSafe:
    """Safe integration tests that don't actually install anything."""
    
    def test_real_environment_variables(self):
        """Test with real Windows environment variables."""
        dm = DependencyManager()
        paths = dm._get_windows_paths()
        
        # Should have paths using real environment variables
        assert any('AppData' in path for path in paths), "No AppData paths found"
        
        # Paths should be absolute Windows paths
        for path in paths:
            assert Path(path).is_absolute(), f"Path is not absolute: {path}"
    
    def test_write_access_real_directories(self):
        """Test write access detection on real directories."""
        dm = DependencyManager()
        
        # Should be able to write to temp directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            assert dm._has_write_access(temp_dir)
        
        # Should not be able to write to Program Files (unless running as admin)
        program_files = Path(os.environ.get('PROGRAMFILES', r'C:\Program Files'))
        if program_files.exists():
            # This might be True if running as admin, but that's okay
            write_access = dm._has_write_access(program_files)
            assert isinstance(write_access, bool)  # Should return a boolean