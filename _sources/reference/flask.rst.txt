.. title:: Transitioning from Drafter to Flask

===================================
Transitioning from Drafter to Flask
===================================

Welcome to this guide on transitioning from Drafter to Flask! You have just completed a web project in Drafter and are now ready to explore Flask, a more flexible and powerful web framework for Python. This guide will help you draw connections between Drafter and Flask while ensuring a smooth transition.

.. contents:: Table of Contents
    :depth: 2

--------------
What is Flask?
--------------

Flask is a lightweight web framework for Python that allows you to create and manage web applications. Unlike Drafter, which simplifies many aspects of web development, Flask requires you to manually set up routing, templates, and state management. However, this added flexibility allows for more complex and scalable web applications.

Official Flask documentation: <https://flask.palletsprojects.com/en/latest/>_

----------------
Installing Flask
----------------

Flask can be installed through the Integrated Development Environment (IDE) Thonny_ in two ways:

1. Through the `Thonny package manager`_
    - Open the package manager through *Tools* -> *Manage packages*
    - Type in the search bar for "flask"
    - Press "Find packages from PyPI"
    - Flask should be loaded from the search. Press "Install".

**OR:**

2. Through the `Thonny system shell`_
    - Open the Thonny system shell through *Tools* -> *Open system shell*
    - Type ``pip install flask``

This might also be the time to start exploring using VS Code or a more serious development environment.
From a terminal, you can install Flask easily enough:

.. code-block::

    pip install flask

Once Flask is installed, you will need to create a new Python file for your Flask application. A common
name for this file would be ``app.py``.

-------------
Basic Routing
-------------

In Drafter, you used the ``route`` decorator to define routes. In Flask, you use the ``app.route`` decorator.

.. code-block:: python

    from drafter import *

    @route
    def index(state) -> Page:
        return Page(state, ["Hello, Drafter!"])

    start_server()

Flask Equivalent:

.. code-block:: python

    from flask import Flask

    app = Flask(name)

    @app.route('/')
    def index():
        return "Hello, Flask!"

    if name == 'main':
        app.run(debug=True)

In Flask, the ``app.run()`` function starts the server. Notice that you have to create an instance of
the ``Flask`` object and assign it to ``app``.

The ``debug=True`` argument enables live reloading and error messages during development;
this is a feature that Drafter automatically enables.

----------------------
Returning HTML Content
----------------------

In Drafter, you could return HTML directly inside a Page object using components, or by writing HTML directly.
In Flask, you return an HTML string or use templates (although templates are far more popular for maintainability).

Drafter Example:

.. code-block:: python

    @route
    def index(state) -> Page:
        return Page(state, [
            "Welcome to Drafter",
            Button("Click me", hello_clicked)
        ])

Flask Equivalent:

.. code-block:: python

    @app.route('/')
    def index():
        return """
        Welcome to Flask
        <button>Click me</button>
        """


---------------
Using Templates
---------------

Instead of writing the HTML content in a string, Flask uses HTML templates stored in a ``templates/`` folder.

Create a templates folder and a file called index.html inside it:

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Template</title>
    </head>
    <body>
        <h1>Welcome to Flask</h1>
        <button>Click me</button>
    </body>
    </html>

Modify app.py to render the template:

.. code-block:: python

    from flask import render_template

    @app.route('/')
    def index():
        return render_template('index.html')

------------------------
Handling Forms and Input
------------------------

In Drafter, user input is collected using components like TextBox and Button, with data automatically passed to routes.

.. code-block:: python

    @route
    def form_page(state) -> Page:
        return Page(state, [
            TextBox("name"),
            Button("Submit", form_result)
        ])

    @route
    def form_result(state, name: str) -> Page:
        return Page(state, [f"Hello, {name}!"])

In Flask, you use HTML forms and request data from the client.

Create an HTML form (templates/form.html):

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Form</title>
    </head>
    <body>
        <form action="/submit" method="post">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name">
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>

Handle the form submission in app.py:

.. code-block:: python

    from flask import request

    @app.route('/submit', methods=['POST'])
    def submit():
        name = request.form.get('name')
        return f"Hello, {name}!"

--------------
Managing State
--------------

In Drafter, you stored state in a dataclass and passed it between routes. In Flask, you use sessions to store user data across requests.

.. code-block:: python

    from flask import session

    app.secret_key = 'your_secret_key'

    @app.route('/set_state')
    def set_state():
        session['name'] = 'Alice'
        return "State saved!"

    @app.route('/get_state')
    def get_state():
        return f"Name: {session.get('name', 'No name set')}"

----------
Conclusion
----------

This document oulined the transition from Drafter to Flask for routes, templates, forms, and state management.
Flask gives you more flexibility but requires a bit more setup.

To learn more, check out the Flask documentation: <https://flask.palletsprojects.com/en/latest/>_


.. _Thonny: https://thonny.org/
.. _Thonny system shell: https://thonny.org/#:~:text=Beginner%20friendly%20system%20shell.%20Select%20Tools%20%E2%86%92%20Open%20system%20shell%20to%20install%20extra%20packages%20or%20learn%20handling%20Python%20on%20command%20line.%20PATH%20and%20conflicts%20with%20other%20Python%20interpreters%20are%20taken%20care%20of%20by%20Thonny.
.. _Thonny package manager: https://thonny.org/#:~:text=Simple%20and%20clean%20pip%20GUI.%20Select%20Tools%20%E2%86%92%20Manage%20packages%20for%20even%20easier%20installation%20of%203rd%20party%20packages.
.. _Python virtual environment: https://realpython.com/python-virtual-environments-a-primer/
