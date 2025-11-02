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

    :ivar parameter: The name of the parameter
    :ivar value: The original value before conversion
    :ivar expected_type: The type the parameter was expected to be
    :ivar converted_value: The value after conversion
    """

    parameter: str
    value: Any
    expected_type: Any
    converted_value: Any

    def as_html(self):
        """
        Returns an HTML representation of the conversion.

        :return: HTML string showing the conversion
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

    :ivar parameter: The name of the parameter
    :ivar value: The value (unchanged)
    :ivar expected_type: The expected type (optional)
    """

    parameter: str
    value: Any
    expected_type: Any = None

    def as_html(self):
        """
        Returns an HTML representation of the unchanged parameter.

        :return: HTML string showing the parameter
        """
        return (
            f"<li><code>{html.escape(self.parameter)}</code>: "
            f"<code>{safe_repr(self.value)}</code></li>"
        )
