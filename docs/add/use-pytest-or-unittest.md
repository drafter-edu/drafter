---
page_type: how-to
title: Use pytest or unittest
level: L3
audience: S
priority: P2
prereqs: [add/test-a-feature]
symbols: []
outcome: Run route tests with pytest or unittest.
---

# Use pytest or unittest

## Goal

You already test your routes with Drafter's `assert_` functions, and
you want to run the same kind of checks with `pytest` or `unittest`,
the two tools most Python projects use.

## Before you start

Every route is a plain function, so any testing tool can call it and
check the `Page` it returns. Only one thing is in the way: your site
file ends with `start_server(...)`, and importing the file would
launch the site and never come back to your tests.

Setting the `DRAFTER_SKIP` environment variable fixes that. While it
is set, `start_server(...)` does nothing at all, so a test file can
import your routes safely. The line that sets it has to run **before**
the line that imports your site.

`unittest` comes with Python. `pytest` is installed separately, with
`pip install pytest`.

## The site being tested

Both examples below test this small site, saved as `cookie_game.py`:

```python
# cookie_game.py
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


start_server(State(0))
```

## Test it with pytest

Put the tests in a second file in the same folder. `pytest` looks for
files whose names start with `test_` and runs every function in them
whose name starts with `test_`:

```python
# test_cookie_game.py
import os

os.environ["DRAFTER_SKIP"] = "1"

from drafter import *
from cookie_game import State, index, add_point


def test_index_shows_the_score():
    assert index(State(7)) == Page(State(7), [
        Header("Cookie Game"),
        "Your score is 7\n",
        Button("Click me!", "add_point")
    ])


def test_add_point_adds_one():
    page = add_point(State(4))
    assert page.state == State(5)


def test_page_mentions_the_score():
    assert assert_has(index(State(12)), "Your score is 12")
```

Run it from that folder:

```text
pytest
```

A passing run prints one dot per test. When a test fails, `pytest`
shows the line that failed and what differed. Here the expected page
said 8 where the real page said 7:

```text
E   Drill down into differing attribute content:
E     content: [Header('Cookie Game'), 'Your score is 7\n', ...] != [Header('Cookie Game'), 'Your score is 8\n', ...]
E     At index 1 diff: 'Your score is 7\n' != 'Your score is 8\n'
```

## Test it with unittest

`unittest` groups tests as methods of a class, and compares values
with `self.assertEqual`:

```python
# check_cookie_game.py
import os

os.environ["DRAFTER_SKIP"] = "1"

import unittest

from drafter import *
from cookie_game import State, index, add_point


class TestCookieGame(unittest.TestCase):
    def test_index_shows_the_score(self):
        self.assertEqual(index(State(7)), Page(State(7), [
            Header("Cookie Game"),
            "Your score is 7\n",
            Button("Click me!", "add_point")
        ]))

    def test_add_point_adds_one(self):
        page = add_point(State(4))
        self.assertEqual(page.state, State(5))

    def test_page_mentions_the_score(self):
        self.assertTrue(assert_has(index(State(12)), "Your score is 12"))


if __name__ == "__main__":
    unittest.main()
```

Run it like any other Python file:

```text
python check_cookie_game.py
```

## Keep using Drafter's assertions

Plain `==` is exact: capitalization, spacing, and every decimal place
of a float have to match. Drafter's `assert_` functions are
[more forgiving by default](test-a-feature.md#loose-by-default-strict-when-you-want),
and they can search a page without spelling out all of it.

Each `assert_` function returns `True` when it passes and `False`
when it fails, so you can use them inside either tool. Wrap the call
in `assert` for `pytest`, or in `self.assertTrue(...)` for `unittest`,
as the `test_page_mentions_the_score` tests above do. A failure then
prints Drafter's own explanation of what differed, and the test is
also counted as failed.

Without that wrapper the test still passes when the assertion fails,
because a Drafter assertion reports a failure and carries on. It
never stops the program by itself.

## Common problems

- **Running the tests opens your site, or the tests never finish**:
  the `os.environ["DRAFTER_SKIP"] = "1"` line is missing, or it comes
  after the import of your site file. It has to come first.
- **`ModuleNotFoundError: No module named 'cookie_game'`**: run the
  tests from the folder that holds both files, and check that the
  name after `from` matches your site's file name without `.py`.
- **`SUCCESS` and `FAILURE` lines appear before the test results**:
  those come from `assert_` tests inside your site file. They run
  when the file is imported, exactly as they do when the site starts.
- **A test passes even though a Drafter assertion printed
  `FAILURE`**: the call is not wrapped in `assert` or
  `self.assertTrue(...)`.
- **Your site no longer starts when you run it**: `DRAFTER_SKIP` is
  set in your terminal as well. Set it only inside the test file, as
  shown above.

## Understand it

Routes are functions you can call, and the pages they return can be
compared like any other value. See
[Routes and pages](../concepts/routes-and-pages.md).

## See another example

[Test a feature](test-a-feature.md) covers the same site with
Drafter's built-in assertions, which need no second file.

## Look it up

[Testing functions](../reference/testing-functions.md) lists every
assertion and what it returns. The `skip` setting is described under
[start_server](../reference/start-server.md).

## Fix a problem

[Troubleshooting](../help/troubleshooting.md) covers a site that will
not start, including a leftover `DRAFTER_SKIP`.
