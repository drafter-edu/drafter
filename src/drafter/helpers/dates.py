"""Conversion helpers for datetime, date, and time values."""

from datetime import date, datetime, time
from typing import Any

from drafter.data.errors import StudentFacingError


def current_moment(target_type: Any) -> datetime | date | time:
    """The present moment as a datetime, a date, or a time of day.

    This is what a blank date or time field stands for when the route's
    parameter is neither optional nor given a default.

    Args:
        target_type: One of `datetime`, `date`, or `time`.

    Returns:
        Now, in the form of the requested type.

    Raises:
        ValueError: If `target_type` is not one of the three types.
    """
    now = datetime.now()
    if target_type is datetime:
        return now
    if target_type is date:
        return now.date()
    if target_type is time:
        return now.time()
    raise ValueError(f"Expected datetime, date, or time, not {target_type!r}.")


def try_convert_datetime(value, target_type) -> tuple[bool, Any]:
    """Convert a value to datetime-like types if possible.

    A blank string converts to the current date or time. Route parameters
    get more choices for a blank field (None for an optional parameter,
    then the parameter's default); the converter registry applies those
    before this function is reached.

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
            return True, current_moment(target_type)
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
                    "If the value comes from a form, use a DateInput, "
                    "TimeInput, or DateTimeInput so the browser formats it "
                    "for you.",
                ),
            ) from e

    return False, value
