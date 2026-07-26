# Transitioning from Drafter to Flask

Welcome to this guide on transitioning from Drafter to Flask. You have just completed a web project in Drafter and are now ready to explore Flask, a more flexible and powerful web framework for Python.

## Table of Contents

- [What is Flask?](#what-is-flask)
- [Installing Flask](#installing-flask)
- [Basic Routing](#basic-routing)
- [Returning HTML Content](#returning-html-content)
- [Using Templates](#using-templates)
- [Handling Forms and Input](#handling-forms-and-input)
- [Managing State](#managing-state)
- [Conclusion](#conclusion)

## What is Flask?

Flask is a lightweight web framework for Python that allows you to create and manage web applications. Unlike Drafter, which simplifies many aspects of web development, Flask requires you to manually set up routing, templates, and state management.

Official Flask documentation: <https://flask.palletsprojects.com/en/latest/>

## Installing Flask

Flask can be installed through Thonny in two ways:

1. Through the [Thonny package manager](https://thonny.org/#:~:text=Simple%20and%20clean%20pip%20GUI.%20Select%20Tools%20%E2%86%92%20Manage%20packages%20for%20even%20easier%20installation%20of%203rd%20party%20packages.)
   - Open the package manager through Tools -> Manage packages
   - Search for "flask"
   - Install Flask from PyPI
2. Through the [Thonny system shell](https://thonny.org/#:~:text=Beginner%20friendly%20system%20shell.%20Select%20Tools%20%E2%86%92%20Open%20system%20shell%20to%20install%20extra%20packages%20or%20learn%20handling%20Python%20on%20command%20line.%20PATH%20and%20conflicts%20with%20other%20Python%20interpreters%20are%20taken%20care%20of%20by%20Thonny.)
   - Open the system shell through Tools -> Open system shell
   - Run `pip install flask`

From a terminal:

```bash
pip install flask
```

## Basic Routing

In Drafter, you use `@route`:

```python
from drafter import *

@route
def index(state) -> Page:
    return Page(state, ["Hello, Drafter!"])

start_server()
```

Flask equivalent:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, Flask!"

if __name__ == '__main__':
    app.run(debug=True)
```

## Returning HTML Content

In Drafter, you can return components in a `Page`. In Flask, you can return HTML strings directly or render templates.

```python
@app.route('/')
def index():
    return """
    <h1>Welcome to Flask</h1>
    <button>Click me</button>
    """
```

## Using Templates

Create `templates/index.html`:

```html
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
```

Render it:

```python
from flask import render_template

@app.route('/')
def index():
    return render_template('index.html')
```

## Handling Forms and Input

In Flask, use HTML forms and read submitted values from `request.form`.

```html
<form action="/submit" method="post">
    <label for="name">Name:</label>
    <input type="text" id="name" name="name">
    <button type="submit">Submit</button>
</form>
```

```python
from flask import request

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    return f"Hello, {name}!"
```

## Managing State

In Flask, session storage is commonly used for per-user state.

```python
from flask import session

app.secret_key = 'your_secret_key'

@app.route('/set_state')
def set_state():
    session['name'] = 'Alice'
    return "State saved!"

@app.route('/get_state')
def get_state():
    return f"Name: {session.get('name', 'No name set')}"
```

## Conclusion

This guide outlined the transition from Drafter to Flask for routes, templates, forms, and state management. Flask gives you more flexibility, but requires more setup.
