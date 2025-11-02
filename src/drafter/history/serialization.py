"""
JSON serialization and deserialization for state persistence.
"""

import io
from dataclasses import fields, is_dataclass

from drafter.components.utilities.image_support import HAS_PILLOW, PILImage


def image_to_bytes(value):
    """
    Converts a PIL Image to PNG bytes.

    :param value: A PIL Image object
    :return: Bytes representing the image in PNG format
    """
    with io.BytesIO() as output:
        value.save(output, format="PNG")
        return output.getvalue()


def bytes_to_image(value):
    """
    Converts bytes to a PIL Image.

    :param value: Bytes representing an image
    :return: A PIL Image object
    """
    return PILImage.open(io.BytesIO(value))


def dehydrate_json(value, seen=None):
    """
    Converts a Python value to a JSON-serializable format.
    Handles dataclasses, PIL Images, and detects circular references.

    :param value: The value to serialize
    :param seen: Set of already-seen object IDs (for circular reference detection)
    :return: JSON-serializable value
    :raises ValueError: If circular reference detected or unsupported type
    """
    if seen is None:
        seen = set()
    else:
        seen = set(seen)
    if id(value) in seen:
        raise ValueError(
            f"Error while serializing state: Circular reference detected in {value!r}"
        )
    if isinstance(value, (list, set, tuple)):
        seen.add(id(value))
        return [dehydrate_json(v, seen) for v in value]
    elif isinstance(value, dict):
        seen.add(id(value))
        return {
            dehydrate_json(k, seen): dehydrate_json(v, seen) for k, v in value.items()
        }
    elif isinstance(value, (int, str, float, bool)) or value is None:
        return value
    elif is_dataclass(value):
        seen.add(id(value))
        return {
            f.name: dehydrate_json(getattr(value, f.name), seen) for f in fields(value)
        }
    elif HAS_PILLOW and isinstance(value, PILImage.Image):
        return image_to_bytes(value).decode("latin1")
    raise ValueError(
        f"Error while serializing state: The {value!r} is not a int, str, float, bool, list, or dataclass."
    )


def rehydrate_json(value, new_type):
    """
    Converts a JSON-serialized value back to its original Python type.
    Handles type annotations, dataclasses, and PIL Images.

    :param value: The JSON value to deserialize
    :param new_type: The target Python type
    :return: Deserialized value of the target type
    :raises ValueError: If the value cannot be converted to the target type
    """
    if isinstance(value, list):
        if hasattr(new_type, "__args__"):
            element_type = new_type.__args__
            if len(element_type) == 1:
                element_type = element_type[0]
            else:
                raise ValueError(
                    f"Error while restoring state: Could not create {new_type!r} from {value!r}. The element type of the list ({new_type!r}) is not a single type."
                )
            return [rehydrate_json(v, element_type) for v in value]
        elif (
            hasattr(new_type, "__origin__") and getattr(new_type, "__origin__") is list
        ):
            return value
    elif isinstance(value, str):
        if HAS_PILLOW and issubclass(new_type, PILImage.Image):
            return bytes_to_image(value.encode("latin1"))
        return value
    elif isinstance(value, (int, float, bool)) or value is None:
        return value
    elif isinstance(value, dict):
        if hasattr(new_type, "__args__"):
            # Handle typed dictionaries
            key_type, value_type = new_type.__args__
            return {
                rehydrate_json(k, key_type): rehydrate_json(v, value_type)
                for k, v in value.items()
            }
        elif (
            hasattr(new_type, "__origin__") and getattr(new_type, "__origin__") is dict
        ):
            return value
        elif is_dataclass(new_type):
            converted = {
                f.name: rehydrate_json(value[f.name], f.type)
                if f.name in value
                else f.default
                for f in fields(new_type)
            }
            return new_type(**converted)  # type: ignore
        else:
            return value
    # Fall through if an error
    raise ValueError(
        f"Error while restoring state: Could not create {new_type!r} from {value!r}"
    )
