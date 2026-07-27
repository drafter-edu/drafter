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

Everything so far has followed one rhythm: the visitor clicks a
button and receives a whole new page. That rhythm covers most apps,
but some behavior happens between clicks: a character counter that
follows your typing, a preview that updates as you choose, a form
that reacts before it is submitted.

Two pieces make that work, and both are variations on ideas you
already know:

**Events call routes.** Any component accepts `on_` keywords naming a
route: `on_input` (every keystroke), `on_change` (a value changed and
the field lost focus), `on_focus`, `on_blur`, `on_click`, and several
others. `TextBox("draft", "", on_input="count")` means: whenever the
visitor types, run the route named `count`. The event's values arrive
as parameters by name, following the same contract that forms use.

**Routes can return less than a page.** A route that may be triggered
many times per second should not rebuild the entire page each time.
Instead of a `Page`, it can return:

- [Fragment](../reference/fragment.md): new content for one part of
  the page, chosen by a `target` (an element id like `"#counter"`,
  or `None` for the element that triggered the event).
- [Update](../reference/update.md): a state change with no visible
  content at all.
- [Redirect](../reference/redirect.md): an instruction to run a
  different route instead, useful after finishing something.

## See it

This example is a character counter that follows the keyboard. The
`Output` component creates a named region, and the `Fragment` targets
it by id:

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

Trace the cause and effect: each keystroke fires `on_input`, which runs
`count` with the box's current text as `draft`; the returned
`Fragment` replaces only the contents of the `counter` region. The
rest of the page never re-renders, which is why the cursor never
loses its place in the box.

## What this means for your code

- Event routes are ordinary routes: `@route`, parameters by name,
  testable by calling them
  (`assert_has(count("hello"), "5 characters")`).
- Give every `Fragment` a destination: an
  [Output](../reference/components/input/output.md) region or any
  component with an `id`, and a matching `target="#that_id"`.
- State still flows the usual way. An event route that changes state
  should take `state` first and pass it into the `Fragment`
  (`Fragment(state, [...])`), or use an `Update` when there is
  nothing to show.
- `on_input` fires on every keystroke, so keep its route small:
  compute a string and return a small fragment. Expensive work
  belongs behind a button instead.
- Prefer full pages until they cause a real problem. Whole-page
  updates are easier to reason about, easier to test, and behave most
  predictably with the back button. Use fragments when rebuilding the
  whole page visibly interferes with the visitor, as it does while
  they are typing.

## Where people get confused

- **"The fragment replaced the wrong thing."** With `target=None`,
  the fragment lands in the element that fired the event. To place
  it elsewhere, give the destination an id and target it explicitly.
- **"My counter resets the text box."** The route should return a
  fragment targeting the display region, not a `Page`; a full page
  rebuilds the box mid-typing.
- **"The event route never fires."** The `on_` name must be a
  supported event (`on_input`, not `on_type`), and its value must
  name a real route, exactly like a button target.
- **"State changed but the page disagrees."** A `Fragment` only
  redraws its target. If an event changes state that other parts of
  the page display, those parts are stale until the next full page.
  That situation is a sign to reconsider the design: either target a
  region that includes everything affected, or return a full page
  from a button click instead.

## Go deeper

- [Add live behavior](../add/live-behavior.md) has recipes for a
  counter, a silent save, and a redirect after submitting.
- [Fragment](../reference/fragment.md), [Update](../reference/update.md),
  and [Redirect](../reference/redirect.md) describe the exact
  behavior of each return type.
- [Timers](../add/timers.md) covers events that fire on a schedule
  instead of in response to an action.
