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

* ``float_left``
* ``float_right``
* ``bold``
* ``italic``
* ``underline``
* ``strikethrough``
* ``monospace``
* ``small_font``
* ``large_font``
* ``change_color``
* ``change_background_color``
* ``change_text_size``
* ``change_text_font``
* ``change_text_align``
* ``change_text_decoration``
* ``change_text_transform``
* ``change_margin``
* ``change_border``
* ``change_padding``
* ``change_width``
* ``change_height``


Keyword Parameters
------------------

Another way to style components is to use keyword parameters. Any component can take
`style_` prefixed keyword parameters. For example:

.. code-block:: python

    def index(state: State) -> Page:
        return Page(state, [
            Button("Quit", index, style_text_color="red", float='right')
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