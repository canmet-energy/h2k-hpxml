"""Build translation config dicts from conversionconfig.ini with optional overrides."""

from __future__ import annotations

from typing import Any

from .manager import ConfigManager
from .translation_modes import normalize_translation_mode


def build_translation_config(
    config_manager: ConfigManager | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge INI defaults with caller overrides for h2ktohpxml().

    Precedence: overrides > conversionconfig.ini > hard defaults (STANDARD/SOC).
    """
    cm = config_manager or ConfigManager()
    config = {
        "translation_mode": cm.translation_mode,
        "operating_condition": cm.operating_condition,
    }
    if overrides:
        if not isinstance(overrides, dict):
            raise TypeError("Translation config overrides must be a dictionary")
        config.update(overrides)
    config["translation_mode"] = normalize_translation_mode(config["translation_mode"])
    return config
