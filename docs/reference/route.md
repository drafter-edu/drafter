---
page_type: reference
title: route
level: L1
audience: S
priority: P0
prereqs: []
symbols:
  - route
  - add_route
outcome: Know exact route decorator behavior.
---

# route

`@route` registers a function with Drafter so that buttons, links, and
addresses can reach it. A route is not a page; it is a function that
builds and returns a [Page](page.md) each time someone arrives.

## Syntax

```python
@route
def some_name(state: State) -> Page: ...

@route("other-address")
def some_name(state: State) -> Page: ...
```

| Form | Meaning |
| ---- | ------- |
| `@route` | Register under the function's own name. `def feed(...)` becomes the address `feed`. |
| `@route("url")` | Register under a custom address instead of the function name. |
| `add_route(url, function)` | Do the same thing without decorator syntax. Rarely needed. |

## The name becomes the address

The route registered from `def feed(...)` is what
`Button("Feed", "feed")` points at, and what the browser shows as the
page's address. The route named `index` is special: it builds the
front page shown when your app starts, and every app must have one.

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        "The front page.\n",
        Button("Visit the other page", "second")
    ])


@route
def second() -> Page:
    return Page([
        "The route named second built this page.\n",
        Button("Home", "index")
    ])


start_server()
```

## How parameters are filled

When a route runs, Drafter fills its parameters in a fixed order:

1. **State comes first.** If the first parameter is named `state`, it
   receives the current state. (Drafter can usually still identify the
   state parameter if you name it something else, but `state` is the
   convention and the docs use it everywhere.)
2. **Form values bind by name.** Each input component's `name` must
   match a parameter: `TextBox("guess")` fills a parameter called
   `guess`. The parameter's type annotation controls conversion, so
   `guess: int` receives a number. See
   [Forms and input](../concepts/forms-and-input.md).
3. **Button arguments bind by name too.** `Argument("prize", "gold")`
   attached to a button fills a parameter called `prize`.

A required parameter that nothing fills stops the request with a
[missing parameter](../help/errors/missing-parameter.md) error; a value
that cannot be converted to the annotated type stops it with a
[conversion error](../help/errors/type-conversion-int.md).

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    record: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Last entry: " + state.record + "\n",
        "Pet name:",
        TextBox("pet_name"),
        "\nAge:",
        TextBox("pet_age"),
        "\n",
        Button("Save", "save")
    ])


@route
def save(state: State, pet_name: str, pet_age: int) -> Page:
    state.record = pet_name + " (" + str(pet_age) + " years old)"
    return index(state)


start_server(State("none yet"))
```

## Notes

- **Route names must be unique.** If you define two functions with the
  same name, Python silently keeps only the second definition; this is
  Python's behavior, not Drafter's.
- **Routes are ordinary functions.** You can call one from another
  (`return index(state)`) and call them directly in tests
  (`assert_state(save(State("x"), "Ada", 4), State("Ada (4 years old)"))`).
- **Custom addresses** from `@route("...")` are normalized before
  matching: extra slashes are trimmed, and in the most heavily cleaned
  form, only letters, numbers, and underscores are kept. Buttons and
  links can target the custom address string.
- **Advanced injection (L4):** parameters named `_server`,
  `_configuration`, or `_request` receive framework objects instead of
  form values. You will not need these outside of the advanced
  material in [Extend](../extend/index.md).

## Related

- [Page](page.md): what a route returns.
- [Routes and pages](../concepts/routes-and-pages.md): the concept.
- [Add and connect pages](../add/pages.md): the how-to.
- [Link or button points to an unknown route](../help/errors/route-not-found.md):
  the most common routing mistake.
