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

Nothing new, and that is the point. This project takes an app that
already works and makes it *finished*: its pages frozen into
regression tests that catch accidental breakage, a theme and a
styling pass, and the production settings that make it presentable to
someone who is not you.

The steps work on any app. The listings here use a tiny compliment
machine so they stay short; if you built the
[quiz game](quiz-game.md), do every step on your quiz instead, which
is the real assignment.

## Try the finished app

This is the compliment machine *after* finishing: themed, titled, no
debug panel. The starting version appears in Step 1.

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

A working app you care about (the quiz, or the compliment machine
copied from Step 1) and one sitting. You should know how to write an
`assert_state` test; the
[virtual pet](virtual-pet.md) and [quiz game](quiz-game.md) both did.

## Step 1: Start from "works"

Here is the machine before finishing: plain look, debug panel
showing, no tests.

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
later change that alters it, deliberate or accidental, gets noticed.
Drafter records everything you need while you click around:

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
its message shows exactly what changed: the expected header against
the one your route now builds. This is what frozen tests are for;
nobody re-reads a whole app after every edit, but the tests do.

Fix the header. Green again.

One honest cost: frozen tests fail on *deliberate* changes too. When
you actually redesign a page, the old frozen test is stale; replace
it by freezing the new page the same way. A failing frozen test is
never information to ignore, it is a question: "did you mean to
change this?"

## Step 4: Style it, and set it up for release

Two finishing touches, both one-liners at the top of the file, after
the imports:

```python
set_website_title("The Compliment Machine")
set_website_style("sakura")
```

The title names the browser tab; the theme restyles every page at
once (browse the [theme catalog](../reference/themes.md) and pick
your own). If any single component needs attention after the theme
does its work, a targeted
[styling function](../add/change-appearance/helpers.md) is the tool;
resist restyling everything by hand.

Then the release settings:

```python
hide_debug_information()
```

The debug panel is your tool, not your visitors'. Hiding it is the
single biggest "this is finished now" signal. The full production
checklist, including site information for the about page and
unframing, is
[Prepare for release](../your-project/deploy/prepare.md); apply it
when you deploy for real.

Compare your result against the finished version at the top. Same
app, but it looks like someone meant it.

## Common problems

- **The frozen test fails immediately after you paste it**: the page
  changed between visiting it and freezing it, or the copied state
  does not match what the call produces. Freeze the page again from a
  fresh visit.
- **The frozen test is enormous**: you froze a page with a lot on it.
  That is legal but noisy; prefer freezing small, stable pages, and
  test big pages with a few `assert_has` checks on their important
  parts instead.
- **`hide_debug_information()` and now you miss the tests**: the
  tests still run and still print failures to the console; the panel
  is hidden, not the testing. Keep the line commented out until you
  actually release.
- **The theme made your custom styling look odd**: themes style
  everything; your hand-styling now competes with them. Apply the
  theme first, then re-judge which manual touches are still needed.

## Name it

- **Regression tests**: tests that protect finished behavior from
  future accidents. Frozen pages are regression tests you get almost
  for free, because Drafter records the call and the page for every
  visit. More in [Test a feature](../add/test-a-feature.md) and
  [Freeze finished pages](../add/freeze-pages.md).
- **Production**: the version of your app that other people see. The
  difference between development and production is configuration, not
  code: same routes, same state, but titled, styled, and with the
  debugging tools put away.

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
[deployment arc](../your-project/deploy/index.md): prepare, publish
on GitHub Pages, and show it to someone.

<div class="grid cards" markdown>

- **The road to your own app**

    ---

    The guided projects are done. Your Project walks the same skills
    toward an app that is entirely yours.

    [Your Project](../your-project/index.md)

</div>
