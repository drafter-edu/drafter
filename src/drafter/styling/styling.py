"""Helper functions for styling PageContent components.

Provides convenience wrappers that update a component's CSS styles or HTML
attributes and return the component, so calls can be chained inline when
building a page. Includes text styling helpers (`bold`, `italic`,
`underline`, `strikethrough`, `monospace`, font/size/color changes), layout
helpers (`float_left`, `float_right`, sizing, border/margin/padding), and
the general-purpose `update_style` and `update_attr` primitives that the
other helpers are built on.

Each helper also accepts a plain string (which is wrapped in a new Text
component) or a list of components (each element is updated).
"""

# Ideas for additional helpers, not yet implemented:
# - indent
# - center
# - superscript, subscript
# - border/margin/padding for individual sides


from drafter.components import PageContent, Text


def update_style(component: PageContent, style: str, value: str) -> PageContent:
    """
    Updates the style of a component, returning the component (allowing you to chain calls).
    The ``style`` property should match the CSS property name.
    Remember to include units in the ``value`` if they are expected!

    Example style properties include:
    - color
    - background-color
    - font-size

    Args:
        component: The component to update. May also be a string (which is
            wrapped in a new Text component) or a list of components (each
            element is updated).
        style: The name of the style property to change
        value: The value to set the style property to (should be a string).

    Returns:
        The updated component. If a component was given, the original
        component is updated in place and returned. If a string was given,
        a new Text component wrapping it is returned. If a list was given,
        a new list of the updated elements is returned.
    """
    if isinstance(component, str):
        component = Text(component)
    # TODO: Consider this approach
    if isinstance(component, list):
        modified = []
        for i in range(len(component)):
            modified.append(update_style(component[i], style, value))
        return modified
    return component.update_style(style, value)


def update_attr(component: PageContent, attr: str, value: str) -> PageContent:
    """
    Updates the attribute of a component, returning the component (allowing you to chain calls).
    The ``attr`` property should match the HTML attribute name.

    Example attributes include:
    - id
    - class
    - title

    Args:
        component: The component to update. May also be a string (which is
            wrapped in a new Text component) or a list of components (each
            element is updated).
        attr: The name of the attribute to change
        value: The value to set the attribute to (should be a string).

    Returns:
        The updated component. If a component was given, the original
        component is updated in place and returned. If a string was given,
        a new Text component wrapping it is returned. If a list was given,
        a new list of the updated elements is returned.
    """
    if isinstance(component, str):
        component = Text(component)
    if isinstance(component, list):
        modified = []
        for i in range(len(component)):
            modified.append(update_attr(component[i], attr, value))
        return modified
    return component.update_attr(attr, value)


def float_right(component: PageContent) -> PageContent:
    """
    Floats the component to the right.

    Args:
        component: The component to float right

    Returns:
        The original component (updated)
    """
    return update_style(component, "float", "right")


def float_left(component: PageContent) -> PageContent:
    """
    Floats the component to the left.

    Args:
        component: The component to float left

    Returns:
        The original component (updated)
    """
    return update_style(component, "float", "left")


def bold(component: PageContent) -> PageContent:
    """
    Applies bold font weight to a component.

    Args:
        component: The component to make bold.

    Returns:
        The original component (updated).
    """
    return update_style(component, "font-weight", "bold")


def italic(component: PageContent) -> PageContent:
    """
    Applies italic font style to a component.

    Args:
        component: The component to italicize.

    Returns:
        The original component (updated).
    """
    return update_style(component, "font-style", "italic")


def underline(component: PageContent) -> PageContent:
    """
    Applies underline text decoration to a component.

    Args:
        component: The component to underline.

    Returns:
        The original component (updated).
    """
    return update_style(component, "text-decoration", "underline")


def strikethrough(component: PageContent) -> PageContent:
    """
    Applies strikethrough (line-through) text decoration to a component.

    Args:
        component: The component to strike through.

    Returns:
        The original component (updated).

    Example:
        `strikethrough(Text("Old price: $20"))`
    """
    return update_style(component, "text-decoration", "line-through")


def monospace(component: PageContent) -> PageContent:
    """
    Applies a monospace font family to a component.

    Args:
        component: The component to display in a monospace font.

    Returns:
        The original component (updated).

    Example:
        `monospace(Text("x = 5"))`
    """
    return update_style(component, "font-family", "monospace")


def small_font(component: PageContent) -> PageContent:
    """
    Sets a component's font size to the browser's built-in "small" size.

    Args:
        component: The component to shrink.

    Returns:
        The original component (updated).

    Example:
        `small_font(Text("Some fine print"))`
    """
    return update_style(component, "font-size", "small")


def large_font(component: PageContent) -> PageContent:
    """
    Sets a component's font size to the browser's built-in "large" size.

    Args:
        component: The component to enlarge.

    Returns:
        The original component (updated).

    Example:
        `large_font(Text("Welcome!"))`
    """
    return update_style(component, "font-size", "large")


