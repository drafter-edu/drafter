---
page_type: tutorial
title: Moving on to Flask
level: L4
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Bridge from Drafter to a backend framework.
---

# Moving on to Flask

You have built something real in Drafter, and now you want things
that Drafter leaves out on purpose. You might want a server that
you control, data that is still there after a reload, or visitors
who can see what other visitors did. Flask is a widely used Python
library for building that kind of site, and most of what you
learned in Drafter has a direct counterpart in it.

## What you'll build

You will build the same small greeting app twice. The app asks for
a name in a form and then greets the visitor by that name. The
first version is in Drafter and the second is in Flask, so that
each new piece of Flask sits next to the Drafter idea you already
know. After that you will move the HTML into a template, test the
Flask app, and read a table that pairs each Drafter idea with its
Flask counterpart.

## What you need

You need Python, your Drafter experience, and Flask itself. Flask
installs like any other package, either through Thonny's
**Tools**, then **Manage packages**, or with `pip install flask`
on the command line. The code on this page was run with Flask 3.1.
Flask's own
[quickstart](https://flask.palletsprojects.com/en/latest/quickstart/)
is a good page to keep open next to this one.

## The app you already know

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Hello, " + state.name + "!"),
        "Your name: ",
        TextBox("new_name"),
        Button("Save", "save_name")
    ])


@route
def save_name(state: State, new_name: str) -> Page:
    state.name = new_name
    return index(state)


assert_has(save_name(State("stranger"), "Ada"), Header("Hello, Ada!"))

start_server(State("stranger"))
```

Four connections hold this program together. The `Button` names
the route to run. The `TextBox` is named `new_name`, and its text
arrives in the parameter with the same name. The route stores the
name in the state, and returning a `Page` shows the result. Each
of these four has a Flask counterpart in the next listing.

## The same app in Flask

Save this program as `app.py`. It is not a Drafter program, so it
has no live demo on this page.

```python
from flask import Flask, redirect, request, session, url_for
from markupsafe import escape

app = Flask(__name__)
app.secret_key = "replace-this-with-random-text"


@app.route("/")
def index():
    name = session.get("name", "stranger")
    return (
        "<h1>Hello, " + str(escape(name)) + "!</h1>"
        + '<form action="/save_name" method="post">'
        + 'Your name: <input name="new_name">'
        + "<button>Save</button>"
        + "</form>"
    )


@app.route("/save_name", methods=["POST"])
def save_name():
    session["name"] = request.form["new_name"]
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
```

Run the file and visit `http://localhost:5000` in your browser.
The app behaves like the Drafter version, with one difference you
can see. After you save a name, the Flask version still greets you
by that name when you reload the page, because the name is stored
outside the page. The state of a Drafter app starts over on every
reload.

The pieces line up with the Drafter program as follows.

- `@app.route("/")` does the job of `@route`, with the address
  written out. In Drafter the route's name is the function's name.
  In Flask you choose the address yourself, and `"/"` is the
  address of the front page.
- `index` returns a string of HTML. Flask has no `Page` and no
  components, so the header is an `<h1>` tag, the text box is an
  `<input>` tag, and the button is a `<button>` tag that you type
  out.
- The `<form>` tag's `action="/save_name"` does the job of the
  `Button`'s target. Submitting the form sends the visitor's
  browser to that address. `method="post"` says that the form is
  sending data, and `methods=["POST"]` on the `save_name` route
  says that the route accepts data sent that way.
- `<input name="new_name">` is the `TextBox("new_name")`. Flask
  does not pass the text as a parameter. The route looks the text
  up by the same name in `request.form`, which holds every field
  of the form that was submitted.
- Flask routes have no `state` parameter. A Flask program is one
  running program that answers every visitor, so anything it
  remembers about one visitor has to be stored somewhere that
  belongs to that visitor. `session` is that place. It behaves
  like a dictionary, and Flask keeps a separate one for each
  visitor's browser.
- `save_name` does not return a page. It returns
  `redirect(url_for("index"))`, which tells the browser to go and
  ask for the front page. `url_for("index")` looks up the address
  of the `index` function, so the address is written in only one
  place. The Drafter route did the same job with
  `return index(state)`.
- `app.run(debug=True)` does the job of `start_server`. The
  difference is where the Python runs. With Flask, your Python
  runs on the computer that started the program, and each
  visitor's browser receives only the HTML that a route returns.
- `app.secret_key` has no Drafter counterpart. Flask stores the
  session in the visitor's browser and uses the secret key to
  detect whether the visitor changed it. A real site needs a long
  random key that is kept out of public code.

One line has no Drafter counterpart because Drafter did the work
for you. `escape(name)` turns any HTML in the name into plain
text. Drafter escapes every string it displays, as
[Security honestly](security.md) shows. In Flask, a string that
you build yourself is sent to the browser exactly as it is, so
text from a visitor must go through `escape` first.

### Moving the HTML into a template

Building HTML out of Python strings becomes hard to read as a page
grows. Flask's answer is a **template**, which is an HTML file
with marked gaps that Flask fills in. Create a folder named
`templates` next to `app.py`, and save this file in it as
`index.html`.

```html
<h1>Hello, {{ name }}!</h1>
<form action="{{ url_for('save_name') }}" method="post">
    Your name: <input name="new_name">
    <button>Save</button>
</form>
```

Then import `render_template` from `flask` and change the `index`
route to use the file.

```python
@app.route("/")
def index():
    name = session.get("name", "stranger")
    return render_template("index.html", name=name)
```

