Components Reference
====================

This is a comprehensive reference for all Components in Drafter, including code examples and explanations.

.. _components_reference:

Form Input Components
---------------------

TextBox
~~~~~~~

Creates a single-line text input field.

**Usage:**

.. code-block:: python

    TextBox(name)
    TextBox(name, default_value)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Enter your name:",
            TextBox("user_name"),
            TextBox("user_email", "example@email.com"),  # with default
            Button("Submit", process_form)
        ])

**Description:** TextBox creates an HTML ``<input type="text">`` element. The ``name`` parameter specifies the field name that will be passed to your route function. An optional ``default_value`` can be provided to pre-fill the field.

**Visual Example:**

.. image:: /_static/component_examples/textbox-example.png
   :alt: TextBox component showing a basic text input field
   :width: 600px

After entering text and clicking Submit:

.. image:: /_static/component_examples/textbox-result.png
   :alt: Result after submitting text through TextBox
   :width: 600px

TextArea
~~~~~~~~

Creates a multi-line text input area.

**Usage:**

.. code-block:: python

    TextArea(name)
    TextArea(name, default_value)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Enter your comment:",
            TextArea("user_comment"),
            TextArea("feedback", "Please provide detailed feedback..."),
            Button("Submit", process_form)
        ])

**Description:** TextArea creates an HTML ``<textarea>`` element for longer text input. It automatically expands to fit content and allows line breaks.

SelectBox
~~~~~~~~~

Creates a dropdown selection menu.

**Usage:**

.. code-block:: python

    SelectBox(name, options)
    SelectBox(name, options, default_value)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Choose your favorite color:",
            SelectBox("color", ["Red", "Green", "Blue"]),
            SelectBox("size", ["Small", "Medium", "Large"], "Medium"),
            Button("Submit", process_form)
        ])

**Description:** SelectBox creates an HTML ``<select>`` element. The ``options`` parameter should be a list of strings. The optional ``default_value`` specifies which option is pre-selected.

CheckBox
~~~~~~~~

Creates a checkbox for boolean input.

**Usage:**

.. code-block:: python

    CheckBox(name)
    CheckBox(name, default_value)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            CheckBox("newsletter"), "Subscribe to newsletter",
            LineBreak(),
            CheckBox("terms", True), "I agree to terms (checked by default)",
            Button("Submit", process_form)
        ])

**Description:** CheckBox creates an HTML ``<input type="checkbox">`` element. The value passed to your route function will be ``True`` if checked, ``False`` if unchecked.

FileUpload
~~~~~~~~~~

Creates a file upload input.

**Usage:**

.. code-block:: python

    FileUpload(name)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Upload a file:",
            FileUpload("user_file"),
            Button("Upload", process_file)
        ])

    @route
    def process_file(state: str, user_file) -> Page:
        if user_file:
            return Page(state, [f"Uploaded: {user_file.filename}"])
        return Page(state, ["No file uploaded"])

**Description:** FileUpload creates an HTML ``<input type="file">`` element. The uploaded file object has ``filename`` and ``content`` attributes.

Interactive Components
----------------------

Button
~~~~~~

Creates a clickable button that navigates to another route.

**Usage:**

.. code-block:: python

    Button(text, route_function)
    Button(text, route_function, arguments)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: int) -> Page:
        return Page(state, [
            f"Counter: {state}",
            Button("Increment", increment),
            Button("Add 5", add_number, 5),
            Button("Reset", reset)
        ])

    @route
    def increment(state: int) -> Page:
        return index(state + 1)

    @route
    def add_number(state: int, amount: int) -> Page:
        return index(state + amount)

**Description:** Button creates an HTML ``<button>`` element that submits a form to the specified route. Additional arguments can be passed as hidden form fields.

**Visual Example:**

.. image:: /_static/component_examples/button-example.png
   :alt: Button component showing increment, decrement, and reset buttons
   :width: 600px

After clicking the Increment button:

.. image:: /_static/component_examples/button-result.png
   :alt: Result after clicking the increment button showing counter changed from 0 to 1
   :width: 600px

Link
~~~~

Creates a hyperlink to another page or URL.

**Usage:**

