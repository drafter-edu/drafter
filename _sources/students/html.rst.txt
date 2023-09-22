.. _html:

HTML
====

Ultimately, Pages in Drafter become HTML. Although you can use functions like ``Button`` and ``Link`` to create HTML
elements, you can also embed HTML in the string literals that you return for the page. For example, the following
page will render a button that links to the Google homepage:

.. code-block:: python

    from drafter import *

    @route
    def index() -> Page:
        return Page([
            "<h1>Go to Google</h1>",
            '<a href="http://www.google.com">Google</a>'
        ])

    start_server()

This is a very simple example, but it demonstrates how you can use HTML to create pages. You can also use HTML to
modify text, add images, and more.

.. code-block:: python

    from drafter import *

    @route
    def index() -> Page:
        return Page([
            "<strong>This text</strong> will be bolded. <br>",
            "<em>This text</em> will be italicized. <br>",
            "<u>This text</u> will be underlined. <br>",
            "<s>This text</s> will be strikethrough. <br>",
        ])

    start_server()