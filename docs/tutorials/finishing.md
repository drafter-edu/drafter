---
page_type: tutorial
title: 4. Finish and test an app
level: L2
audience: S
priority: P1
prereqs: [tutorials/quiz-game]
symbols: []
outcome: Turn a working app into a tested, styled, releasable one.
---

# 4. Finish and test an app

## What you'll build

This project builds nothing new, and that is the point. It takes an
app that already works and makes it *finished*. You will freeze its
pages into regression tests that catch accidental breakage, give it a
theme and a styling pass, and add the production settings that make
it presentable to someone other than you.

The steps work on any app. The listings here use a tiny compliment
machine so that they stay short. If you built the
[quiz game](quiz-game.md), do every step on your quiz instead; that
is the real assignment.

## Try the finished app

This is the compliment machine *after* finishing: it has a theme, a
title, and no debug panel. The starting version appears in Step 1.

```python drafter height=300
from drafter import *
from dataclasses import dataclass

set_website_title("The Compliment Machine")
set_website_style("sakura")
hide_debug_information()


@dataclass
class State:
    compliments: list[str]
    position: int


COMPLIMENTS = [
    "Your code is looking sharp today.",
    "Ada the corgi would sit for you.",
    "You debug with style."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Compliment Machine"),
        state.compliments[state.position] + "\n",
        Button("Another, please", "another")
    ])


@route
def another(state: State) -> Page:
    state.position = state.position + 1
    if state.position >= len(state.compliments):
        state.position = 0
    return index(state)


assert_equal(index(State(COMPLIMENTS, 0)),
             Page(State(COMPLIMENTS, 0), [
                 Header("The Compliment Machine"),
                 "Your code is looking sharp today.\n",
                 Button("Another, please", "another")
             ]))
assert_state(another(State(COMPLIMENTS, 2)), State(COMPLIMENTS, 0))

start_server(State(COMPLIMENTS, 0))
```

## What you need

You need a working app you care about (the quiz, or the compliment
machine copied from Step 1) and one sitting. You should know how to
write an `assert_state` test; both the
[virtual pet](virtual-pet.md) and the [quiz game](quiz-game.md)
included them.

## Step 1: Start from "works"

Here is the machine before finishing. It has a plain look, the debug
panel is showing, and there are no tests.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    compliments: list[str]
    position: int


COMPLIMENTS = [
    "Your code is looking sharp today.",
    "Ada the corgi would sit for you.",
    "You debug with style."
]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Compliment Machine"),
        state.compliments[state.position] + "\n",
        Button("Another, please", "another")
    ])


@route
def another(state: State) -> Page:
    state.position = state.position + 1
    if state.position >= len(state.compliments):
        state.position = 0
    return index(state)


start_server(State(COMPLIMENTS, 0))
```

Click through it once. Which pages matter most? Those are the ones
worth freezing.

## Step 2: Freeze a page into a regression test

So far your tests have checked rules you wrote by hand. A *frozen*
test instead records a whole page you are happy with, so that any
later change to that page, whether deliberate or accidental, causes a
test failure. Drafter records everything you need while you click
around:

1. Run your app and visit the page you want to freeze.
2. Open the debug panel's **History** tab. Each visit shows the
   route call that produced it, and expanding its **Response** shows
   the full `Page(...)` your route returned, written as Python.
3. Copy the call and the page into an `assert_equal`, above
   `start_server(...)`:

```python
assert_equal(index(State(COMPLIMENTS, 0)),
             Page(State(COMPLIMENTS, 0), [
                 Header("The Compliment Machine"),
                 "Your code is looking sharp today.\n",
                 Button("Another, please", "another")
             ]))
```

Run the app again: the Tests tab shows the frozen test passing. Add
one behavior test alongside it while you are there, for the wraparound
rule:

```python
assert_state(another(State(COMPLIMENTS, 2)), State(COMPLIMENTS, 0))
```

**Predict first**: which pages of the quiz game are worth freezing?
(The results page for a known score is a strong pick: it has the most
ways to quietly break.)

## Step 3: Break it, and let the tests tell you

On your copy, "accidentally" rename the header to
`"The Compliment Machin"`. Run the app. The frozen test fails, and
its message shows exactly what changed: the expected header next to
the one your route now builds. Frozen tests exist for exactly this
situation; nobody re-reads a whole app after every edit, but the
tests check every recorded page each time the program runs.

Fix the header, and the tests pass again.

Frozen tests have one honest cost: they fail on *deliberate* changes
too. When you redesign a page on purpose, the old frozen test becomes
stale; replace it by freezing the new page the same way. A failing
frozen test is never information to ignore. It is asking whether you
meant to change the page.

## Step 4: Style it, and set it up for release

Two finishing touches remain, and both are single lines at the top of
the file, after the imports:

```python
set_website_title("The Compliment Machine")
set_website_style("sakura")
```

The title sets the name shown on the browser tab, and the theme
restyles every page at once (browse the
[theme catalog](../reference/themes.md) and pick your own). If a
single component still needs attention after the theme is applied,
use a targeted
[styling function](../add/change-appearance/helpers.md) rather than
restyling everything by hand.

Then the release settings:

```python
hide_debug_information()
```

The debug panel is a tool for you, not for your visitors, and hiding
it is the clearest sign that an app is finished. The full production
checklist, including site information for the about page and
unframing, is in
[Prepare for release](../your-project/deploy/prepare.md); apply it
when you deploy for real.

Compare your result against the finished version at the top. It is
the same app, but now it looks deliberate.

## Common problems

- **The frozen test fails immediately after you paste it**: the page
  changed between visiting it and freezing it, or the copied state
  does not match what the call produces. Freeze the page again from a
  fresh visit.
- **The frozen test is enormous**: you froze a page with a lot on it.
  That works, but the test is noisy; prefer freezing small, stable
  pages, and test big pages with a few `assert_has` checks on their
  important parts instead.
- **You called `hide_debug_information()` and now you miss the
  tests**: the tests still run and still print failures to the
  console; hiding the panel does not disable the testing. Keep the
  line commented out until you actually release.
- **The theme made your custom styling look odd**: a theme styles
  everything, so your hand-written styling now competes with it.
  Apply the theme first, then decide which manual touches are still
  needed.

## Name it

- **Regression tests**: tests that protect finished behavior from
  future accidents. Frozen pages are regression tests you get almost
  for free, because Drafter records the call and the page for every
  visit. Read more in [Test a feature](../add/test-a-feature.md) and
  [Freeze finished pages](../add/freeze-pages.md).
- **Production**: the version of your app that other people see. The
  difference between development and production is configuration, not
  code: the routes and state stay the same, but the app gains a title
  and a theme, and the debugging tools are put away.

## Make it yours

1. Freeze one more page of your app, then deliberately redesign it
   and practice replacing the stale test.
2. Pick the theme that most changes your app's personality, then the
   one that suits it best. They are rarely the same theme.
3. Add a `set_site_information(...)` call with your name and a real
   description, and find where the about page shows it.
4. Harder: on the quiz game, freeze the results page for a perfect
   score, then change the verdict wording on purpose and watch
   exactly what the failure message shows you.

## Next steps

You unlocked
[Freeze finished pages](../add/freeze-pages.md) and, with a finished
app in hand, the whole
[deployment arc](../your-project/deploy/index.md): preparing the app,
publishing it on GitHub Pages, and showing it to someone.

<div class="grid cards" markdown>

- **The road to your own app**

    ---

    The guided projects are done. Your Project applies the same
    skills to an app that is entirely yours.

    [Your Project](../your-project/index.md)

</div>
