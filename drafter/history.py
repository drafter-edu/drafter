import json
import html
import base64
import os
import io
from urllib.parse import unquote
from dataclasses import dataclass, is_dataclass, replace, asdict, fields
from dataclasses import field as dataclass_field
from datetime import datetime, UTC as timezone_UTC
from typing import Any, Optional, Callable
import pprint

from drafter.constants import LABEL_SEPARATOR, JSON_DECODE_SYMBOL
from drafter.setup import request
from drafter.testing import DIFF_INDENT_WIDTH
from drafter.image_support import HAS_PILLOW, PILImage


TOO_LONG_VALUE_THRESHOLD = 256

def make_value_expandable(value):
    if isinstance(value, str) and len(value) > TOO_LONG_VALUE_THRESHOLD:
        return f"<span class='expandable'>{value}</span>"
    return value

def value_to_html(value):
    return make_value_expandable(html.escape(repr(value)))

def is_generator(iterable):
    return hasattr(iterable, '__iter__') and not hasattr(iterable, '__len__')


# TODO: If no filename data, then could dump base64 representation or something? tobytes perhaps?

def safe_repr(value: Any, handled=None):
    obj_id = id(value)
    if handled is None:
        handled = set()
    else:
        handled = set(handled)
    if obj_id in handled:
        return f"<strong>Circular Reference</strong>"
    if isinstance(value, (int, float, bool, type(None), str, bytes, complex, bytearray)):
        return make_value_expandable(html.escape(repr(value)))
    if isinstance(value, list):
        handled.add(obj_id)
        return f"[{', '.join(safe_repr(v, handled) for v in value)}]"
    if isinstance(value, dict):
        handled.add(obj_id)
        return f"{{{', '.join(f'{safe_repr(k, handled)}: {safe_repr(v, handled)}' for k, v in value.items())}}}"
    if is_dataclass(value):
        handled.add(obj_id)
        fields_repr = ', '.join(f'{f.name}={safe_repr(getattr(value, f.name), handled)}' for f in fields(value))
        return f"{value.__class__.__name__}({fields_repr})"
    if isinstance(value, set):
        handled.add(obj_id)
        return f"{{{', '.join(safe_repr(v, handled) for v in value)}}}"
    if isinstance(value, tuple):
        handled.add(obj_id)
        return f"({', '.join(safe_repr(v, handled) for v in value)})"
    if isinstance(value, (frozenset, range, )):
        handled.add(obj_id)
        args_repr = ', '.join(safe_repr(v, handled) for v in value)
        return f"{value.__class__.__name__}({{{args_repr}}})"

    if HAS_PILLOW and isinstance(value, PILImage.Image):
        return repr_pil_image(value)

    # TODO: How should we handle custom things like dict_keys, numpy arrays, etc?

    # TODO: Handle the recursive case of a list/dictionary/dataclass with images inside
    return make_value_expandable(html.escape(repr(value)))



def repr_pil_image(value):
    from drafter.server import get_server_setting
    filename = value.filename if hasattr(value, 'filename') else None
    if not filename:
        # TODO: Make sure that the imports are provided to the student
        image_data = base64.b64encode(image_to_bytes(value)).decode('latin1')
        image_src = f"data:image/png;base64,{image_data}"
        escaped_data = json.dumps(image_data)
        full_call = f"Image.open(io.BytesIO(base64.b64decode({escaped_data}.encode(\"latin1\"))))"
        return f"<img src={image_src} alt='{full_call}' />"
    try:
        # If the file does not already exist, persist it to the image folder
        print("Folder:", get_server_setting("src_image_folder"))
        print("Filename:", filename)
        full_path = os.path.join(get_server_setting("src_image_folder"), filename)
        if get_server_setting("save_uploaded_files"):
            if not os.path.exists(full_path):
                value.save(full_path)
    except Exception as e:
        print(f"Could not save {value!r} because", e)
        return f"Image.open('?')"
    try:
        escaped_name = json.dumps(full_path)
        return f"<img src={escaped_name} alt='Image.open({escaped_name})' />"
    except AttributeError as e:
        print(f"Could not get filename for {value!r} because", e)
        return f"Image.open('?')"


@dataclass
class ConversionRecord:
    parameter: str
    value: Any
    expected_type: Any
    converted_value: Any

    def as_html(self):
        return (f"<li><code>{html.escape(self.parameter)}</code>: "
                f"<code>{safe_repr(self.value)}</code> &rarr; "
                f"<code>{safe_repr(self.converted_value)}</code></li>")

@dataclass
class UnchangedRecord:
    parameter: str
    value: Any
    expected_type: Any = None

    def as_html(self):
        return (f"<li><code>{html.escape(self.parameter)}</code>: "
                f"<code>{safe_repr(self.value)}</code></li>")

try:
    pprint.PrettyPrinter