.. code-block:: python

    Link(text, destination)
    Link(text, route_function)
    Link(text, route_function, content)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            Link("Visit Google", "https://www.google.com"),
            LineBreak(),
            Link("Go to Page 2", page2),
            LineBreak(),
            Link("Image Link", page2, Image("icon.png"))
        ])

**Description:** Link creates an HTML ``<a>`` element. It can link to external URLs, other route functions, or contain custom content like images.

Content Display Components
--------------------------

Text
~~~~

Displays formatted text content.

**Usage:**

.. code-block:: python

    Text(content)

**Example:**

.. code-block:: python

    Text("This is plain text")
    Text("This text has <em>HTML</em> tags")

Image
~~~~~

Displays an image from a URL or file.

**Usage:**

.. code-block:: python

    Image(url)
    Image(url, width, height)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            Image("https://via.placeholder.com/150x100"),
            Image("logo.png", width=200, height=100),
            Link("Clickable Image", other_page, 
                 Image("button.png"))
        ])

**Description:** Image creates an HTML ``<img>`` element. The URL can be external or a local file. Optional width and height parameters control the display size.

Header
~~~~~~

Creates heading text at different levels.

**Usage:**

.. code-block:: python

    Header(text)              # h1 by default
    Header(text, level)       # h1-h6

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            Header("Main Title"),           # h1
            Header("Subtitle", 2),          # h2
            Header("Section", 3),           # h3
            Header("Subsection", 4)         # h4
        ])

**Description:** Header creates HTML heading elements (``<h1>`` through ``<h6>``). The level parameter determines the heading level (1-6).

Table
~~~~~

Displays data in a tabular format.

**Usage:**

.. code-block:: python

    Table(data)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        student_data = [
            ["Name", "Grade", "Subject"],    # Header row
            ["Alice", "A", "Math"],
            ["Bob", "B+", "Science"],
            ["Charlie", "A-", "History"]
        ]
        
        return Page(state, [
            Header("Student Grades"),
            Table(student_data)
        ])

**Description:** Table creates an HTML ``<table>`` element. The data should be a list of lists, where the first row typically contains column headers.

Layout Components
-----------------

LineBreak
~~~~~~~~~

Inserts a line break.

**Usage:**

.. code-block:: python

    LineBreak()

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "First line",
            LineBreak(),
            "Second line"
        ])

**Description:** LineBreak creates an HTML ``<br>`` element to force a line break in the content flow.

HorizontalRule
~~~~~~~~~~~~~~

Inserts a horizontal dividing line.

**Usage:**

.. code-block:: python

    HorizontalRule()

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Content above",
            HorizontalRule(),
            "Content below"
        ])

**Description:** HorizontalRule creates an HTML ``<hr>`` element to visually separate sections of content.

Div
~~~

Groups content in a block-level container.

**Usage:**

.. code-block:: python

    Div(*components, **attributes)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            Div(
                Header("Section Title"),
                "This content is grouped together",
                style="border: 1px solid black; padding: 10px;"
            )
        ])

**Description:** Div creates an HTML ``<div>`` element to group and style content. Accepts styling attributes.

Span
~~~~

Groups content in an inline container.

**Usage:**

.. code-block:: python

    Span(*components, **attributes)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "This is ",
            Span("highlighted text", style="color: red;"),
            " in a sentence."
        ])

**Description:** Span creates an HTML ``<span>`` element for inline content grouping and styling.

List Components
---------------

BulletedList
~~~~~~~~~~~~

Creates an unordered (bulleted) list.

**Usage:**

.. code-block:: python

    BulletedList(items)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        fruits = ["Apple", "Banana", "Cherry"]
        
        return Page(state, [
            Header("My Favorite Fruits"),
            BulletedList(fruits)
        ])

**Description:** BulletedList creates an HTML ``<ul>`` (unordered list) element with bullet points.

NumberedList
~~~~~~~~~~~~

Creates an ordered (numbered) list.

**Usage:**

.. code-block:: python

    NumberedList(items)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        steps = [
            "Mix ingredients",
            "Heat oven to 350°F", 
            "Bake for 30 minutes"
        ]
        
        return Page(state, [
            Header("Recipe Steps"),
            NumberedList(steps)
        ])

**Description:** NumberedList creates an HTML ``<ol>`` (ordered list) element with sequential numbers.

Advanced Components
-------------------

MatPlotLibPlot
~~~~~~~~~~~~~~

