"""H2K to HPXML translation package."""

__version__ = "1.7.0.1.1"

# Re-export main translation function for backward compatibility
from .core.h2ktohpxml import h2ktohpxml

__all__ = ["h2ktohpxml"]