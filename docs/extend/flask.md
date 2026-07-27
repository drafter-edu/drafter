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

You built something real in Drafter, and now you want the things
Drafter deliberately does not have: a server you control, data
that survives reloads, users who can share things. Flask is the
classic next step, and your Drafter experience maps onto it more
directly than you might expect.

## What you'll build

The same tiny greeting app twice: once in Drafter (you could
write this in your sleep), then in Flask, so every new piece has
a familiar shadow. From there, a map of what transfers and what
is genuinely new.

## What you need

Python, your Drafter experience, and Flask itself, installed the
same way as any package (Thonny's package manager, or
`pip install flask`). Flask's own
[quickstart](https://flask.palletsprojects.com/en/latest/quickstart/)
is the companion to keep open.

## The app you already know

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    visits: int


@route
def index(state: State) -> Page:
    state.visits = state.visits + 1
    return Page(state, [
        Header("Hello!"),
        "You have visited " + str(state.visits) + " times."
    ])


start_server(State(0))
```

## The same app in Flask

```python
from flask import Flask, session

app = Flask(__name__)
app.secret_key = "any-random-text"


@app.route("/")
def index():
    session["visits"] = session.get("visits", 0) + 1
    return ("<h1>Hello!</h1>"
            + "You have visited " + str(session["visits"])
            + " times.")


if __name__ == "__main__":
    app.run(debug=True)
```

Run it and visit `http://localhost:5000`. Piece by piece:

- `@app.route("/")` is your `@route`, with the URL written out
  explicitly; the index route's URL is `"/"`.
- The function returns HTML as a string. There is no `Page` and
  no components; you write markup yourself (or use Flask's
  template system, the next thing to learn).
- There is no `state` parameter. The server is one program
  serving *everyone*, so per-visitor memory has to live
  somewhere deliberate; `session` is Flask's per-visitor
  storage, and this data survives reloads.
- `app.run(debug=True)` is `start_server`, except this server
  is real: your Python runs on it, and visitors' browsers only
  receive the HTML it returns.

## What transfers and what is new

Your instincts carry over: routes as functions, values crossing
pages through forms (Flask spells it `request.form["name"]`
instead of a named parameter), building pages from data, and
testing routes by calling them. The genuinely new material is
the architecture you never had: a server process to run and
deploy, templates for HTML, request/response vocabulary, and
before long a database. When those feel heavy, that weight is
what Drafter was carrying for you.

## Name it

You now hold both runtime models. Drafter is **client-side**:
the program ships to each visitor and runs privately in their
browser. Flask is **server-side**: one program you host answers
everyone, which is why it can keep shared, permanent data and a
real secret, and why deployment now involves an actual machine.
Every tradeoff between the two frameworks unwinds from that one
difference.

## Common problems

- **"Where do I put my State dataclass?"**: nowhere directly.
  Ask what each field was for: per-visitor memory goes in
  `session`, shared permanent data eventually goes in a
  database, and page-building scratch values become plain local
  variables.
- **Everyone sees the same data**: module-level variables in
  Flask are shared by all visitors, which is sometimes a
  feature and always a surprise. Per-visitor data belongs in
  `session`.
- **Missing the debugger**: fair. Flask's debug mode gives
  error pages and auto-reload, but there is no state inspector;
  `print()` and tests are your eyes again.
- **HTML feels like a step backward**: it is, briefly. Flask's
  `render_template` and the Jinja template language bring the
  structure back; learn them early.

## Make it yours

Port your final project's walking skeleton: the index page and
one action, nothing more. You will meet forms, sessions, and
templates in miniature, on an app whose behavior you already
know by heart, which is the gentlest possible introduction to
all three.

## Next steps

- [Flask's tutorial](https://flask.palletsprojects.com/en/latest/tutorial/):
  builds a real multi-user app with a database, the two things
  Drafter could not give you.
- [Security honestly](security.md): reread it from the other
  side; you now own a server, so secrets are finally possible,
  and so are real mistakes.
- [Why Drafter](../teach/why-drafter.md): the design tradeoffs,
  which read differently once you have seen both worlds.
