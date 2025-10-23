.. _getting_started:

===============================
Getting Started for Beginners
===============================

Welcome to Drafter! This guide will help you understand the basics of web development with Drafter
if you're new to programming or web development. If you're already comfortable with Python, you
might want to skip ahead to the :ref:`quickstart`.

What is Drafter?
================

Drafter is a Python library that lets you create websites without needing to know HTML, CSS, or JavaScript.
You write regular Python code using dataclasses and functions, and Drafter turns that into a working website.

Prerequisites
=============

Before you start, make sure you have:

1. **Python 3.8 or newer** installed on your computer. You can check by opening a terminal and typing:

   .. code-block:: bash

       python3 --version

2. **A text editor or IDE** for writing Python code. We recommend:
   
   - VS Code (beginner-friendly)
   - PyCharm (feature-rich)
   - Thonny (very simple, great for beginners)

3. **Drafter installed**. Follow the installation instructions in the previous chapter if you haven't already.

Understanding the Basics
========================

Before diving into code, let's understand a few key concepts:

Routes
------

A **route** is a Python function that creates a web page. When someone visits a specific URL on your website,
the corresponding route function runs and returns a page to display.

Think of routes like chapters in a book - each URL is like a chapter number, and the route function tells
you what content to show for that chapter.

State
-----

**State** is the data your website remembers between pages. For example, if you're making a calculator website,
the state might remember what numbers the user typed in.

In Drafter, we typically use Python dataclasses to store state. A dataclass is like a container that holds
related pieces of information together.

Pages
-----

A **Page** is what gets shown to the user. It consists of two things:

1. The **state** (the data, hidden from the user)
2. The **content** (what the user sees - text, buttons, images, etc.)

Your First Drafter Website
===========================

Let's build a simple website step by step.

Step 1: Import Drafter
-----------------------

Every Drafter program starts with this line:

.. code-block:: python

    from drafter import *

This imports all the Drafter functions and components you'll need.

Step 2: Create the Index Route
-------------------------------

The **index** route is the main page of your website. It's what shows up when someone first visits your site.

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Hello, World!",
            "This is my first website!"
        ])

    start_server("")

Let's break this down:

- ``@route`` marks the function as a route (a page on your website)
- ``def index(state: str) -> Page:`` defines a function named "index" that takes state as input and returns a Page
- ``return Page(state, [...])`` creates and returns a new Page with the same state and some content
- The content is a **list of strings** - each string becomes text on the page
- ``start_server("")`` starts the web server with an empty string as the initial state

Step 3: Add Some Interactivity
-------------------------------

Let's make our website interactive by adding a button:

.. code-block:: python

    from drafter import *

    @route
    def index(state: str) -> Page:
        return Page(state, [
            "Hello, World!",
            Button("Click me!", "clicked")
        ])

    @route
    def clicked(state: str) -> Page:
        return Page(state, [
            "You clicked the button!",
            Button("Go back", "index")
        ])

    start_server("")

Now we have two routes:

1. ``index`` - shows a button that links to the "clicked" route
2. ``clicked`` - shows a message and a button to go back

Step 4: Remember User Input
----------------------------

Let's create a website that remembers what the user types:

.. code-block:: python

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        user_name: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "What is your name?",
            TextBox("name", state.user_name),
            Button("Submit", "greet")
        ])

    @route
    def greet(state: State, name: str) -> Page:
        state.user_name = name
        return Page(state, [
            f"Hello, {name}!",
            Button("Change name", "index")
        ])

    start_server(State(""))

New concepts here:

- ``@dataclass`` creates a State container that holds ``user_name``
- ``TextBox("name", state.user_name)`` creates a text input box
- ``def greet(state: State, name: str)`` - the ``name`` parameter gets the value from the TextBox
- ``state.user_name = name`` - we update the state to remember the name
- ``f"Hello, {name}!"`` - Python f-strings let you put variables in text

Common Beginner Mistakes
=========================

1. **Forgetting the colon after function definitions**
   
   ❌ Wrong: ``def index(state: State)``
   
   ✅ Right: ``def index(state: State):``

2. **Not returning a Page**
   
   Every route must return a ``Page`` object.

3. **Mismatching parameter names**
   
   If you have ``TextBox("name", ...)``, the parameter must be called ``name`` too:
   
   .. code-block:: python
   
       def greet(state: State, name: str):  # ✅ Correct
       def greet(state: State, username: str):  # ❌ Wrong

4. **Forgetting to import dataclasses**
   
   If you use ``@dataclass``, you need: ``from dataclasses import dataclass``

Next Steps
==========

Now that you understand the basics, you can:

1. Read the :ref:`quickstart` for a more detailed tutorial
2. Explore :ref:`components_detailed` to learn about all the different components (buttons, text boxes, images, etc.)
3. Check out the examples section to see complete working websites
4. Learn about :ref:`styling` to make your website look pretty

Remember: Don't try to learn everything at once! Start with simple websites and gradually add more features
as you get comfortable. The best way to learn is by doing - try building small projects and experimenting!

Getting Help
============

If you get stuck:

1. Check the error message carefully - it often tells you exactly what's wrong
2. Look at the debug information at the bottom of your website - it shows the current state and routes
3. Review the :ref:`help` page for common issues
4. Ask your instructor or classmates for help

Happy coding! 🚀