Displays a matplotlib plot as an image.

**Usage:**

.. code-block:: python

    MatPlotLibPlot()

**Example:**

.. code-block:: python

    from drafter import *
    import matplotlib.pyplot as plt

    @route
    def index(state: str) -> Page:
        # Create plot
        plt.figure(figsize=(8, 6))
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        plt.plot(x, y, 'bo-')
        plt.title('Simple Line Plot')
        plt.xlabel('X values')
        plt.ylabel('Y values')
        
        return Page(state, [
            Header("Data Visualization"),
            MatPlotLibPlot()
        ])

**Description:** MatPlotLibPlot creates an HTML ``<img>`` element containing the current matplotlib figure. Requires matplotlib to be installed.

Download
~~~~~~~~

Creates a downloadable file link.

**Usage:**

.. code-block:: python

    Download(text, filename, contents)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        csv_data = "Name,Age\\nAlice,25\\nBob,30"
        
        return Page(state, [
            Header("Export Data"),
            Download("Download CSV", "data.csv", csv_data),
            Download("Download Text", "sample.txt", "Hello World!")
        ])

**Description:** Download creates an HTML ``<a>`` element that triggers a file download when clicked. The file contents are embedded in the link.

Utility Components
------------------

Argument
~~~~~~~~

Creates a hidden form field for passing data.

**Usage:**

.. code-block:: python

    Argument(name, value)

**Example:**

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Process this data:",
            Argument("hidden_id", "12345"),
            Button("Submit", process_data)
        ])

    @route
    def process_data(state: str, hidden_id: str) -> Page:
        return Page(state, [f"Processed ID: {hidden_id}"])

**Description:** Argument creates an HTML ``<input type="hidden">`` element to pass data through forms without displaying it to the user.

Quick Reference Table
---------------------

+-----------------------------------------+--------------+----------------------------------+
| Component Function                      | HTML Tag     | Purpose                          |
+=========================================+==============+==================================+
| TextBox(name, default_value)            | `input`      | Single-line text input           |
+-----------------------------------------+--------------+----------------------------------+
| TextArea(name, default_value)           | `textarea`   | Multi-line text input            |
+-----------------------------------------+--------------+----------------------------------+
| SelectBox(name, options, default)       | `select`     | Dropdown selection               |
+-----------------------------------------+--------------+----------------------------------+
| CheckBox(name, default_value)           | `input`      | Boolean checkbox input           |
+-----------------------------------------+--------------+----------------------------------+
| FileUpload(name)                        | `input`      | File upload field                |
+-----------------------------------------+--------------+----------------------------------+
| Button(text, route, arguments)          | `button`     | Interactive button               |
+-----------------------------------------+--------------+----------------------------------+
| Link(text, destination, content)        | `a`          | Hyperlink                        |
+-----------------------------------------+--------------+----------------------------------+
| Image(url, width, height)               | `img`        | Display images                   |
+-----------------------------------------+--------------+----------------------------------+
| Header(text, level)                     | `h1`-`h6`    | Section headings                 |
+-----------------------------------------+--------------+----------------------------------+
| Table(data)                             | `table`      | Tabular data display             |
+-----------------------------------------+--------------+----------------------------------+
| LineBreak()                             | `br`         | Line break                       |
+-----------------------------------------+--------------+----------------------------------+
| HorizontalRule()                        | `hr`         | Horizontal divider               |
+-----------------------------------------+--------------+----------------------------------+
| Div(*components, **attrs)               | `div`        | Block-level container            |
+-----------------------------------------+--------------+----------------------------------+
| Span(*components, **attrs)              | `span`       | Inline container                 |
+-----------------------------------------+--------------+----------------------------------+
| BulletedList(items)                     | `ul`         | Unordered list                   |
+-----------------------------------------+--------------+----------------------------------+
| NumberedList(items)                     | `ol`         | Ordered list                     |
+-----------------------------------------+--------------+----------------------------------+
| MatPlotLibPlot()                        | `img`        | Matplotlib plot display          |
+-----------------------------------------+--------------+----------------------------------+
| Download(text, filename, contents)      | `a`          | File download link               |
+-----------------------------------------+--------------+----------------------------------+
| Argument(name, value)                   | `input`      | Hidden form field                |
+-----------------------------------------+--------------+----------------------------------+