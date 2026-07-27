"""
Type conversion tracking for debugging and display purposes.
"""

import html
from dataclasses import dataclass
from typing import Any

from drafter.history.utils import safe_repr


@dataclass
class ConversionRecord:
    """
    Records a parameter that was converted from one type to another.

    Attributes:
        parameter: The name of the parameter
        value: The original value before conversion
        expected_type: The type the parameter was expected to be
        converted_value: The value after conversion
    """

    parameter: str
    value: Any
    expected_type: Any
    converted_value: Any

    def as_html(self):
        """
        Returns an HTML representation of the conversion.

        Returns:
            HTML string showing the conversion
        """
        return (
            f"<li><code>{html.escape(self.parameter)}</code>: "
            f"<code>{safe_repr(self.value)}</code> &rarr; "
            f"<code>{safe_repr(self.converted_value)}</code></li>"
        )


@dataclass
class UnchangedRecord:
    """
    Records a parameter that was not converted (already the correct type).

    Attributes:
        parameter: The name of the parameter
        value: The value (unchanged)
        expected_type: The expected type (optional)
    """

    parameter: str
    value: Any
    expected_type: Any = None

    def as_html(self):
        """
        Returns an HTML representation of the unchanged parameter.

        Returns:
            HTML string showing the parameter
        """
        return (
            f"<li><code>{html.escape(self.parameter)}</code>: "
            f"<code>{safe_repr(self.value)}</code></li>"
        )
