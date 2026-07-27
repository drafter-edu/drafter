"""Conversion helpers for datetime, date, and time values."""

from datetime import date, datetime, time
from typing import Any

from drafter.data.errors import StudentFacingError


def try_convert_datetime(value, target_type) -> tuple[bool, Any]:
    """Convert a value to datetime-like types if possible.

    TODO: Allow control over "default" behavior for blank fields. Could raise an error,
          return None, or use current date/time. Currently just uses the current date/time
          for missing parts.

    Args:
        value: Arbitrary input to convert.
        target_type: Desired type, one of datetime, date, or time.

    Returns:
        Tuple where the first element indicates success and the second is the converted
        value or original input.

    Raises:
        StudentFacingError: If a string value cannot be parsed as ISO for the target type.
    """
    if target_type not in {datetime, date, time}:
        return False, value

    if isinstance(value, str):
        if not value.strip():
            # Empty string; return current date/time based on target type
            if target_type is datetime:
                return True, datetime.now()
            elif target_type is date:
                return True, date.today()
            elif target_type is time:
                now = datetime.now()
                return True, time(now.hour, now.minute, now.second, now.microsecond)
        try:
            if target_type is datetime:
                return True, datetime.fromisoformat(value)
            elif target_type is date:
                return True, date.fromisoformat(value)
            elif target_type is time:
                return True, time.fromisoformat(value)
        except ValueError as e:
            raise StudentFacingError(
                f"Could not convert string '{value}' to {target_type.__name__}. Expected ISO format.",
                friendly=(
                    f"The text '{value}' is not written in a way Python can "
                    f"read as a {target_type.__name__}."
                ),
                steps=(
                    "Write dates as YYYY-MM-DD (like '2026-07-26') and "
                    "times as HH:MM:SS (like '14:30:00').",
                    "If the value comes from a form, use a TextBox with the "
                    "matching date/time kind so the browser formats it "
                    "for you.",
                ),
            ) from e

    return False, value