Each pair of double braces is a gap. `{{ name }}` is filled with
the value passed as `name=name`, and the template escapes that
value for you, so the `escape` import is no longer needed. The
template can call `url_for` as well, which removes the last
hand-typed address. The template language is called Jinja. It
also has loops and `if` blocks, which take over the job that a
`for` loop building a list of components did in Drafter.

## What transfers and what is new

Most of your habits carry over. A route is still a function, a
form field still reaches the route by its name, and a page is
still built from data. What is new is the machinery that Drafter
kept out of sight. You now write HTML or templates, you work with
a request coming in and a response going out, you run a server
and later find somewhere to host it, and before long you will
want a database. Flask asks you to handle each of those yourself,
and in return each of them is under your control.

### Drafter ideas and their Flask counterparts

| Idea | In Drafter | In Flask |
| ---- | ---------- | -------- |
| A route | `@route` above a function. The route's name is the function's name. | `@app.route("/save_name")` above a function. You write the address, and a route that receives a form adds `methods=["POST"]`. |
| What a route returns | `Page(state, [...])`, a list of components. | A string of HTML, usually from `render_template(...)`, or a `redirect(...)` to another route. |
| Remembering things | `state`, which every route receives and returns. It lives in one browser tab and starts over on a reload. | `session` for a few small values per visitor. Data that is shared or must last goes in a database. |
| Going to another route | `Button("Save", "save_name")` or `Link("Home", "index")`. | A `<form action="..." method="post">` with a `<button>`, or a link written as `<a href="{{ url_for('index') }}">Home</a>`. |
| Reading a form field | `TextBox("new_name")` fills the parameter `new_name: str`, converted to the annotated type. | `<input name="new_name">` is read with `request.form["new_name"]`, which is always a string. `request.form.get("age", type=int)` converts it. |
| Tests | `assert_equal` and its relatives, calling the route function directly. | `app.test_client()`, which sends requests to the app without a browser. |
| Starting the app | `start_server(State("stranger"))` | `app.run(debug=True)` |
| Deploying | Compile to plain files and put them on any static host, such as GitHub Pages. Each visitor's browser runs the Python. | Rent or borrow a server that keeps your Python program running, usually through a hosting service. |

### Testing a Flask route

In Drafter you test a route by calling it, as the `assert_has`
line in the first listing does. A Flask route that uses `session`
or `request` cannot be called that way. Both objects exist only
while Flask is answering a request, and calling `index()` on its
own stops with this error.

```text
RuntimeError: Working outside of request context.
```

Flask provides a **test client** for this purpose. The test
client sends requests to your app the way a browser would, without
starting a server. Save these lines as `test_app.py` next to
`app.py` and run the file.

```python
from app import app

client = app.test_client()
client.post("/save_name", data={"new_name": "Ada"})
response = client.get("/")
assert "Hello, Ada!" in response.text
print("The greeting test passed.")
```

The `post` call submits the form with `new_name` filled in, and
the `get` call asks for the front page afterwards. One client
keeps its session between requests, as one visitor's browser
would, which is why the second request is greeted as Ada.
`assert` is Python's own checking statement. It stops the program
with an `AssertionError` when the condition is false and does
nothing when the condition is true, so the final `print` runs only
when the test passed.

## Name it

You have now used both ways of running a web application. Drafter
is **client-side**, which means that the program is sent to each
visitor and runs privately in that visitor's browser. Flask is
**server-side**, which means that one program on a computer you
control answers every visitor. A server-side program can keep data
that all visitors share, can keep that data permanently, and can
hold a secret that visitors never see. The price is that someone
has to keep that computer running. The other differences between
the two libraries follow from this one.

## Common problems

- **"Where do I put my State dataclass?"** Flask has no single
  place for it. Decide what each field was for. A value that
  belongs to one visitor goes in `session`. Data that is shared or
  permanent goes in a database. A value that was only used while
  building one page becomes a local variable in the route.
- **Every visitor sees the same data.** A variable defined at the
  top of a Flask program is shared by all visitors, because there
  is only one running program. Keep per-visitor data in `session`.
- **`RuntimeError: Working outside of request context.`** A route
  that uses `session` or `request` was called as a plain function.
  Use the test client, as shown above.
- **"400 Bad Request" after submitting a form.** The name inside
  `request.form[...]` does not match the `name` of any input in
  the form. This is the Flask version of a parameter name that
  does not match its `TextBox`.
- **"405 Method Not Allowed".** The address of a route that
  accepts only `POST` was opened directly, for example by typing
  `/save_name` into the address bar. Reach that route by
  submitting the form.
- **There is no debug panel.** Flask's debug mode shows an error
  page with a traceback and restarts the server when you save the
  file. It has no display of the current state and no page
  history, so `print()` and tests do that work.
- **Writing HTML by hand feels like a step backward.** Templates
  give back much of the structure that components provided, so
  move each page into a template early.

## Make it yours

Rebuild the smallest working version of your final project in
Flask, with the index page and one action and nothing else. That
is enough to use a form, the session, and a template once each, on
an app whose behavior you already know.

## Next steps

- [Flask's tutorial](https://flask.palletsprojects.com/en/latest/tutorial/)
  builds a blog with user accounts and a database, which are the
  two things a Drafter app cannot have.
- [Security honestly](security.md) is worth rereading now. With a
  server of your own, real secrets become possible, and so do real
  security mistakes.
- [Why Drafter](../teach/why-drafter.md) describes the design
  choices behind Drafter, which read differently once you have
  used both libraries.
