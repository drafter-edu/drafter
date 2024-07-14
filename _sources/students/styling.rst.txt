.. _styling:

Styling
=======

Styling Functions
-----------------

One of the easiest ways to apply styling to components is to use the
styling functions available. These functions take a component and return
the same component, but with additional styling applied.

.. code-block:: python

    def index(state: State) -> Page:
        return Page(state, [
            float_right(Button("Quit", index))
        ])


The above example shows how to use the ``float_right`` function to make
the button align on the right hand side of the screen.

The following functions are available:

.. function:: float_left(component)

    Makes the component "float" to the left, allowing other components to wrap around it.

.. function:: float_right(component)

    Makes the component "float" to the right, so that it aligns to the right side of the screen.

.. function:: bold(component)

    Makes the text bold (increasing the font weight and making it darker). Usually used to indicate importance.

.. function:: italic(component)

    Makes the text italic (slanted to the right). Usually used to indicate emphasis.

.. function:: underline(component)

    Adds an underline to the text. Usually used to indicate that the text is a link, so use sparingly.

.. function:: strikethrough(component)

    Adds a line through the text. Usually used to indicate that the text is no longer relevant.

.. function:: monospace(component)

    Changes the font to a monospace font (all the characters will be the same width). Usually used to indicate that the text is code.

.. function:: small_font(component)

    Makes the font size smaller. Usually used for less important text.

.. function:: large_font(component)

    Makes the font size larger. Usually used for more important text. Consider using a header instead.

.. function:: change_color(component, color)

    Changes the text color. The color can be a named color (e.g. "red") or a hex code (e.g. "#FF0000").
    See the `colors`_ page for available HTML colors.

    :param color: The color to change the text to.
    :type color: str

.. function:: change_background_color(component, color)

    Changes the background color of the component (the ``background-color`` CSS attribute). The color can be a named color (e.g. "red") or a hex code (e.g. "#FF0000").
    See the `colors`_ page for available HTML colors.

    :param color: The color to change the background to.
    :type color: str


.. function:: change_text_size(component, size)

    Changes the text size. The size must be a string followed by the units (e.g. "16px") or an integer (e.g. 16).
    If an integer is given, the units are assumed to be pixels. Valid units are:

    * px: Pixels
    * em: Relative to the font size of the element
    * rem: Relative to the font size of the root element
    * %: Percentage of the parent element's font size

    :param size: The size to change the text to.
    :type size: int or str

.. function:: change_text_font(component, font)

    Changes the font of the text. The font must be a valid font name (e.g. ``"Arial"``, ``"Times New Roman"``, ``"Courier New"``).
    See the `fonts`_ page for available fonts.

    :param font: The font to change the text to.
    :type font: str

.. function:: change_text_align(component, alignment)

    Changes the text alignment. The alignment must be one of the following:

    * ``left``: Aligns the text to the left
    * ``right``: Aligns the text to the right
    * ``center``: Centers the text
    * ``justify``: Justifies the text (evenly spaces the words)

    :param alignment: The alignment to change the text to.
    :type alignment: str

.. function:: change_text_decoration(component, decoration)

    Changes the text decoration. The decoration must be one of the following:

    * ``none``: No decoration
    * ``underline``: Adds an underline
    * ``overline``: Adds a line over the text
    * ``line-through``: Adds a line through the text

    :param decoration: The decoration to change the text to.
    :type decoration: str

.. function:: change_text_transform(component, transform)

    Changes the text transformation. The transformation must be one of the following:

    * ``none``: No transformation
    * ``uppercase``: Converts the text to uppercase
    * ``lowercase``: Converts the text to lowercase
    * ``capitalize``: Capitalizes the first letter of each word

    :param transform: The transformation to change the text to.
    :type transform: str

.. function:: change_margin(component, margin)

    Changes the margin of the component. The margin is the space around the component (as opposed to its padding,
    which is the space inside the component). The margin must be a string of 1-4 numbers followed by the units (e.g. "16px") or an integer (e.g. 16),
    separated by spaces.

    The margin must be a string followed by the units (e.g. "16px") or an integer (e.g. 16).
    If an integer is given, the units are assumed to be pixels. Valid units are:

    * px: Pixels
    * em: Relative to the font size of the element
    * rem: Relative to the font size of the root element
    * %: Percentage of the parent element's font size

    .. code-block:: python

        change_margin(Div("Hello"), "16px")  # Adds a 16px margin to all sides
        change_margin(Div("Hello"), "16px 8px")  # Adds a 16px margin to the top and bottom, and an 8px margin to the left and right
        change_margin(Div("Hello"), "16px 8px 4px 2px")  # Adds a 16px margin to the top, 8px to the right, 4px to the bottom, and 2px to the left

    :param margin: The margin to change the component to.
    :type margin: int or str

