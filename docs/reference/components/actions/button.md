---
page_type: component
title: Button
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - Button
outcome: Trigger a route, optionally passing Arguments.
---

# Button

Group: [Actions](../index.md#actions)

## Description

A `Button` is a clickable control that runs a route. When clicked, it
gathers the values of any form fields on the page, sends them along,
and shows whatever page the target route returns. Use a `Button` when
the visitor is performing an action ("Feed", "Submit", "Play"); use a
[Link](link.md) when the visitor is navigating to another page.

## Syntax

```python
Button(text, url)
Button(text, url, arguments)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `text` | `str` | required | The label shown on the button. |
| `url` | route name or route function | required | The route to run. Give its name as a string, such as `"feed"` for the route defined by `def feed(...)`, or give the function itself. See [Route targets](#route-targets). |
| `arguments` | see [Passing arguments](#passing-arguments) | `None` | Extra values delivered to the target route's parameters. |

Like every component, `Button` also accepts
[styling and attribute keywords](../../keyword-attributes.md).

### Route targets

The `url` parameter accepts the route's name as a string, as in
`Button("Feed", "feed")`, or the route function itself, as in
`Button("Feed", feed)`. Both forms run the same route, and a page
built with one form is equal in tests to the same page built with the
other.

The tutorials use strings. A string works wherever in the file the
target route is defined, because Drafter looks the name up only when
the page is shown. The function form lets an editor that checks names
point out a misspelled route before the program runs. Python looks the
function up at the moment the page is built, so the function form
stops with a `NameError` when a page is built before its target route
has been defined. This happens when a test calls a route from a line
above the definition of a route that it links to.

### Passing arguments

The `arguments` parameter accepts four forms. These four buttons all
deliver the same value, `10`, to a parameter named `amount`:

```python
Button("Add ten", "add_points", Argument("amount", 10))
Button("Add ten", "add_points", [Argument("amount", 10)])
Button("Add ten", "add_points", [("amount", 10)])
Button("Add ten", "add_points", {"amount": 10})
```

The first form is a single [Argument](argument.md). The second is a
list of `Argument` objects, the third is a list of `(name, value)`
pairs, and the fourth is a dictionary. The list and dictionary forms
can hold several entries, such as `{"amount": 10, "bonus": True}`, and
each entry fills the target route's parameter of the same name. The
values must be text, numbers, booleans, or lists of those. The
[Argument](argument.md) page describes what happens when a name
matches no parameter.

## Examples

In its most basic form, a button runs a route that changes the state
and shows the result:

```python drafter height=200
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ada the corgi has had " + str(state.treats) + " treats.\n",
        Button("Give a treat", "feed")
    ])


@route
def feed(state: State) -> Page:
    state.treats = state.treats + 1
    return index(state)


start_server(State(0))
```

A button submits the form fields on its page; the values arrive as
parameters named after each field:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    greeting: str


@route
def index(state: State) -> Page:
    return Page(state, [
        state.greeting + "\n",
        "Your name:",
        TextBox("visitor"),
        "\n",
        Button("Say hello", "greet")
    ])


@route
def greet(state: State, visitor: str) -> Page:
    state.greeting = "Hello, " + visitor + "!"
    return index(state)


start_server(State("Hello, whoever you are!"))
```

With `arguments`, several buttons can share one route while
identifying which button was clicked:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    activity: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Captain the cat is currently: " + state.activity + "\n",
        Button("Nap time", "act", [Argument("choice", "napping")]),
        Button("Play time", "act", [Argument("choice", "playing")])
    ])


@route
def act(state: State, choice: str) -> Page:
    state.activity = choice
    return index(state)


start_server(State("sitting"))
```

A frequent use of `arguments` is a button on every row of a list,
where each button tells the route which row it belongs to. This
example gives each Delete button its row's position, written in the
dictionary form, and the `delete` route receives that position as an
`int`:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


@route
def index(state: State) -> Page:
    content = [Header("Chores")]
    position = 0
    for chore in state.chores:
        content.append(chore + " ")
        content.append(Button("Delete", "delete", {"position": position}))
        content.append("\n")
        position = position + 1
    return Page(state, content)


@route
def delete(state: State, position: int) -> Page:
    state.chores.pop(position)
    return index(state)


start_server(State(["Walk Ada", "Brush Captain", "Feed Domino"]))
```

## Notes

- A button whose `url` names no existing route stops the page with a
  [points to non-existent page](../../../help/errors/route-not-found.md)
  error. Check the spelling against the route function's name.
- Two buttons can point at the same route; use `arguments` to tell
  them apart, as above.
- While a click is being processed, the button can show a loading
  spinner; see `set_button_spinners` in
  [Site configuration](../../site-config.md).
- In tests, pages compare by structure:
  `assert_has(index(State(0)), Button("Give a treat", "feed"))`.

## Accessibility

Button text is what screen readers announce, so make it name the
action ("Give a treat"), not a vague "Click here". Buttons are
keyboard-operable by default; do not replace them with styled text.

## Related components

- [Link](link.md): the counterpart component for navigating to
  another page.
- [Argument](argument.md): extra values a button can deliver to its
  route.
- Inputs like [TextBox](../input/textbox.md) supply the form values a
  button submits.
- [Add and connect pages](../../../add/pages.md) is the how-to guide
  for joining several pages with buttons and links.
- [Show different content](../../../add/show-different-content.md) is
  the how-to guide with a recipe for one route that serves many
  buttons.

## External links

- [The button element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/button)
