import json

BASE_PARAMETER_ERROR = (
    """The {component_type} name must be a valid Python identifier name. A string is considered """
    """a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or """
    """underscores (_). A valid identifier cannot start with a number, or contain any spaces."""
)
BASE_PARAMETER_ERROR = """The {component_type} value must be a JSON-serializable value (str, int, float, bool, None, list, or dict). """


def validate_parameter_name(name: str, component_type: str):
    """
    Validates a parameter name to ensure it adheres to Python's identifier naming rules.
    The function verifies if the given name is a string, non-empty, does not contain spaces,
    does not start with a digit, and is a valid Python identifier. Additionally, it ensures
    the name starts with a letter or an underscore. Raises a `ValueError` with a detailed
    error message if validation fails.

    Args:
        name (str): The parameter name to validate.
        component_type (str): The type of component for error message context.
    Raises:
        ValueError: If the name is not a valid Python identifier.
    """
    base_error = BASE_PARAMETER_ERROR.format(component_type=component_type)
    if not isinstance(name, str):
        raise ValueError(
            base_error + f"\n\nReason: The given name `{name!r}` is not a string."
        )
    if not name.isidentifier():
        if " " in name:
            raise ValueError(
                base_error
                + f"\n\nReason: The name `{name}` has a space, which is not allowed."
            )
        if not name:
            raise ValueError(base_error + "\n\nReason: The name is an empty string.")
        if name[0].isdigit():
            raise ValueError(
                base_error
                + f"\n\nReason: The name `{name}` starts with a digit, which is not allowed."
            )
        if not name[0].isalpha() and name[0] != "_":
            raise ValueError(
                base_error
                + f"\n\nReason: The name `{name}` does not start with a letter or an underscore."
            )
        raise ValueError(
            base_error + f" The name `{name}` is not a valid Python identifier name."
        )


def validate_json_value(value, component_type: str):
    """
    Recursively validates that a value is JSON-serializable and does not contain any unsupported types.

    Args:
        value: The value to validate.
        component_type: A string describing the type of component for error messages.
    Raises:
        ValueError: If the value is not JSON-serializable or contains unsupported types.
    """
    base_error = BASE_PARAMETER_ERROR.format(component_type=component_type)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_json_value(item, component_type)
    elif isinstance(value, dict):
        for key, val in value.items():
            if not isinstance(key, str):
                raise ValueError(
                    base_error
                    + f"\n\nReason: The dictionary key `{key!r}` is not a string, which is not allowed."
                )
            validate_json_value(val, component_type)
    else:
        raise ValueError(
            base_error
            + f"\n\nReason: Found value of type {type(value)}: {value!r}, which is not JSON-serializable."
        )
