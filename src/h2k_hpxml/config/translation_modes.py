"""Translation mode constants and legacy value normalization."""

from __future__ import annotations

from typing import Callable

VALID_TRANSLATION_MODES = ("STANDARD", "ASHRAE140")


def normalize_translation_mode(
    mode: str,
    warn: Callable[[str], None] | None = None,
) -> str:
    """Map legacy translation mode values to current names."""
    if mode == "SOC":
        if warn is not None:
            warn("Translation mode 'SOC' is deprecated; use 'STANDARD' instead.")
        return "STANDARD"
    return mode
