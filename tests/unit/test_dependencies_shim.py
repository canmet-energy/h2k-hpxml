"""Tests for the h2k_hpxml.utils.dependencies backward-compat shim.

The dependency-management implementation now lives in the standalone ``osdep``
package. This module re-exports osdep's public API and injects h2k-hpxml's pinned
versions globally. These tests lock in that contract.
"""

import osdep
import pytest

from h2k_hpxml.utils import dependencies as shim
from h2k_hpxml.utils.dependencies._h2k_versions import H2K_CONFIG


def test_shim_reexports_public_api():
    """All names h2k code (and external callers) rely on remain importable."""
    for name in [
        "DependencyManager",
        "DependencyConfig",
        "validate_dependencies",
        "verify_installation",
        "main",
        "download_file",
        "safe_echo",
        "get_dependency_paths",
        "get_openstudio_binary",
        "get_hpxml_os_path",
        "get_energyplus_binary",
        "get_openstudio_path",
        "get_openstudio_paths",
        "load_dependency_config",
        "resolve_config",
        "set_default_config",
    ]:
        assert hasattr(shim, name), f"shim missing re-export: {name}"


def test_h2k_versions_match_resource_json():
    """H2K_CONFIG is loaded from h2k_hpxml/resources/dependency_versions.json."""
    import json
    from importlib import resources

    with (
        resources.files("h2k_hpxml.resources")
        .joinpath("dependency_versions.json")
        .open(encoding="utf-8") as f
    ):
        data = json.load(f)

    assert H2K_CONFIG.openstudio_version == data["openstudio_version"]
    assert H2K_CONFIG.openstudio_sha == data["openstudio_sha"]
    assert H2K_CONFIG.openstudio_hpxml_version == data["openstudio_hpxml_version"]


def test_injection_makes_zero_arg_resolution_use_h2k_versions():
    """Importing the shim injects H2K_CONFIG as osdep's module default."""
    # The shim ran set_default_config(H2K_CONFIG) at import time.
    assert osdep.resolve_config().openstudio_version == H2K_CONFIG.openstudio_version
    assert osdep.resolve_config().openstudio_sha == H2K_CONFIG.openstudio_sha


def test_manager_without_config_uses_h2k_versions():
    manager = shim.DependencyManager(interactive=False)
    assert manager.REQUIRED_OPENSTUDIO_VERSION == H2K_CONFIG.openstudio_version
    assert manager.REQUIRED_HPXML_VERSION == H2K_CONFIG.openstudio_hpxml_version
    assert manager.OPENSTUDIO_BUILD_HASH == H2K_CONFIG.openstudio_sha


def test_validate_dependencies_defaults_config_to_h2k(monkeypatch):
    """The shim's validate_dependencies injects config=H2K_CONFIG by default."""
    captured = {}

    def fake_validate(*args, **kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(shim, "_validate_dependencies", fake_validate)
    assert shim.validate_dependencies(check_only=True) is True
    assert captured["config"] is H2K_CONFIG


def test_load_dependency_config_returns_dict():
    cfg = shim.load_dependency_config()
    assert cfg == H2K_CONFIG.as_dict()
    assert cfg["openstudio_version"] == H2K_CONFIG.openstudio_version
