.. _llm_prompt_snippet:

LLM Prompt Snippet
==================

This page provides a comprehensive reference snippet that can be added to LLM prompts
to help AI assistants understand how to build websites with Drafter. Copy the content
below and append it to your prompts when asking an LLM to create Drafter applications.

.. note::
   The markdown version of this snippet is also available at ``docsrc/llm_prompt_snippet.md``
   for easy copying.

---

Drafter Quick Reference
-----------------------

Drafter is a Python library for creating full-stack web applications. Sites are built with routes, state, and pages.

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: python

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        """Application state - fields persist across pages."""
        username: str
        count: int

    @route
    def index(state: State) -> Page:
        """Routes receive state and return a Page."""
        return Page(state, [
            "Welcome!",
            state.username
        ])

    start_server(State("Guest", 0))

Core Concepts
~~~~~~~~~~~~~

**@route decorator**: Registers a function as a URL endpoint. Function name becomes the URL path.

**State dataclass**: Define with ``@dataclass``. Fields store data across page navigations. Pass the state as first parameter to routes.

**Page(state, content)**: Returns rendered page. First argument is updated state, second is a list of strings and components.

Components Reference
~~~~~~~~~~~~~~~~~~~~

+-----------------------------------------+----------------------------------------+-----------------------------------+
| Component                               | Usage                                  | Description                       |
+=========================================+========================================+===================================+
| ``Button(text, url)``                   | ``Button("Click", next_page)``         | Navigates to another route        |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Button(text, url, arguments)``        | ``Button("Go", page, [Argument(...)])``| Pass extra values                 |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Link(text, url)``                     | ``Link("Go", "page")``                 | Hyperlink to route or external URL|
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``TextBox(name, default)``              | ``TextBox("email", "")``               | Text input; name becomes param    |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``TextArea(name, default)``             | ``TextArea("bio", "")``                | Multi-line text input             |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``SelectBox(name, options, default)``   | ``SelectBox("size", ["S","M","L"])``   | Dropdown menu                     |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``CheckBox(name, default)``             | ``CheckBox("agree", False)``           | Boolean checkbox                  |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``FileUpload(name, accept)``            | ``FileUpload("file", "image/*")``      | File upload input                 |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Image(url, width, height)``           | ``Image("pic.png", 200, 100)``         | Display image                     |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Header(text, level)``                 | ``Header("Title", 1)``                 | Header h1-h6                      |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``NumberedList(items)``                 | ``NumberedList(["A", "B"])``           | Ordered list                      |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``BulletedList(items)``                 | ``BulletedList(["X", "Y"])``           | Unordered list                    |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Table(rows, header)``                 | ``Table([["a","b"]], ["Col1","Col2"])``| HTML table                        |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Div(*content)``                       | ``Div("Hello", Button(...))``          | Container div                     |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Span(*content)``                      | ``Span("text")``                       | Inline span                       |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Row(*content)``                       | ``Row(Button("A", a), Button("B", b))``| Flex row layout                   |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``LineBreak()``                         | ``LineBreak()``                        | Line break                        |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``HorizontalRule()``                    | ``HorizontalRule()``                   | Horizontal line                   |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``PreformattedText(text)``              | ``PreformattedText("code")``           | Preformatted text                 |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Download(text, filename, content)``   | ``Download("Get", "data.txt", data)``  | Download link                     |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``Argument(name, value)``               | ``Argument("id", 42)``                 | Hidden value sent with form       |
+-----------------------------------------+----------------------------------------+-----------------------------------+
| ``MatPlotLibPlot()``                    | ``MatPlotLibPlot()``                   | Embed matplotlib figure           |
+-----------------------------------------+----------------------------------------+-----------------------------------+

Form Data Transfer
~~~~~~~~~~~~~~~~~~

Input components (``TextBox``, ``CheckBox``, ``SelectBox``, ``TextArea``, ``FileUpload``) create form fields.
The ``name`` parameter becomes a parameter in the route receiving the form:

.. code-block:: python

    @route
    def form_page(state: State) -> Page:
        return Page(state, [
            TextBox("username"),
            CheckBox("remember", True),
            Button("Submit", handle_form)
        ])

    @route
    def handle_form(state: State, username: str, remember: bool) -> Page:
        # username and remember come from form fields
        return Page(state, [f"Hello {username}!"])

Argument Component
~~~~~~~~~~~~~~~~~~

Use ``Argument`` to pass hidden values. Place inside Page content or pass to Button:

.. code-block:: python

    # Hidden value in page
    Page(state, [Argument("item_id", 5), Button("Buy", purchase)])

    # Values attached to button
    Button("Delete", delete_item, [Argument("id", item.id)])

Styling
~~~~~~~

**Keyword arguments** - Any component accepts ``style_*`` for CSS:

.. code-block:: python

    Button("Red", page, style_color="red", style_font_size="20px")
    TextBox("name", "", style_background_color="#eee")

**Attributes** - Use non-prefixed kwargs for HTML attributes:

.. code-block:: python

    Div("content", id="main", classes="container highlight")

**Styling functions** - Apply CSS transformations:

.. code-block:: python

    bold("Important")           # Font-weight bold
    italic("Emphasis")          # Font-style italic
    underline("Linked")         # Text decoration underline
    strikethrough("Old")        # Line-through text
    monospace("code")           # Monospace font
    float_right(Button(...))    # Float right
    float_left(Image(...))      # Float left
    change_color("text", "red") # Change text color
    change_background_color(Div(...), "#fff")
    change_text_size("big", "24px")
    change_margin(Div(...), "10px")
    change_padding(Div(...), "5px")
    change_border(Div(...), "1px solid black")

Configuration Functions
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    set_website_title("My App")       # Browser tab title
    set_website_framed(False)         # Remove default frame
    set_website_style("none")         # Disable default theme
    hide_debug_information()          # Hide debug panel
    add_website_css("body { background: #f0f0f0; }")  # Custom CSS
    add_website_css("button", "color: blue;")         # Selector + rules

Available themes: ``skeleton`` (default), ``mvp``, ``sakura``, ``simple``, ``tacit``, ``98``, ``XP``, ``7``, ``bootstrap``, ``none``

Testing with Bakery
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from bakery import assert_equal

    assert_equal(
        index(State("Alice", 0)),
        Page(State("Alice", 0), [
            "Welcome!",
            "Alice"
        ])
    )

    assert_equal(
        handle_form(State("", 0), "Bob", True),
        Page(State("", 0), ["Hello Bob!"])
    )

Deployment Functions
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    set_site_information(
        author="email@example.com",
        description="Site description",
        sources=["https://source.com"],
        planning=["design.pdf"],
        links=["https://github.com/repo"]
    )
    hide_debug_information()
    set_website_title("Production Site")
    set_website_framed(False)
    deploy_site()  # Prepares for deployment

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        todos: list
        
    @route
    def index(state: State) -> Page:
        return Page(state, [
            Header("Todo App"),
            NumberedList(state.todos),
            TextBox("new_item"),
            Button("Add", add_item),
        ])

    @route
    def add_item(state: State, new_item: str) -> Page:
        state.todos.append(new_item)
        return index(state)

    start_server(State([]))

Notes
~~~~~

- Routes return ``Page(state, [content_list])``
- Content list contains strings (rendered as ``<p>``) and components
- State persists automatically between page loads
- Form field names must be valid Python identifiers
- Type annotations on route parameters enable automatic conversion
- Use ``Button`` for actions/navigation, ``Link`` for simple hyperlinks
- Generated pages are standard HTML/CSS/JS
