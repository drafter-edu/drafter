"""Type definitions for the Python execution engines Drafter supports."""

from typing import Literal

EngineType = Literal["skulpt", "pyodide"]
"""Type alias for the names of the supported in-browser Python execution
engines: "skulpt" or "pyodide"."""
