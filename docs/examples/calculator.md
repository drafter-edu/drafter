---
page_type: example
title: Calculator
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: See forms and state working together in one small app.
---

# Calculator

## What it does

An adding machine: two boxes, one button, one answer. Type two
numbers, press Add, and the sum appears; type something that is not a
number and the machine says so instead of crashing. Small as it is,
it exercises the whole loop of a Drafter app: form values travel to a
route, the route updates state, and the page shows the result.

## Try it

Type numbers, then try typing words.

```python drafter height=300
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    first_number: str
    second_number: str
    result: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adding Machine"),
        "What is the first number?",
        TextBox("first", state.first_number),
        "\nWhat is the second number?",
        TextBox("second", state.second_number),
        "\n",
        Button("Add", "add"),
        "\nThe result is: " + state.result
    ])


@route
def add(state: State, first: str, second: str) -> Page:
    state.first_number = first
    state.second_number = second
    if first.isdigit() and second.isdigit():
        state.result = str(int(first) + int(second))
    else:
        state.result = "not a number!"
    return index(state)


assert_state(add(State("", "", ""), "3", "4"), State("3", "4", "7"))
assert_state(add(State("", "", ""), "cat", "4"),
             State("cat", "4", "not a number!"))
assert_has(index(State("", "", "")), Button("Add", "add"))

start_server(State("", "", ""))
```

## The code

Three pieces do all the work:

- **The `State`** holds both typed values and the result, all as
  strings.
- **The `index` route** builds the page: two `TextBox` fields
  prefilled from state, an Add button, and the current result.
- **The `add` route** receives the boxes' contents as its `first` and
  `second` parameters, saves them, computes the result, and reuses
  `index` to show the page again.

## How it works

The deliberate design decision is that everything in the state is a
`str`, even though this is a calculator. The visitor might type
anything, and the app wants to remember exactly what they typed, wrong
or not, so the boxes stay filled after every press. The `add` route
checks `isdigit()` before converting, so the conversion can never
fail; bad input becomes a message rather than an error.

Compare that with annotating the parameters as `int`: Drafter would
convert for you, but a visitor typing "cat" would hit the friendly
[conversion error](../help/errors/type-conversion-int.md) instead of
your calmer in-page message. Both designs are legitimate; this one
treats bad input as a normal case rather than a mistake.

The last line of `add`, `return index(state)`, is a habit worth
stealing: after changing state, reuse the route that already knows how
to display it.

## Make it yours

In rough order of difficulty:

1. **Modify**: change the starting values from empty strings to
   `"0"`.
2. **Modify**: the machine rejects negative numbers, because
   `"-3".isdigit()` is `False`. Decide whether that is a bug, and if
   so, fix it (checking `lstrip("-").isdigit()` is one way).
3. **Complete**: add a Subtract button pointing at a new route.
4. **Combine**: add a `history: list[str]` field to the state, append
   each calculation like `"3 + 4 = 7"`, and show it with
   `BulletedList`.
5. **Create**: turn it into a tip calculator: bill plus percentage,
   with three preset percentage buttons using `Argument`.

## Tests

The listing carries three assertions, which run before the server
starts and appear in the debug panel's Tests tab:

- `assert_state(add(...), State("3", "4", "7"))` checks the logic:
  calling the route with typed values produces the right state.
- The second checks the failure path: "cat" lands as
  `"not a number!"`.
- `assert_has(index(...), Button("Add", "add"))` checks the page
  offers the button.

Testing routes is just calling functions; see
[Test a feature](../add/test-a-feature.md).

## Likely errors

- **Renaming a box but not the parameter** (or the reverse) produces
  a [missing parameter](../help/errors/missing-parameter.md) error
  naming the route.
- **Changing the Button target** to a route that does not exist stops
  the page with a
  [points to non-existent page](../help/errors/route-not-found.md)
  error.
- **Forgetting `str()`** when building the result, such as
  `state.result = int(first) + int(second)`, makes the state hold an
  `int` where a `str` belonged; the mismatch surfaces when the page
  tries to concatenate it.

## Related

- [Ask the user for information](../add/ask-for-information.md): the
  how-to behind the form.
- [Remember a score or choice](../add/remember-things.md): the
  how-to behind the state.
- [Big form](forms.md): every input type at once.
- [Forms and input](../concepts/forms-and-input.md): why the box
  names become parameters.
