"""
History module for tracking page visits, state, and form parameter handling.
"""

from drafter.history.pages import VisitedPage
from drafter.history.serialization import rehydrate_json, dehydrate_json
from drafter.history.conversion import ConversionRecord, UnchangedRecord
from drafter.history.forms import (
    get_params,
    remap_hidden_form_parameters,
)
from drafter.history.utils import safe_repr


__all__ = [
    "VisitedPage",
    "rehydrate_json",
    "dehydrate_json",
    "ConversionRecord",
    "UnchangedRecord",
    "get_params",
    "remap_hidden_form_parameters",
    "safe_repr",
]
