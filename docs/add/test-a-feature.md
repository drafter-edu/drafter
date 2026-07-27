---
page_type: how-to
title: Test a feature
level: L2
audience: S
priority: P0
prereqs: [start/first-app]
symbols: []
outcome: Write focused tests for routes.
---

# Test a feature

## Goal

You added a feature and want proof it works, now and every time you run
the program from now on.

## Before you start

One fact makes all of this possible: every route is a plain function. It
takes a `State`, returns a `Page`, and you can call it yourself and check
the result. Drafter's `assert_` functions make those checks easy to
write, and they are built in.

Tests go after your routes and before `start_server(...)`. They run at
every startup. A passing test prints a `SUCCESS` line; a failing one
prints a `FAILURE` explaining exactly what differed, and **never crashes
your program**; the rest of your tests keep running. Every result also
appears in the debug panel's **Tests** tab with a side-by-side
comparison.

## The smallest version

The running example for this page, with its tests:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    score: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Cookie Game"),
        "Your score is " + str(state.score) + "\n",
        Button("Click me!", "add_point")
    ])


@route
def add_point(state: State) -> Page:
    state.score = state.score + 1
    return index(state)


assert_state(add_point(State(5)), State(6))
assert_has(index(State(5)), "Your score is 5")
assert_has(index(State(5)), Button("Click me!", "add_point"))

start_server(State(0))
```

Read them aloud: adding a point to a score of 5 gives 6; the page shows
the score; the page has the button. Three facts that matter, checked in
three lines.

## Pick the assertion that matches what you care about

| Function | What it checks |
| -------- | -------------- |
| `assert_state(page, expected_state)` | Just the page's state (the data) |
| `assert_has(page, needle)` | The page contains some text or component, anywhere |
| `assert_content(page, expected_content)` | Just the page's content, in full |
| `assert_page(page, expected_page)` | The whole page: state and content |
| `assert_text(page, expected_text)` | The visible words, ignoring structure |
| `assert_equal(a, b)` | Any two values |

The first two cover most tests. Prefer them: a test that checks one
thing tells you exactly what broke, and keeps working while you restyle
and rearrange the page. Whole-page `assert_page` tests have their place,
as [frozen regression tests](freeze-pages.md).

## Recipe: check the data

`assert_state` compares only the state. Hand it the whole `Page` your
route returned; it pulls the state out:

```python
assert_state(add_point(State(5)), State(6))
```

A failure names the exact field:

```text
FAILURE at line 20 (assert_state):
    The page's state was different from what the test expected:
      - In State score: Expected 6 but got 5
```

## Recipe: check something is on the page

`assert_has` searches the whole page, however deeply nested. The needle
can be text (partial matches count) or a whole component:

```python
page = index(State(5))
assert_has(page, "score")
assert_has(page, Button("Click me!", "add_point"))
assert_not_has(page, "Game Over")
```

A failed text search shows what text the page *did* have, which makes
typos easy to spot. (`assert_in` and `assert_not_in` are the same checks
with the arguments flipped, needle first.)

## Recipe: zoom in on one component

`page.content` is a list, so you can grab one component and check its
details:

```python
page = index(State(5))
button = page.content[2]
assert_attribute(button, "text", "Click me!")
assert_children(page.content[0], "Cookie Game")
```

Styling is normally ignored by tests, but when a style is the point, use
`assert_style`:

```python
fancy = Button("Click me!", "add_point", style_color="red")
assert_style(fancy, "color", "red")
```

It sees styles set on the component itself (helpers, `style_` keywords);
themes and CSS files are invisible to it.

## Loose by default, strict when you want

Assertions are deliberately forgiving, so tests do not break over things
that usually do not matter: capitalization and extra spaces are ignored,
styling is ignored, and floats match to 4 decimal places. Flags tighten
any single test:

```python
assert_has(page, "Your score is 5", exact_strings=True)
assert_state(result, State(0.333333333), precision=8)
```

`set_assertion_defaults(...)` changes the default for every test at
once, for example `set_assertion_defaults(strict_styles=True)` when an
assignment is all about styling.

## Common problems

- **Your tests do not run**: they must sit before `start_server(...)`;
  nothing after that line runs.
- **A test broke after you restyled a page**: the test is checking more
  than it cares about. Narrow it: `assert_page` → `assert_has` or
  `assert_state`.
- **`assert_has` cannot find text that is clearly in a table**: text
  search does not reach inside a `Table`'s rows; use a component needle,
  as in [Show a collection](show-a-collection.md).
- **A test fails and you cannot see why**: the debug panel's Tests tab
  shows expected and actual side by side, with the differences listed.

## Understand it

Routes are callable functions returning inspectable pages:
[Routes and pages](../concepts/routes-and-pages.md) and
[State](../concepts/state.md).

## See another example

Every guided project tests as it builds; the
[virtual pet's mood tests](../tutorials/virtual-pet.md) are a good
pattern to copy.

## Look it up

[Testing functions](../reference/testing-functions.md): every assertion
with its flags and failure output.

## Fix a problem

["Circular Reference" in generated tests](../help/errors/circular-reference-tests.md),
and [Freeze finished pages](freeze-pages.md) for turning page history
into regression tests automatically.
