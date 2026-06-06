"""
Backward-compatibility shim for h2k_hpxml dependency management.

The dependency management code now lives in the standalone, reusable ``osdep``
package (openstudio-deps). This module re-exports osdep's public API so existing
``from h2k_hpxml.utils.dependencies import ...`` imports keep working, and injects
h2k-hpxml's pinned versions globally so every zero-argument helper call resolves to
the versions h2k is built against.
"""

from osdep import DependencyConfig
from osdep import DependencyManager
from osdep import download_file
from osdep import get_default_hpxml_path
from osdep import get_default_openstudio_path
from osdep import get_dependency_paths
from osdep import get_energyplus_binary
from osdep import get_hpxml_os_path
from osdep import get_openstudio_binary
from osdep import get_openstudio_hpxml_path
from osdep import get_openstudio_hpxml_path_static
from osdep import get_openstudio_path
from osdep import get_openstudio_path_static
from osdep import get_openstudio_paths
from osdep import get_user_data_dir
from osdep import resolve_config
from osdep import safe_echo
from osdep import set_default_config
from osdep import validate_dependencies as _validate_dependencies
from osdep import verify_installation

from ._h2k_versions import H2K_CONFIG

# Inject h2k-hpxml's pinned versions globally. After this, every osdep helper that
# resolves config with no explicit override (e.g. the lazy properties in
# h2k_hpxml.config.manager and h2k_hpxml.api) uses H2K_CONFIG.
set_default_config(H2K_CONFIG)


def validate_dependencies(*args, **kwargs):
    """h2k-flavored validate_dependencies: defaults config to h2k's pinned versions."""
    kwargs.setdefault("config", H2K_CONFIG)
    return _validate_dependencies(*args, **kwargs)


def load_dependency_config():
    """Deprecated: return h2k's pinned versions as a dict.

    Retained for backward compatibility with callers that expected the old
    ``load_dependency_config()`` dict. Prefer ``resolve_config()`` /
    ``DependencyConfig`` from osdep.
    """
    return H2K_CONFIG.as_dict()


# The generic os-setup entry point now lives in h2k_hpxml.cli.os_setup. This alias
# is kept so any lingering references to the old entry point still resolve.
def main():
    """Backward-compatible entry point; delegates to the h2k os-setup wrapper."""
    from h2k_hpxml.cli.os_setup import main as _h2k_main

    return _h2k_main()


__all__ = [
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
    "get_openstudio_hpxml_path",
    "get_openstudio_path_static",
    "get_openstudio_hpxml_path_static",
    "load_dependency_config",
    "resolve_config",
    "set_default_config",
    "get_user_data_dir",
    "get_openstudio_paths",
    "get_default_hpxml_path",
    "get_default_openstudio_path",
    "H2K_CONFIG",
]
