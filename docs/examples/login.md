---
page_type: example
title: Login flow
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: See conditional pages driven by state (and why this is not security).
---

# Login flow

## What it does

A site whose front page changes depending on whether you are "logged
in": one version greets a visitor and offers a login form, the other
greets a user by name and offers logout. One boolean in state drives
the whole personality of the app.

!!! warning "This is a simulation, not security"
    Everything in a Drafter app, including this password check, runs
    in the visitor's own browser, where anyone can read the code and
    the state. A real login system involves a server you control,
    stored password hashes, and encrypted transport; this example has
    none of those and cannot be patched into having them. Build login
    *flows* with it, never login *protection*. More information is
    in [Security honestly](../extend/security.md).

## Try it

Log in as `ada` with password `lovelace`, then log out. Try a wrong
password too.

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    username: str
    logged_in: bool


def check_password(username: str, password: str) -> bool:
    # A stand-in, not security: every visitor can read this code.
    if username == "ada" and password == "lovelace":
        return True
    if username == "admin" and password == "password":
        return True
    return False


@route
def index(state: State) -> Page:
    if state.logged_in:
        body = [
            Header("The Clubhouse"),
            "Welcome back, " + state.username + "!\n",
            Button("Log out", "do_logout")
        ]
    else:
        body = [
            Header("The Clubhouse"),
            "You are not logged in.\n",
            Button("Log in", "ask_login")
        ]
    return Page(state, body)


@route
def ask_login(state: State) -> Page:
    return Page(state, [
        Header("Log in"),
        "Username:",
        TextBox("username", state.username),
        "\nPassword:",
        TextBox("password", "", "password"),
        "\n",
        Button("Log in", "finish_login"),
        Button("Go back", "index")
    ])


@route
def finish_login(state: State, username: str, password: str) -> Page:
    state.username = username
    if check_password(username, password):
        state.logged_in = True
        return index(state)
    return Page(state, [
        "Incorrect username or password.\n",
        Button("Try again", "ask_login"),
        Button("Go back", "index")
    ])


@route
def do_logout(state: State) -> Page:
    state.logged_in = False
    return index(state)


assert_state(finish_login(State("", False), "ada", "lovelace"),
             State("ada", True))
assert_has(finish_login(State("", False), "ada", "wrong"),
           "Incorrect username or password.")
assert_state(do_logout(State("ada", True)), State("ada", False))

start_server(State("", False))
```

## The code

`check_password` is a plain helper: it answers a question and touches
nothing. The routes split the flow into moments: `index` branches on
`logged_in`, `ask_login` shows the form, `finish_login` decides, and
`do_logout` flips the flag. The whole "login system" is one boolean
and one string in state.

## How it works

`index` is a dynamic page in the sense of
[the concept](../concepts/dynamic-pages.md): same route, two
personalities, chosen by state. The branch builds a `body` list and
one shared `Page(state, body)` returns it, so the two versions cannot
drift apart structurally.

The password box, `TextBox("password", "", "password")`, uses the
third parameter (`kind`) to get dots instead of visible characters.
That is politeness toward shoulder-surfers, and the only real
security property this app has.

Note what `finish_login` does with failure: it does not log the
attempt, lock the account, or even keep the wrong password; it just
shows a page with a way back. The username *is* kept (`state.username
= username`), so the form is prefilled on retry, a small kindness
copied from real sites.

## Make it yours

1. **Modify**: add yourself as a third valid user.
2. **Modify**: after three failed attempts (a counter in state),
   make the login page suggest taking a breath.
3. **Complete**: add a members-only page that redirects the visitor
   to `index` if `logged_in` is false; every private page needs that
   same guard.
4. **Combine**: greet users differently by name ("Welcome back,
   admin" gets a broom emoji), using the branching from
   [Show different content](../add/show-different-content.md).
5. **Create**: reuse the shape for a quiz gate: the "password" is a
   riddle's answer, and logging in unlocks the good content.

## Tests

Three assertions cover the three outcomes that matter: right
password flips the flag, wrong password shows the failure page
without flipping it, and logout flips it back. `finish_login` is
easy to test precisely because `check_password` is a helper; rules
that live in helpers are rules tests can reach without pages getting
involved.

## Likely errors

- **Everyone can log in**: `check_password` must return `False` at
  the end; without the final `return False`, Python returns `None`,
  which is falsy, so this particular bug hides. The tests catch its
  siblings (a stray `return True`).
- **The private page forgot its guard**: every route is reachable by
  its address, whether or not any button points at it. A
  members-only route must itself check `state.logged_in`; the login
  page is decoration, not a wall.
- **`missing parameter` on `finish_login`**: both boxes must be on
  the submitting page, named exactly `username` and `password`.

## Related

- [Security honestly](../extend/security.md): what Drafter can and
  cannot protect, without comfort.
- [Show different content](../add/show-different-content.md): the
  branching pattern.
- [Dynamic pages](../concepts/dynamic-pages.md): the concept.
