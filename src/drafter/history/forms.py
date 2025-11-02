"""
Form parameter handling and remapping utilities for the Drafter framework.
"""

import json
from typing import Any, Dict
from urllib.parse import unquote

from drafter.constants import LABEL_SEPARATOR, JSON_DECODE_SYMBOL


def extract_button_label(full_key: str):
    """
    Extracts the button namespace and parameter key from a namespaced form parameter.

    :param full_key: The full parameter key that may contain a button namespace
    :return: Tuple of (button_namespace, parameter_key) or (None, full_key) if no namespace
    """
    if LABEL_SEPARATOR not in full_key:
        return None, full_key
    button_pressed, key = full_key.split(LABEL_SEPARATOR, 1)
    button_pressed = json.loads(unquote(button_pressed))
    # Return the full button namespace (including ID) and the parameter key
    # The namespace format is "text#id" where id is the button instance ID
    return button_pressed, key


def add_unless_present(a_dictionary, key, value, from_button=False):
    """
    Adds a key-value pair to a dictionary if the key doesn't already exist.
    Raises an error if the key already exists to prevent parameter collision.

    :param a_dictionary: The dictionary to add to
    :param key: The key to add
    :param value: The value to add
    :param from_button: Whether this parameter came from a button
    :return: The modified dictionary
    """
    if key in a_dictionary:
        base_message = f"Parameter {key!r} with new value {value!r} already exists in {a_dictionary!r}"
        if from_button:
            raise ValueError(
                f"{base_message}. Did you have a button with the same name as another component?"
            )
        else:
            raise ValueError(
                f"{base_message}. Did you have a component with the same name as another component?"
            )
    a_dictionary[key] = value
    return a_dictionary


def remap_hidden_form_parameters(kwargs: dict, button_pressed: str):
    """
    Remaps form parameters by extracting namespaced button arguments and JSON-decoded values.

    :param kwargs: The raw form parameters dict
    :param button_pressed: The namespace of the button that was pressed (e.g., "Button#12345")
    :return: A new dict with remapped and decoded parameters
    """
    renamed_kwargs: Dict[Any, Any] = {}
    for key, value in kwargs.items():
        possible_button_pressed, possible_key = extract_button_label(key)
        if button_pressed and possible_button_pressed == button_pressed:
            try:
                new_value = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Could not decode JSON for {possible_key}={value!r}"
                ) from e
            add_unless_present(
                renamed_kwargs, possible_key, new_value, from_button=True
            )
        elif key.startswith(JSON_DECODE_SYMBOL):
            key = key[len(JSON_DECODE_SYMBOL) :]
            try:
                new_value = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Could not decode JSON for {key}={value!r}") from e
            add_unless_present(renamed_kwargs, key, new_value)
        elif LABEL_SEPARATOR not in key:
            add_unless_present(renamed_kwargs, key, value)
    return renamed_kwargs


def get_params():
    """
    Placeholder for getting request parameters from the bottle framework.
    In the new client-server architecture, this is handled differently.

    :return: Empty dict (deprecated in client-server architecture)
    """
    # This is kept for backwards compatibility with old code
    # In the new client-server architecture, parameters come from the Request object
    return {}
