import json
import base64
import io
from dataclasses import dataclass, is_dataclass, replace, asdict, fields
from dataclasses import field as dataclass_field
from datetime import datetime
from typing import Any
import pprint

from drafter.constants import LABEL_SEPARATOR, JSON_DECODE_SYMBOL
from drafter.setup import request
from drafter.testing import DIFF_INDENT_WIDTH
from drafter.image_support import HAS_PILLOW, PILImage

@dataclass
class ConversionRecord:
    parameter: str
    value: Any
    expected_type: Any
    converted_value: Any

    def as_html(self):
        return (f"<li><code>{self.parameter}</code>: "
                f"<code>{self.value!r}</code> &rarr; "
                f"<code>{self.converted_value!r}</code></li>")

@dataclass
class UnchangedRecord:
    parameter: str
    value: Any
    expected_type: Any = None

    def as_html(self):
        return (f"<li><code>{self.parameter}</code>: "
                f"<code>{self.value!r}</code></li>")


def format_page_content(content, width=80):
    try:
        return pprint.pformat(content, indent=DIFF_INDENT_WIDTH, width=width)
    except Exception as e:
        return repr(content)


def remap_hidden_form_parameters(kwargs: dict, button_pressed: str):
    renamed_kwargs = {}
    for key, value in kwargs.items():
        if button_pressed and key.startswith(f"{button_pressed}{LABEL_SEPARATOR}"):
            key = key[len(f"{button_pressed}{LABEL_SEPARATOR}"):]
            renamed_kwargs[key] = json.loads(value)
        elif key.startswith(JSON_DECODE_SYMBOL):
            key = key[len(JSON_DECODE_SYMBOL):]
            renamed_kwargs[key] = json.loads(value)
        elif LABEL_SEPARATOR not in key:
            renamed_kwargs[key] = value
    return renamed_kwargs


@dataclass
class VisitedPage:
    url: str
    function: callable
    arguments: str
    status: str
    button_pressed: str
    original_page_content: str = None
    old_state: Any = None
    started: datetime = dataclass_field(default_factory=datetime.utcnow)
    stopped: datetime = None

    def update(self, new_status, original_page_content=None):
        self.status = new_status
        if original_page_content is not None:
            self.original_page_content = format_page_content(original_page_content, 120)

    def finish(self, new_status):
        self.status = new_status
        self.stopped = datetime.utcnow()

    def as_html(self):
        function_name = self.function.__name__
        return (f"<strong>Current Route:</strong><br>Route function: <code>{function_name}</code><br>"
                f"URL: <href='{self.url}'><code>{self.url}</code></href>")

def dehydrate_json(value):
    if isinstance(value, (list, set, tuple)):
        return [dehydrate_json(v) for v in value]
    elif isinstance(value, dict):
        return {dehydrate_json(k): dehydrate_json(v) for k, v in value.items()}
    elif isinstance(value, (int, str, float, bool)) or value == None:
        return value
    elif is_dataclass(value):
        return {f.name: dehydrate_json(getattr(value, f.name))
                for f in fields(value)}
    elif HAS_PILLOW and isinstance(value, PILImage.Image):
        return value.tobytes().decode('latin1')
    raise ValueError(
        f"Error while serializing state: The {value!r} is not a int, str, float, bool, list, or dataclass.")


def rehydrate_json(value, new_type):
    # TODO: More validation that the structure is consistent; what if the target is not these?
    if isinstance(value, list):
        if hasattr(new_type, '__args__'):
            element_type = new_type.__args__
            return [rehydrate_json(v, element_type) for v in value]
        elif hasattr(new_type, '__origin__') and getattr(new_type, '__origin__') == list:
            return value
    elif isinstance(value, str):
        if HAS_PILLOW and issubclass(new_type, PILImage):
            return PILImage.open(io.BytesIO(value.encode('latin1')))
        return value
    elif isinstance(value, (int, float, bool)) or value is None:
        return value
    elif isinstance(value, dict):
        if hasattr(new_type, '__args__'):
            # TODO: Handle various kinds of dictionary types more intelligently
            # In particular, should be able to handle dict[int: str] (slicing) and dict[int, str]
            key_type, value_type = new_type.__args__
            return {rehydrate_json(k, key_type): rehydrate_json(v, value_type)
                    for k, v in value.items()}
        elif hasattr(new_type, '__origin__') and getattr(new_type, '__origin__') == dict:
            return value
        elif is_dataclass(new_type):
            converted = {f.name: rehydrate_json(value[f.name], f.type) if f.name in value else f.default
                         for f in fields(new_type)}
            return new_type(**converted)
    # Fall through if an error
    raise ValueError(f"Error while restoring state: Could not create {new_type!r} from {value!r}")


def get_params():
    if hasattr(request.params, 'decode'):
        return request.params.decode('utf-8')
    else:
        return request.params