except:
    class PrettyPrinter:
        def __init__(self, indent, width, *args, **kwargs):
            self.indent = indent
            self.width = width
        def pformat(self, obj):
            return pprint.pformat(obj, indent=self.indent, width=self.width)

    pprint.PrettyPrinter = PrettyPrinter  # type: ignore


class CustomPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if HAS_PILLOW and isinstance(object, PILImage.Image):
            return repr_pil_image(object), True, False
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

def format_page_content(content, width=80):
    try:
        custom_pretty_printer = CustomPrettyPrinter(indent=DIFF_INDENT_WIDTH, width=width)
        return custom_pretty_printer.pformat(content)
    except Exception as e:
        return safe_repr(content)


def extract_button_label(full_key: str):
    if LABEL_SEPARATOR not in full_key:
        return full_key, None
    button_pressed, key = full_key.split(LABEL_SEPARATOR, 1)
    button_pressed = json.loads(unquote(button_pressed))
    return button_pressed, key


def remap_hidden_form_parameters(kwargs: dict, button_pressed: str):
    renamed_kwargs = {}
    for key, value in kwargs.items():
        possible_button_pressed, possible_key = extract_button_label(key)
        if button_pressed and possible_button_pressed == button_pressed:
            try:
                renamed_kwargs[possible_key] = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Could not decode JSON for {possible_key}={value!r}") from e
        elif key.startswith(JSON_DECODE_SYMBOL):
            key = key[len(JSON_DECODE_SYMBOL):]
            try:
                renamed_kwargs[key] = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Could not decode JSON for {key}={value!r}") from e
        elif LABEL_SEPARATOR not in key:
            renamed_kwargs[key] = value
    return renamed_kwargs


@dataclass
class VisitedPage:
    url: str
    function: Callable
    arguments: str
    status: str
    button_pressed: str
    original_page_content: Optional[str] = None
    old_state: Any = None
    started: datetime = dataclass_field(default_factory=lambda:datetime.now(timezone_UTC))
    stopped: Optional[datetime] = None

    def update(self, new_status, original_page_content=None):
        self.status = new_status
        if original_page_content is not None:
            self.original_page_content = html.escape(format_page_content(original_page_content, 120))

    def finish(self, new_status):
        self.status = new_status
        self.stopped = datetime.now(timezone_UTC)

    def as_html(self):
        function_name = self.function.__name__
        return (f"<strong>Current Route:</strong><br>Route function: <code>{function_name}</code><br>"
                f"URL: <href='{self.url}'><code>{self.url}</code></href>")

def dehydrate_json(value, seen=None):
    if seen is None:
        seen = set()
    else:
        seen = set(seen)
    if id(value) in seen:
        raise ValueError(f"Error while serializing state: Circular reference detected in {value!r}")
    if isinstance(value, (list, set, tuple)):
        seen.add(id(value))
        return [dehydrate_json(v, seen) for v in value]
    elif isinstance(value, dict):
        seen.add(id(value))
        return {dehydrate_json(k, seen): dehydrate_json(v, seen)
                for k, v in value.items()}
    elif isinstance(value, (int, str, float, bool)) or value == None:
        return value
    elif is_dataclass(value):
        seen.add(id(value))
        return {f.name: dehydrate_json(getattr(value, f.name), seen)
                for f in fields(value)}
    elif HAS_PILLOW and isinstance(value, PILImage.Image):
        return image_to_bytes(value).decode('latin1')
    raise ValueError(
        f"Error while serializing state: The {value!r} is not a int, str, float, bool, list, or dataclass.")


def image_to_bytes(value):
    with io.BytesIO() as output:
        value.save(output, format='PNG')
        return output.getvalue()

def bytes_to_image(value):
    return PILImage.open(io.BytesIO(value))




def rehydrate_json(value, new_type):
    # TODO: More validation that the structure is consistent; what if the target is not these?
    if isinstance(value, list):
        if hasattr(new_type, '__args__'):
            element_type = new_type.__args__
            if len(element_type) == 1:
                element_type = element_type[0]
            else:
                raise ValueError(f"Error while restoring state: Could not create {new_type!r} from {value!r}. The element type of the list ({new_type!r}) is not a single type.")
            return [rehydrate_json(v, element_type) for v in value]
        elif hasattr(new_type, '__origin__') and getattr(new_type, '__origin__') == list:
            return value
    elif isinstance(value, str):
        if HAS_PILLOW and issubclass(new_type, PILImage.Image):
            return bytes_to_image(value.encode('latin1'))
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
        else:
            return value
    # Fall through if an error
    raise ValueError(f"Error while restoring state: Could not create {new_type!r} from {value!r}")


def get_params():
    params = request.params
    if hasattr(params, 'decode'):
        params = params.decode('utf-8')
    for file_object in request.files:
        params[file_object] = request.files[file_object]
    return params
