from typing import Any

BASELINE_ATTRS = [
    "id",
    "class",
    "style",
    "title",
    "lang",
    "dir",
    "accesskey",
    "tabindex",
    "value",
    "onclick",
    "ondblclick",
    "onmousedown",
    "onmouseup",
    "onmouseover",
    "onmousemove",
    "onmouseout",
    "onkeypress",
    "onkeydown",
    "onkeyup",
    "onfocus",
    "onblur",
    "onselect",
    "onchange",
    "onsubmit",
    "onreset",
    "onabort",
    "onerror",
    "onload",
    "onunload",
    "onresize",
    "onscroll",
    "accesskey",
    "anchor",
    "role",
    "spellcheck",
    "tabindex",
    # ARIA attributes
    "aria-label",
    "aria-labelledby",
    "aria-hidden",
    "aria-describedby",
    "aria-checked",
    "aria-expanded",
    "aria-controls",
    "aria-required",
    "aria-selected",
    "aria-live",
    "aria-busy",
    "aria-atomic",
    "aria-relevant",
    "aria-modal",
]

ALTERNATIVE_FOR_ATTRIBUTE_NAMES = [
    "for_", "_for", "for_name", "for_element"
]

def remap_attr_styles(attributes: dict) -> tuple[dict, dict]:
    """
    Remaps attributes into styles and attributes dictionaries. This is useful for handling style and class attributes.
    The 'classes' key's vales will be moved to 'class' and joined with a space. Any key prefixed with 'style_' will be
    moved to the styles dictionary. All other keys will be moved to the attributes dictionary.
    Event handlers (keys starting with 'on_') will have their underscores removed to align with HTML attribute naming conventions.

    :param attributes: The attributes to remap
    :return: A tuple of the styles and attributes dictionaries
    """
    styles: dict[str, Any] = {}
    attrs: dict[str, Any] = {}
    # Handle classes keyword
    if "classes" in attributes:
        attributes["class"] = attributes.pop("classes")
        if isinstance(attributes["class"], list):
            attributes["class"] = " ".join(attributes["class"])
    # Handle `for` attribute
    for alt_name in ALTERNATIVE_FOR_ATTRIBUTE_NAMES:
        if alt_name in attributes:
            attributes["for"] = attributes.pop(alt_name)
            break
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