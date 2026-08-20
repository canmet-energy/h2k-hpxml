"""Configuration management for H2K-HPXML package."""

from .manager import ConfigManager
from .translation_config import build_translation_config

__all__ = ["ConfigManager", "build_translation_config"]
