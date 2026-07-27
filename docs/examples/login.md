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

This example is a site whose front page changes depending on whether
the visitor is "logged in". One version greets a visitor and offers
a login form; the other greets the user by name and offers a logout
button. A single boolean in the state determines which version
appears.

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

`check_password` is a plain helper function: it answers a yes-or-no
question and changes nothing. The four routes divide the flow into
steps: `index` branches on `logged_in`, `ask_login` shows the form,
`finish_login` checks the password and updates the state, and
`do_logout` sets the flag back to `False`. The entire "login system"
amounts to one boolean and one string in the state.

## How it works

`index` builds a dynamic page in the sense described in
[the concept](../concepts/dynamic-pages.md): the same route returns
two different versions of the page, chosen by the state. Each branch
builds a `body` list, and a single shared `Page(state, body)` at the
end wraps whichever list was chosen, so the two versions cannot
drift apart structurally.

The password box, `TextBox("password", "", "password")`, uses the
third parameter (`kind`) to show dots instead of visible characters.
Masking the input protects against someone reading over the
visitor's shoulder, and that is the only real security property this
app has.

Notice how `finish_login` handles failure: it does not log the
attempt, lock the account, or keep the wrong password. It only shows
a page with a way back. The username *is* kept (`state.username =
username`), so the form is prefilled when the visitor tries again, a
convenience that real sites also provide.

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

The three assertions cover the three outcomes that matter: a correct
password sets the flag to `True`, a wrong password shows the failure
page without changing the flag, and logging out resets it to
`False`. `finish_login` can be tested this directly because
`check_password` is a separate helper; rules that live in helper
functions can be tested without involving any pages.

## Likely errors

- **Everyone can log in**: `check_password` must reject every
  combination it does not recognize, so a stray `return True` lets
  everyone in; the tests catch that mistake. Forgetting the final
  `return False` happens to be harmless, because Python then returns
  `None`, which also counts as false.
- **The private page forgot its guard**: every route is reachable by
  its address, whether or not any button points at it. A
  members-only route must itself check `state.logged_in`; the login
  page does not prevent anyone from visiting other routes directly.
- **`missing parameter` on `finish_login`**: both boxes must be on
  the submitting page, named exactly `username` and `password`.

## Related

- [Security honestly](../extend/security.md) explains what Drafter
  can and cannot protect.
- [Show different content](../add/show-different-content.md) covers
  the branching pattern used in `index`.
- [Dynamic pages](../concepts/dynamic-pages.md) explains the
  underlying concept.
