---
page_type: concept
title: Why Drafter
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Evaluate Drafter for a course.
search:
  exclude: true
---

# Why Drafter

## In one sentence

Drafter lets students build real, shareable web applications using
only the Python they learn in a first course: functions,
dataclasses, and lists.

## The idea

Most tools for "web development in intro" make one of two
compromises. Either they demand web knowledge students do not have
(HTTP, HTML, CSS, request/response, servers), or they hide the
program structure so thoroughly that students stop writing
recognizable programs. Drafter's design goal is to avoid both: a
Drafter app is ordinary Python, structured the way an intro course
already teaches.

The core alignment points:

- **Routes are functions.** Each page of the app comes from a
  function that takes the current state and returns a `Page`
  value. Students practice exactly what the course teaches:
  parameters in, return value out.
- **State is a dataclass.** The application's data lives in one
  dataclass the student designs. Deciding what fields it needs is
  a genuine data-design exercise, at intro scale.
- **Routes are testable.** Because a route is a function, students
  call it directly in tests: build a state, call the route, assert
  on the result. Web apps usually make testing harder; here it
  reinforces the course's testing habits.
- **Errors are teaching moments.** Drafter's error messages are
  written in two tiers: a friendly explanation with concrete
  next steps first, the technical detail second.
- **The payoff is real.** The finished app compiles to a static
  site a student can deploy to GitHub Pages and send to their
  family. For non-majors especially, that ending matters.

## See it

This is a complete Drafter application, including a test:

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Trivia: Dogs"),
        "Is Ada a corgi? Score: " + str(state.score) + "\n",
        Button("Yes", "correct"),
        Button("No", "index")
    ])


@route
def correct(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(correct(State(0)), State(1))

start_server(State(0))
```

There is no request object, no template language, and no server
process to manage; the whole mental model is functions and a
dataclass.

## What this means for your code examples

- Everything students see can stay inside the known-constructs
  set: functions, dataclasses, lists, loops, conditionals. The
  student docs never use dicts, comprehensions, lambdas, or
  exceptions, and your course materials can hold the same line.
- `@route` and `@dataclass` can be taught as "marks this
  function/class for Drafter" without a decorator lecture.
- Tests belong in every example. Routes being callable means
  `assert_state` and `assert_has` checks cost two lines each.

## Where people get confused

The main tradeoffs, stated honestly:

- **Versus Flask or Django**: those teach the real client/server
  architecture and real HTTP, and they are what industry uses. But
  they demand routing, requests, templates, and deployment
  infrastructure before anything works, which is a lot of scaffold
  for a first course. Drafter has no backend at all: the whole
  program runs in the visitor's browser. That is a simplification
  students eventually need to unlearn, and
  [Moving on to Flask](../extend/flask.md) exists for that moment.
- **Versus Streamlit**: Streamlit is faster to first pixel, but
  its rerun-the-whole-script model breaks the function-call
  mental model an intro course works hard to build, and its
  widget state rules are genuinely confusing. Drafter keeps
  explicit functions with explicit state.
- **Versus raw HTML/CSS/JavaScript**: honest web literacy, but
  three new languages in a Python course.
- **The limits are real.** State lives in memory and vanishes on
  reload. There is no database, no user accounts, and no
  security boundary of any kind: everything ships to the browser.
  Multi-user apps, real logins, and big data are out of scope,
  and student project ideas need steering away from them. The
  first Pyodide load also takes noticeable seconds.

Experienced developers tend to mispredict Drafter by analogy;
[Expert misconceptions](expert-misconceptions.md) collects the
specific corrections.

## Go deeper

- [The big ideas](big-ideas.md): what to emphasize, in order.
- [How Drafter works](../start/how-drafter-works.md): the runtime
  model as students meet it.
- [Python in the browser](../extend/pyodide.md): the fuller
  technical story.
- [Security honestly](../extend/security.md): exactly what is and
  is not protected.
