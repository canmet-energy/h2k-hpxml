"""h2k-hpxml's required OpenStudio / OpenStudio-HPXML versions.

These are injected into the generic ``osdep`` package at import time so that all
dependency path resolution uses the versions h2k-hpxml is built against. The
version values live in ``h2k_hpxml/resources/dependency_versions.json`` (kept in
this package, not in osdep) so h2k can pin them independently of osdep's defaults.
"""

import json
from importlib import resources

from osdep import DependencyConfig


def load_h2k_config():
    """Load h2k-hpxml's pinned versions into a DependencyConfig."""
    with (
        resources.files("h2k_hpxml.resources")
        .joinpath("dependency_versions.json")
        .open(encoding="utf-8") as f
    ):
        data = json.load(f)
    return DependencyConfig.from_dict(data)


H2K_CONFIG = load_h2k_config()
