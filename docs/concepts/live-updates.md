---
page_type: concept
title: Live updates
level: L3
audience: S
priority: P1
prereqs: [concepts/dynamic-pages]
symbols: []
outcome: Understand events and partial updates.
---

# Live updates

## In one sentence

Events let a component call a route the moment something happens
(typing, choosing, hovering), and the route can respond by replacing
just part of the page instead of all of it.

## The idea

Everything so far follows one rhythm: click a button, get a whole new
page. That rhythm covers most apps, but some behavior lives between
clicks: a character counter that follows your typing, a preview that
updates as you choose, a form that reacts before it is submitted.

Two pieces make that work, and they are both things you already know
wearing new clothes:

**Events call routes.** Any component accepts `on_` keywords naming a
route: `on_input` (every keystroke), `on_change` (a value changed and
the field lost focus), `on_focus`, `on_blur`, `on_click`, and
friends. `TextBox("draft", "", on_input="count")` means: whenever the
visitor types, run the route named `count`. The event's values arrive
as parameters by name, the same contract forms use.

**Routes can return less than a page.** A route triggered many times
a second should not rebuild the world. Instead of a `Page`, it can
return:

- [Fragment](../reference/fragment.md): new content for one part of
  the page, chosen by a `target` (an element id like `"#counter"`,
  or `None` for the element that triggered the event).
- [Update](../reference/update.md): a state change with no visible
  content at all.
- [Redirect](../reference/redirect.md): "go run this other route
  instead", useful after finishing something.

## See it

A character counter that follows the keyboard. The `Output` component
is a named region; the `Fragment` targets it by id:

```python drafter height=260
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Haiku Drafting Desk"),
        "Write, and watch the count:",
        TextBox("draft", "", on_input="count"),
        "\n",
        Output("counter", ["0 characters so far"])
    ])


@route
def count(draft: str) -> Fragment:
    return Fragment([
        str(len(draft)) + " characters so far"
    ], target="#counter")


start_server()
```

Cause and effect: each keystroke fires `on_input`, which runs
`count` with the box's current text as `draft`; the returned
`Fragment` replaces only the contents of the `counter` region. The
rest of the page never re-renders, which is why the cursor never
loses its place in the box.

## What this means for your code

- Event routes are ordinary routes: `@route`, parameters by name,
  testable by calling them
  (`assert_has(count("hello"), "5 characters")`).
- Give a `Fragment` a home to land in: an
  [Output](../reference/components/input/output.md) region or any
  component with an `id`, and a matching `target="#that_id"`.
- State still flows the usual way. An event route that changes state
  should take `state` first and pass it into the `Fragment`
  (`Fragment(state, [...])`), or use an `Update` when there is
  nothing to show.
- `on_input` fires a lot. Keep its route small: compute a string,
  return a small fragment. Anything heavy belongs behind a real
  button.
- Prefer full pages until they hurt. A whole-page rhythm is easier to
  reason about, easier to test, and what the back button understands
  best. Reach for fragments when re-rendering everything visibly
  fights the visitor, as it does with typing.

## Where people get confused

- **"The fragment replaced the wrong thing."** With `target=None`,
  the fragment lands in the element that fired the event. To land
  somewhere else, give that somewhere an id and target it explicitly.
- **"My counter resets the text box."** The route should return a
  fragment targeting the display region, not a `Page`; a full page
  rebuilds the box mid-typing.
- **"The event route never fires."** The `on_` name must be a
  supported event (`on_input`, not `on_type`), and its value must
  name a real route, exactly like a button target.
- **"State changed but the page disagrees."** A `Fragment` only
  redraws its target. If an event changes state that other parts of
  the page display, those parts are stale until the next full page.
  That is a design smell: either target a region that includes
  everything affected, or use the click-for-a-page rhythm.

## Go deeper

- [Add live behavior](../add/live-behavior.md): recipes (counter,
  silent save, redirect after submit).
- [Fragment](../reference/fragment.md), [Update](../reference/update.md),
  [Redirect](../reference/redirect.md): exact behavior of each.
- [Timers](../add/timers.md): events that fire on a schedule instead
  of an action.