.. function:: change_border(component, border)

    Changes the border of the component. The border is a string that can be one of the following:

    * ``none``: No border
    * ``solid``: A solid line border
    * ``dotted``: A dotted line border
    * ``dashed``: A dashed line border
    * ``double``: A double line border
    * ``groove``: A 3D grooved border

    Additionally, a border can have a width and color. The width must be a string followed by the units (e.g. "1px") or an integer (e.g. 1).
    The color can be a named color (e.g. "red") or a hex code (e.g. "#FF0000"); see the `colors`_ page for available HTML colors.
    The format is ``"style width color"``. For example:

    .. code-block:: python

        change_border(Div("Hello"), "solid 1px red")  # Adds a solid 1px red border
        change_border(Div("Hello"), "dotted 2px blue")  # Adds a dotted 2px blue border
        change_border(Div("Hello"), "double 3px green")  # Adds a double 3px green border

    :param border: The border to change the component to.
    :type border: str

.. function:: change_padding(component, padding)

    Changes the padding of the component. The padding is the space inside the component (as opposed to its margin,
    which is the space around the component). The padding must be a string of 1-4 numbers followed by the units (e.g. "16px") or an integer (e.g. 16),

    The padding must be a string followed by the units (e.g. "16px") or an integer (e.g. 16).
    If an integer is given, the units are assumed to be pixels. Valid units are:

    * px: Pixels
    * em: Relative to the font size of the element
    * rem: Relative to the font size of the root element
    * %: Percentage of the parent element's font size

    .. code-block:: python

        change_padding(Div("Hello"), "16px")  # Adds a 16px padding to all sides
        change_padding(Div("Hello"), "16px 8px")  # Adds a 16px padding to the top and bottom, and an 8px padding to the left and right
        change_padding(Div("Hello"), "16px 8px 4px 2px")  # Adds a 16px padding to the top, 8px to the right, 4px to the bottom, and 2px to the left

    :param padding: The padding to change the component to.
    :type padding: int or str


.. function:: change_width(component, width)

    Changes the width of the component. The width must be a string followed by the units (e.g. "16px") or an integer (e.g. 16).
    If an integer is given, the units are assumed to be pixels. Valid units are:

    * px: Pixels
    * em: Relative to the font size of the element
    * rem: Relative to the font size of the root element
    * %: Percentage of the parent element's font size

    :param width: The width to change the component to.
    :type width: int or str

.. function:: change_height(component, height)

    Changes the height of the component. The height must be a string followed by the units (e.g. "16px") or an integer (e.g. 16).
    If an integer is given, the units are assumed to be pixels. Valid units are:

    * px: Pixels
    * em: Relative to the font size of the element
    * rem: Relative to the font size of the root element
    * %: Percentage of the parent element's font size

    :param height: The height to change the component to.
    :type height: int or str


Keyword Parameters
------------------

Another way to style components is to use keyword parameters. Any component can take
`style_` prefixed keyword parameters. For example:

.. code-block:: python

    def index(state: State) -> Page:
        return Page(state, [
            Button("Quit", index, style_text_color="red", style_float='right')
        ])

The example above makes the text red and floats the button to the right.

CSS Style Tags
--------------

Since you can embed HTML into any ``Page`` component, you can also embed CSS style tags.

.. code-block:: python

    def index(state: State) -> Page:
        return Page(state, [
            """
            <style>
                button {
                    color: red;
                    float: right;
                }
            </style>
            """
        ])

This is a more dramatic change, since it will update all buttons across the entire page.

CSS Classes
-----------

You can narrow down the styling by using CSS classes. You can add a class to any component
using the ``classes`` keyword parameter. You can then use the class name in your CSS style.

.. code-block:: python

    # Global Constant for cleaner, reusable code
    STYLE = """
    <style>
        .quit-button {
            color: red;
            float: right;
        }
    </style>
    """

    def index(state: State) -> Page:
        return Page(state, [
            STYLE,
            Button("Quit", index, classes="quit-button")
        ])

Don't forget to include the ``STYLE`` constant in every page that uses the ``quit-button`` class.