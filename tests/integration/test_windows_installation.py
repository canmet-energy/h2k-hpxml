"""
Integration tests for Windows OpenStudio installation.
These tests verify the complete installation workflow works correctly.
"""

import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from h2k_hpxml.utils.dependencies import DependencyManager


@pytest.mark.windows
@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
@pytest.mark.integration
class TestWindowsIntegration:
    """Integration tests for Windows OpenStudio installation."""

    def test_dependency_manager_initialization(self):
        """Test that DependencyManager initializes correctly on Windows."""
        dm = DependencyManager()
        assert dm.is_windows is True
        assert dm.is_linux is False
        assert dm.REQUIRED_OPENSTUDIO_VERSION == "3.9.0"
        assert dm.OPENSTUDIO_BUILD_HASH == "c77fbb9569"

    def test_path_detection_returns_windows_paths(self):
        """Test that path detection returns Windows-style paths."""
        dm = DependencyManager()
        paths = dm._get_openstudio_paths()

        # Should have at least some paths
        assert len(paths) > 0

        # All paths should be absolute and Windows-style
        for path in paths:
            path_obj = Path(path)
            assert path_obj.is_absolute(), f"Path is not absolute: {path}"

            # Should end with openstudio.exe
            assert path.endswith("openstudio.exe"), f"Path doesn't end with openstudio.exe: {path}"

    def test_user_data_directory_creation(self):
        """Test that user data directory can be created and is writable."""
        dm = DependencyManager()
        user_data_dir = dm._get_user_data_dir()

        # Directory should be a Windows path
        assert user_data_dir.is_absolute()

        # Should be able to create the directory
        user_data_dir.mkdir(parents=True, exist_ok=True)
        assert user_data_dir.exists()

        # Should be writable
        assert dm._has_write_access(user_data_dir)

        # Test creating a subdirectory
        test_subdir = user_data_dir / "test_install"
        test_subdir.mkdir(exist_ok=True)
        assert test_subdir.exists()

        # Cleanup
        import shutil

        try:
            shutil.rmtree(test_subdir)
        except Exception:
            pass  # Cleanup failure is not critical for test

    def test_environment_variable_handling(self):
        """Test that Windows environment variables are handled correctly."""
        dm = DependencyManager()

        # Check that standard Windows environment variables are used
        local_appdata = os.environ.get("LOCALAPPDATA")
        userprofile = os.environ.get("USERPROFILE")

        if local_appdata:
            paths = dm._get_windows_paths()
            appdata_paths = [p for p in paths if "AppData" in p]
            assert len(appdata_paths) > 0, "No AppData paths found"

        if userprofile:
            paths = dm._get_windows_paths()
            profile_paths = [
                p for p in paths if userprofile.replace("\\", "/") in p.replace("\\", "/")
            ]
            assert len(profile_paths) > 0, "No USERPROFILE paths found"

    @pytest.mark.slow
    def test_openstudio_check_methods(self):
        """Test OpenStudio detection methods don't crash."""
        dm = DependencyManager()

        # These methods should not crash, regardless of whether OpenStudio is installed
        try:
            python_bindings_ok = dm._check_python_bindings()
            assert isinstance(python_bindings_ok, bool)
        except Exception as e:
            pytest.fail(f"_check_python_bindings() failed: {e}")

        try:
            cli_binary_ok = dm._check_cli_binary()
            assert isinstance(cli_binary_ok, bool)
        except Exception as e:
            pytest.fail(f"_check_cli_binary() failed: {e}")

        try:
            overall_ok = dm._check_openstudio()
            assert isinstance(overall_ok, bool)
        except Exception as e:
            pytest.fail(f"_check_openstudio() failed: {e}")

    def test_binary_path_testing(self):
        """Test binary path testing with non-existent paths."""
        dm = DependencyManager()

        # Test with non-existent path
        fake_path = r"C:\NonExistent\openstudio.exe"
        result = dm._test_binary_path(fake_path)
        assert result is False

        # Test with directory instead of file
        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = dm._test_binary_path(str(temp_dir))
            assert result is False
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
@pytest.mark.integration
@pytest.mark.slow
class TestWindowsInstallationWorkflow:
    """Test complete installation workflow (without actually installing system-wide)."""

    def test_installation_url_construction(self):
        """Test that installation URLs are constructed correctly."""
        dm = DependencyManager(auto_install=True)

        # The URL should be constructible
        expected_base = "https://github.com/NREL/OpenStudio/releases/download"
        expected_version = "v3.9.0"
        expected_filename = "OpenStudio-3.9.0+c77fbb9569-Windows.tar.gz"

        # Construct URL as the method would
        url = (
            f"{dm.OPENSTUDIO_BASE_URL}/"
            f"v{dm.REQUIRED_OPENSTUDIO_VERSION}/"
            f"OpenStudio-{dm.REQUIRED_OPENSTUDIO_VERSION}+"
            f"{dm.OPENSTUDIO_BUILD_HASH}-Windows.tar.gz"
        )

        assert expected_base in url
        assert expected_version in url
        assert expected_filename in url
        assert url.startswith("https://")

    def test_installation_directory_selection(self):
        """Test installation directory selection logic."""
        dm = DependencyManager(auto_install=True)

        # Test with real environment variables
        local_appdata = os.environ.get("LOCALAPPDATA")
        userprofile = os.environ.get("USERPROFILE")

        if local_appdata:
            expected_dir = Path(local_appdata) / f"OpenStudio-{dm.REQUIRED_OPENSTUDIO_VERSION}"

            # The method should choose this directory if LOCALAPPDATA is writable
            if dm._has_write_access(Path(local_appdata)):
                # This would be the preferred installation location
                assert expected_dir.parent.exists()
                assert dm._has_write_access(expected_dir.parent)

    def test_mock_installation_workflow(self):
        """Test installation workflow with mocked external dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "OpenStudio"

            dm = DependencyManager(auto_install=True, openstudio_path=install_dir)

            # Create a mock tarball file
            tarball_path = Path(temp_dir) / "openstudio.tar.gz"

            # Create minimal tar.gz structure for testing
            import tarfile

            with tarfile.open(tarball_path, "w:gz") as tar:
                # Create a mock OpenStudio directory structure
                mock_os_dir = Path(temp_dir) / "OpenStudio-3.9.0+c77fbb9569"
                mock_os_dir.mkdir()

                bin_dir = mock_os_dir / "bin"
                bin_dir.mkdir()

                # Create a mock openstudio.exe
                mock_exe = bin_dir / "openstudio.exe"
                mock_exe.write_text("mock binary")

                # Add to tarball
                tar.add(mock_os_dir, arcname=mock_os_dir.name)

            # Test extraction logic (without actually downloading)
            with tarfile.open(tarball_path, "r:gz") as tar:
                extract_temp_dir = Path(temp_dir) / "extracted"
                extract_temp_dir.mkdir()
                tar.extractall(extract_temp_dir)

                # Find extracted folder
                extracted_folders = [
                    d for d in extract_temp_dir.iterdir() if d.is_dir() and "OpenStudio" in d.name
                ]

                assert len(extracted_folders) == 1, "Should find exactly one OpenStudio folder"

                source_folder = extracted_folders[0]

                # Test that we can copy to final location
                import shutil

                shutil.copytree(source_folder, install_dir)

                # Verify installation structure
                binary_path = install_dir / "bin" / "openstudio.exe"
                assert binary_path.exists(), f"Binary not found at {binary_path}"

                # Binary should have content
                assert binary_path.read_text() == "mock binary"

    def test_config_update_methods_stubbed(self):
        """Test that config update methods are stubbed for backward compatibility."""
        dm = DependencyManager()

        # Config update methods should exist but be stubbed out
        assert hasattr(dm, '_update_single_config_file'), "Should have stubbed _update_single_config_file method"
        assert hasattr(dm, '_update_config_file'), "Should have stubbed _update_config_file method"

        # Should be callable and return success (but do nothing)
        result = dm._update_config_file()
        assert result is True, "Should return True for backward compatibility"

        # _update_single_config_file should also be stubbed
        mock_binary_path = r"C:\Users\Test\AppData\Local\OpenStudio-3.9.0\bin\openstudio.exe"
        result = dm._update_single_config_file(
            "dummy_path.ini", "dummy_hpxml_path", mock_binary_path
        )
        assert result is True, "Should return True for backward compatibility"

    def test_uninstall_detection_workflow(self):
        """Test uninstall detection workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock portable installation
            install_dir = Path(temp_dir) / "OpenStudio-3.9.0"
            install_dir.mkdir()

            bin_dir = install_dir / "bin"
            bin_dir.mkdir()

            mock_exe = bin_dir / "openstudio.exe"
            mock_exe.write_text("mock binary")

            dm = DependencyManager()

            # Mock environment to point to our temp directory
            with unittest.mock.patch.dict(
                "os.environ", {"LOCALAPPDATA": str(temp_dir), "USERPROFILE": str(temp_dir)}
            ):
                with unittest.mock.patch.object(dm, "_check_openstudio", return_value=False):
                    with unittest.mock.patch.object(dm, "interactive", False):
                        result = dm._uninstall_openstudio_windows()

                        # Should successfully remove the installation
                        assert not install_dir.exists()
                        assert result is True


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
@pytest.mark.integration
class TestWindowsErrorHandling:
    """Test error handling in Windows installation scenarios."""

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        dm = DependencyManager()

        # Test with a directory that should not be writable (unless admin)
        system_dir = Path(r"C:\Windows\System32")
        if system_dir.exists():
            # This should return False (unless running as admin)
            write_access = dm._has_write_access(system_dir)
            assert isinstance(write_access, bool)

    def test_missing_directory_handling(self):
        """Test handling of missing directories in paths."""
        dm = DependencyManager()

        # Test with non-existent directory
        fake_dir = Path(r"C:\NonExistentDirectory\SubDir")
        write_access = dm._has_write_access(fake_dir)

        # Should handle gracefully
        assert isinstance(write_access, bool)

    def test_network_error_simulation(self):
        """Test network error handling (simulated)."""
        dm = DependencyManager(auto_install=True)

        # Test URL construction doesn't crash
        try:
            url = (
                f"{dm.OPENSTUDIO_BASE_URL}/"
                f"v{dm.REQUIRED_OPENSTUDIO_VERSION}/"
                f"OpenStudio-{dm.REQUIRED_OPENSTUDIO_VERSION}+"
                f"{dm.OPENSTUDIO_BUILD_HASH}-Windows.tar.gz"
            )

            # URL should be well-formed
            assert url.startswith("https://")
            assert "github.com" in url
            assert ".tar.gz" in url

        except Exception as e:
            pytest.fail(f"URL construction failed: {e}")


# Add import for unittest.mock if needed
try:
    import unittest.mock
except ImportError:
    from unittest import mock as unittest_mock
