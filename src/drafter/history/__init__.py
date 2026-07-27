"""
History module for tracking page visits, state, and form parameter handling.
"""

from drafter.history.conversion import ConversionRecord, UnchangedRecord
from drafter.history.pages import VisitedPage
from drafter.history.utils import safe_repr

__all__ = [
    "VisitedPage",
    "ConversionRecord",
    "UnchangedRecord",
    "safe_repr",
]