def change_color(component: PageContent, c: str) -> PageContent:
    """
    Changes the text color of a component.

    Args:
        component: The component to recolor.
        c: The new text color, as a CSS color (e.g., `"red"`, `"#ff0000"`,
            or `"rgb(255, 0, 0)"`).

    Returns:
        The original component (updated).

    Example:
        `change_color(Text("Hi"), "red")`
    """
    return update_style(component, "color", c)


def change_background_color(component: PageContent, color: str) -> PageContent:
    """
    Changes the background color of a component.

    Args:
        component: The component to recolor.
        color: The new background color, as a CSS color (e.g., `"yellow"`
            or `"#ffff00"`).

    Returns:
        The original component (updated).

    Example:
        `change_background_color(Text("Hi"), "yellow")`
    """
    return update_style(component, "background-color", color)


def change_text_size(component: PageContent, size: str | int) -> PageContent:
    """
    Changes the font size of a component.

    Args:
        component: The component to resize.
        size: The new font size. An integer is treated as pixels (`20`
            becomes `"20px"`); a string is used as-is and should include
            units (e.g., `"1.5em"`).

    Returns:
        The original component (updated).

    Example:
        `change_text_size(Text("Hi"), 20)`
    """
    if isinstance(size, int):
        size = f"{size}px"
    return update_style(component, "font-size", size)


def change_text_font(component: PageContent, font: str) -> PageContent:
    """
    Changes the font family of a component.

    Args:
        component: The component whose font should change.
        font: The new font family (e.g., `"Arial"` or `"serif"`).

    Returns:
        The original component (updated).

    Example:
        `change_text_font(Text("Hi"), "Arial")`
    """
    return update_style(component, "font-family", font)


def change_text_align(component: PageContent, align: str) -> PageContent:
    """
    Changes the horizontal text alignment of a component.

    Args:
        component: The component to align.
        align: The new alignment: `"left"`, `"center"`, `"right"`, or
            `"justify"`.

    Returns:
        The original component (updated).

    Example:
        `change_text_align(Text("Hi"), "center")`
    """
    return update_style(component, "text-align", align)


def change_text_decoration(component: PageContent, decoration: str) -> PageContent:
    """
    Changes the text decoration of a component.

    Args:
        component: The component to decorate.
        decoration: The new decoration (e.g., `"underline"`,
            `"line-through"`, `"overline"`, or `"none"`).

    Returns:
        The original component (updated).

    Example:
        `change_text_decoration(Text("Hi"), "underline")`
    """
    return update_style(component, "text-decoration", decoration)


def change_text_transform(component: PageContent, transform: str) -> PageContent:
    """
    Changes the capitalization (text transform) of a component.

    Args:
        component: The component to transform.
        transform: The new transform: `"uppercase"`, `"lowercase"`,
            `"capitalize"`, or `"none"`.

    Returns:
        The original component (updated).

    Example:
        `change_text_transform(Text("Hi"), "uppercase")`
    """
    return update_style(component, "text-transform", transform)


def change_height(component: PageContent, height: str) -> PageContent:
    """
    Changes the height of a component.

    Args:
        component: The component to resize.
        height: The new height, including units (e.g., `"100px"` or
            `"50%"`).

    Returns:
        The original component (updated).

    Example:
        `change_height(Image("dog.png"), "100px")`
    """
    return update_style(component, "height", height)


def change_width(component: PageContent, width: str) -> PageContent:
    """
    Changes the width of a component.

    Args:
        component: The component to resize.
        width: The new width, including units (e.g., `"200px"` or
            `"50%"`).

    Returns:
        The original component (updated).

    Example:
        `change_width(Image("dog.png"), "200px")`
    """
    return update_style(component, "width", width)


def change_border(component: PageContent, border: str) -> PageContent:
    """
    Changes the border of a component.

    Args:
        component: The component to give a border.
        border: The new border, as CSS border shorthand (width, style,
            and color, e.g., `"1px solid black"`).

    Returns:
        The original component (updated).

    Example:
        `change_border(Text("Hi"), "1px solid black")`
    """
    return update_style(component, "border", border)


def change_margin(component: PageContent, margin: str) -> PageContent:
    """
    Changes the margin (space outside the border) of a component.

    Args:
        component: The component to space out.
        margin: The new margin, including units (e.g., `"10px"`); CSS
            shorthand with per-side values also works (e.g.,
            `"10px 20px"`).

    Returns:
        The original component (updated).

    Example:
        `change_margin(Text("Hi"), "10px")`
    """
    return update_style(component, "margin", margin)


def change_padding(component: PageContent, padding: str) -> PageContent:
    """
    Changes the padding (space inside the border) of a component.

    Args:
        component: The component to pad.
        padding: The new padding, including units (e.g., `"10px"`); CSS
            shorthand with per-side values also works (e.g.,
            `"10px 20px"`).

    Returns:
        The original component (updated).

    Example:
        `change_padding(Text("Hi"), "10px")`
    """
    return update_style(component, "padding", padding)
