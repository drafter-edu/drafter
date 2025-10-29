BASE_PARAMETER_ERROR = (
    """The {component_type} name must be a valid Python identifier name. A string is considered """
    """a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or """
    """underscores (_). A valid identifier cannot start with a number, or contain any spaces."""
)


def validate_parameter_name(name: str, component_type: str):
    """
    Validates a parameter name to ensure it adheres to Python's identifier naming rules.
    The function verifies if the given name is a string, non-empty, does not contain spaces,
    does not start with a digit, and is a valid Python identifier. Additionally, it ensures
    the name starts with a letter or an underscore. Raises a `ValueError` with a detailed
    error message if validation fails.

    :param name: The name to validate.
    :type name: str
    :param component_type: Describes the type of component associated with the parameter.
    :type component_type: str
    :raises ValueError: If `name` is not a string, is empty, contains spaces, starts with a
        digit, does not start with a letter or underscore, or is not a valid identifier.
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
