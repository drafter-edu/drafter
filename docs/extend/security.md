---
page_type: concept
title: Security honestly
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Know exactly what is and is not protected.
---

# Security honestly

## In one sentence

Nothing in a Drafter app is secret or protected, and knowing that
precisely is what lets you build course projects safely.

## The idea

Every part of your app ships to every visitor: the Python source,
the data files you bundled, the state as it changes. The visitor's
browser must have all of it to run the app, and browsers let their
owners inspect everything they run. One right-click on your
deployed site reaches your full source code.

This is not a flaw to work around; it is the architecture. A
Drafter app is more like handing someone a board game than
running a bank teller window: they have the whole box.

What follows from that, concretely:

- **No secrets in code.** Passwords, API keys, quiz answer keys,
  and "hidden" pages are all readable by anyone who looks.
- **Login pages are simulations.** They are excellent practice at
  building flows (and a fine project feature), but they gate
  nothing: the "locked" page's code is in the same file the
  visitor already has.
- **Validation is a courtesy, not a defense.** Checking that a
  number is positive before using it makes your app pleasant and
  robust. It does not stop anyone from anything; a visitor can
  edit state directly in the debugger.
- **No visitor can hurt any other visitor.** The upside of every
  visitor running a private copy: there is no shared server to
  corrupt, and nothing one visitor does is visible to another.
  The person a student's code could mislead is its own visitor,
  which is why honesty in the interface still matters.

## See it

One genuine protection does exist, and you get it for free: text
is displayed as text. When a visitor types HTML or script tags
into your form, Drafter escapes it rather than executing it. Try
typing `<b>hello</b>` or `<script>alert(1)</script>` into this
demo:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    shout: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Echo Chamber"),
        "You said: " + state.shout + "\n",
        TextBox("message"),
        "\n",
        Button("Shout", "shout_it")
    ])


@route
def shout_it(state: State, message: str) -> Page:
    state.shout = message
    return index(state)


start_server(State("nothing yet"))
```

The tags appear as literal text on the page. This protection has
one deliberate hole: `RawHTML` renders its content as real HTML.
That is its job, so the rule is short: never put text a visitor
typed inside `RawHTML`.

## What this means for your code

- Keep real secrets out of the project entirely. If a feature
  seems to need an API key, the key will be public; use keyless
  public APIs, or accept that exposure knowingly for a throwaway
  key.
- Build the login flow if your project wants one, and label it in
  your documentation as a simulation. Saying so out loud reads as
  understanding, not as a shortcut.
- Validate inputs for kindness (clear messages, no crashes), not
  for control.
- Display visitor text as plain text and let Drafter's escaping
  work. Reach for `RawHTML` only with content you wrote yourself.

## Where people get confused

- "I'll hide the answers in a separate file." Bundled files ship
  to the browser with everything else.
- "The compiled site looks like gibberish, so it's obscured." The
  source is in there, readable, and the browser's tools display
  it nicely.
- "Browser storage would make my login real." Anything stored in
  the visitor's browser is controlled by that visitor; it
  persists data, it does not protect it.
- "So security is impossible in Python?" Security is impossible
  *without a server you control*. Frameworks like Flask put
  secret-keeping and real accounts on a machine visitors never
  see; that is the moment to move, and
  [Moving on to Flask](flask.md) is the bridge.

## Go deeper

- [How Drafter works](../start/how-drafter-works.md): the runtime
  model that makes all of this true.
- [The login flow example](../examples/login.md): a well-labeled
  simulation done properly.
- [Expert misconceptions](../teach/expert-misconceptions.md):
  the same facts, phrased for experienced developers.
