"""Validation utilities for component arguments.

Provides functions to validate parameter names and JSON values used in
component arguments and settings. Failures raise `StudentFacingError`,
carrying a concise technical message plus a friendly explanation and fix
steps for the error page.
"""

from drafter.data.errors import StudentFacingError

BASE_PARAMETER_ERROR = (
    """The {component_type} name must be a valid Python identifier name. A string is considered """
    """a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or """
    """underscores (_). A valid identifier cannot start with a number, or contain any spaces."""
)
"""Friendly explanation for invalid component names, formatted with the
`component_type` by `validate_parameter_name`."""

BASE_VALUE_ERROR = """The {component_type} value must be a JSON-serializable value (str, int, float, bool, None, list, or dict). """
"""Friendly explanation for non-JSON-serializable component values,
formatted with the `component_type` by `validate_json_value`."""

_NAME_FIX_STEPS = (
    "Use only letters, digits, and underscores in the name.",
    "Start the name with a letter or an underscore, not a digit.",
    "Replace any spaces in the name with underscores.",
)

_VALUE_FIX_STEPS = (
    "Use only simple data here: text, numbers, True/False, None, lists, and dictionaries.",
    "Convert other objects to text or numbers before passing them in.",
    "Make sure every dictionary key is a string.",
)


def _invalid_name(component_type: str, reason: str) -> StudentFacingError:
    """Build the two-tier error for an invalid component name."""
    return StudentFacingError(
        f"Invalid {component_type} name: {reason}",
        friendly=BASE_PARAMETER_ERROR.format(component_type=component_type),
        steps=_NAME_FIX_STEPS,
    )


def validate_parameter_name(name: str, component_type: str):
    """Validate parameter name as Python identifier.

    Ensures the name follows Python identifier rules: contains only alphanumeric
    characters and underscores, doesn't start with a digit, has no spaces, etc.

    Args:
        name: The parameter name to validate.
        component_type: Component type for error message context.

    Raises:
        StudentFacingError: If name is not a valid Python identifier.
    """
    if not isinstance(name, str):
        raise _invalid_name(
            component_type, f"the given name `{name!r}` is not a string."
        )
    if not name.isidentifier():
        if " " in name:
            raise _invalid_name(
                component_type, f"the name `{name}` has a space, which is not allowed."
            )
        if not name:
            raise _invalid_name(component_type, "the name is an empty string.")
        if name[0].isdigit():
            raise _invalid_name(
                component_type,
                f"the name `{name}` starts with a digit, which is not allowed.",
            )
        if not name[0].isalpha() and name[0] != "_":
            raise _invalid_name(
                component_type,
                f"the name `{name}` does not start with a letter or an underscore.",
            )
        raise _invalid_name(
            component_type,
            f"the name `{name}` is not a valid Python identifier name.",
        )


def validate_json_value(value, component_type: str):
    """Recursively validate value is JSON-serializable.

    Checks that value and all nested structures (lists, dicts) contain only
    JSON-safe types: str, int, float, bool, None, list, dict.

    Args:
        value: The value to validate.
        component_type: Component type for error message context.

    Raises:
        StudentFacingError: If value contains non-JSON-serializable types.
    """
    if isinstance(value, (str, int, float, bool)) or value is None:
        return
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_json_value(item, component_type)
    elif isinstance(value, dict):
        for key, val in value.items():
            if not isinstance(key, str):
                raise StudentFacingError(
                    f"Invalid {component_type} value: the dictionary key "
                    f"`{key!r}` is not a string, which is not allowed.",
                    friendly=BASE_VALUE_ERROR.format(component_type=component_type),
                    steps=_VALUE_FIX_STEPS,
                )
            validate_json_value(val, component_type)
    else:
        raise StudentFacingError(
            f"Invalid {component_type} value: found value of type "
            f"{type(value)}: {value!r}, which is not JSON-serializable.",
            friendly=BASE_VALUE_ERROR.format(component_type=component_type),
            steps=_VALUE_FIX_STEPS,
        )
