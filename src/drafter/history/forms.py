"""
Form parameter handling and remapping utilities for the Drafter framework.
"""

import json
from typing import Any, Dict

from drafter.constants import JSON_DECODE_SYMBOL


def add_unless_present(a_dictionary, key, value):
    """
    Adds a key-value pair to a dictionary if the key doesn't already exist.
    Raises an error if the key already exists to prevent parameter collision.

    Args:
        a_dictionary: The dictionary to add to
        key: The key to add
        value: The value to add

    Returns:
        The modified dictionary
    """
    if key in a_dictionary:
        raise ValueError(
            f"Parameter {key!r} with new value {value!r} already exists in {a_dictionary!r}. "
            f"Did you have a component with the same name as another component?"
        )
    a_dictionary[key] = value
    return a_dictionary


def remap_hidden_form_parameters(kwargs: dict):
    """
    Remaps form parameters by decoding JSON-prefixed hidden input values.

    Keys prefixed with JSON_DECODE_SYMBOL are stripped and their values
    are JSON-decoded. All other keys pass through as-is.

    Args:
        kwargs: The raw form parameters dict

    Returns:
        A new dict with remapped and decoded parameters
    """
    renamed_kwargs: Dict[Any, Any] = {}
    for key, value in kwargs.items():
        if key.startswith(JSON_DECODE_SYMBOL):
            key = key[len(JSON_DECODE_SYMBOL):]
            print("GOT", repr(key), repr(value))
            try:
                new_value = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Could not decode JSON for {key}={value!r}") from e
            add_unless_present(renamed_kwargs, key, new_value)
        else:
            add_unless_present(renamed_kwargs, key, value)
    return renamed_kwargs


def get_params():
    """
    Placeholder for getting request parameters from the bottle framework.
    In the new client-server architecture, this is handled differently.

    Returns:
        Empty dict (deprecated in client-server architecture)
    """
    # This is kept for backwards compatibility with old code
    # In the new client-server architecture, parameters come from the Request object
    return {}
