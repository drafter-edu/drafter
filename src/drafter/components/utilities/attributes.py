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