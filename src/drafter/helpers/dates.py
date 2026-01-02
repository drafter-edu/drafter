from datetime import datetime, time, date
from typing import Any, Union, Optional

def try_convert_datetime(value, target_type) -> tuple[bool, Any]:
    """
    Tries to convert a value to a datetime, date, or time object.
    
    TODO: Allow control over "default" behavior for blank fields. Could raise an error,
          return None, or use current date/time. Currently just uses the current date/time 
          for missing parts.

    :param value: The value to convert.
    :param target_type: The target type (datetime, date, or time).
    :return: A tuple (success: bool, converted_value: Any).
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
            raise ValueError(
                f"Could not convert string '{value}' to {target_type.__name__}. Expected ISO format."
            ) from e

    return False, value