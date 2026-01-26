"""HTML attribute utilities and constants.

Provides baseline HTML attributes, boolean attribute lists, attribute enumerations,
and functions for remapping and parsing extra settings into valid HTML attributes
and inline styles.
"""

import html
from typing import Any

BASELINE_ATTRS = [
    "accesskey",
    "anchor",
    # ARIA attributes
    "aria-atomic",
    "aria-busy",
    "aria-checked",
    "aria-controls",
    "aria-describedby",
    "aria-expanded",
    "aria-hidden",
    "aria-label",
    "aria-labelledby",
    "aria-live",
    "aria-modal",
    "aria-relevant",
    "aria-required",
    "aria-selected",
    #
    "autocapitalize",
    "autocorrect",
    "autofocus",
    "class",
    "contenteditable",
    "dir",
    "draggable",
    "enterkeyhint",
    "exportparts",
    "hidden",
    "id",
    "inert",
    "inputmode",
    "itemid",
    "itemprop",
    "itemref",
    "itemscope",
    "itemtype",
    "lang",
    "nonce",
    # Event handlers
    "onabort",
    "onblur",
    "onchange",
    "onclick",
    "ondblclick",
    "onerror",
    "onfocus",
    "onkeydown",
    "onkeypress",
    "onkeyup",
    "onload",
    "onmousedown",
    "onmousemove",
    "onmouseout",
    "onmouseover",
    "onmouseup",
    "onreset",
    "onresize",
    "onscroll",
    "onselect",
    "onsubmit",
    "onunload",
    # Other common attributes
    "part",
    "popover",
    "role",
    "slot",
    "spellcheck",
    "style",
    "tabindex",
    "title",
    # "translate", # Deprecate for now to avoid conflicts with style
    "value",
    "writingsuggestions",
]

BOOLEAN_ATTRS = [
    "disabled",
    "checked",
    "readonly",
    "multiple",
    "required",
    "autofocus",
    "autoplay",
    "controls",
    "loop",
    "muted",
    "novalidate",
    "formnovalidate",
    "open",
    "reversed",
    "async",
    "defer",
    "hidden",
    "selected",
    "autocomplete",
    "inert",
]

# All strings are case insensitive
# Doubles as checking the valid values for certain attributes
DEFAULT = object()
ATTRIBUTE_ENUMERATIONS = {
    "autocapitalize": {
        DEFAULT: "sentences",
        "none": "none",
        "off": "off",
        None: "none",
        "on": "on",
        False: "off",
        True: "on",
        "sentences": "sentences",
        "words": "words",
        "characters": "characters",
    },
    "autocorrect": {
        DEFAULT: "on",
        "on": "on",
        "": "on",
        True: "on",
        "off": "off",
        False: "off",
        None: "off",
    },
    "draggable": {
        DEFAULT: "auto",
        None: "auto",
        True: "true",
        False: "false",
        "true": "true",
        "false": "false",
    },
}


def remap_attr_styles(attributes: dict) -> tuple[dict, dict]:
    """Remap attribute dict into separate styles and attributes dicts.

    Processes special attribute keys:
    - 'classes': Joined with spaces and mapped to 'class' attribute
    - 'style_*' prefixed keys: Moved to styles dict (prefix removed)
    - 'on_*' prefixed keys: Underscores removed for HTML event handlers
    - Other keys: Underscores converted to hyphens for CSS properties

    Args:
        attributes: The attributes dict to remap.

    Returns:
        Tuple of (styles_dict, attributes_dict).
    """
    styles: dict[str, Any] = {}
    attrs: dict[str, Any] = {}
    # Handle classes keyword
    if "classes" in attributes:
        attributes["class"] = attributes.pop("classes")
        if isinstance(attributes["class"], list):
            attributes["class"] = " ".join(attributes["class"])
    # Handle styles_ prefixed keyword
    for key, value in attributes.items():
        target = attrs
        if key.startswith("style_"):
            key = key[len("style_") :]
            target = styles
        # Convert underscores to hyphens except for event handlers
        # @acbart: There are no css properties that start with "on_"
        # https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties
        if key.startswith("on_"):
            key = key.replace("_", "")
        else:
            key = key.replace("_", "-")
        target[key] = value
    # All done
    return styles, attrs


def parse_extra_settings(extra_settings, known_attrs, component_id):
    """Parse and format extra settings into HTML attributes and inline styles.

    Validates attribute names and types, handles boolean attributes, enumerations,
    and converts unknown attributes to inline styles. Ensures component ID is included.

    Args:
        extra_settings: Dict of attribute/style settings.
        known_attrs: List of recognized attribute names.
        component_id: Optional component ID to include.

    Returns:
        Space-separated string of formatted HTML attributes and inline style.

    Raises:
        ValueError: If an enumerated attribute has an invalid value.
    """
    if known_attrs is None:
        known_attrs = []
    raw_styles, raw_attrs = remap_attr_styles(extra_settings)
    styles, attrs = [], []
    seen_attrs = set()
    # Preprocess attributes and styles
    for key, value in raw_attrs.items():
        # Check for data-* attributes
        is_data_attr = key.startswith("data-")
        # Check if known attribute
        is_known_attr = key in known_attrs or key in BASELINE_ATTRS

        if not is_data_attr and not is_known_attr:
            # If not a data-* or known attribute, assume it is a style
            styles.append(f"{key}: {value}")
        else:
            # Handle boolean attributes
            if key in BOOLEAN_ATTRS:
                if value:
                    attrs.append(f"{key}")
                    seen_attrs.add(key)
                continue
            # Handle specially enumerated attributes
            elif key in ATTRIBUTE_ENUMERATIONS:
                enum_map = ATTRIBUTE_ENUMERATIONS[key]
                if value not in enum_map:
                    raise ValueError(
                        f"Invalid value '{value}' for attribute '{key}'. "
                        f"Valid values are: {list(enum_map.keys())}"
                    )
                if isinstance(value, str):
                    value = value.lower()
                value = enum_map[value]
            # Otherwise handle regular attribute
            escaped_value = html.escape(str(value), quote=True)
            attrs.append(f'{key}="{escaped_value}"')
            seen_attrs.add(key)
    # Ensure component ID is included
    if "id" not in seen_attrs and component_id is not None:
        attrs.append(f'id="{component_id}"')
    # Now handle styles
    for key, value in raw_styles.items():
        styles.append(f"{key}: {value}")
    if styles:
        attrs.append(f'style="{"; ".join(sorted(styles))}"')
    return " ".join(sorted(attrs))
