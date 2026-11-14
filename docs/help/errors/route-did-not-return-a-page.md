---
page_type: error
title: Route did not return a Page
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix a route that does not return a Page.
error_text: "Route Did Not Return a Page"
error_id: payload.verification_failed
---

# Route did not return a Page

## The error

The error page has this title:

```text
Route Did Not Return a Page
```

The sentence under the title names your route function and says what
the function gave back. This form is the most common one:

```text
Your route function `feed` finished without returning a Page. In Python,
a function that does not reach a return statement gives back None.
```

Below that sentence is the technical message:

```text
payload.verification_failed: Payload verification failed for the page 'feed':
The server did not return a Page() object from feed.
Instead, it returned None (which happens by default when you do not return anything else).
Make sure you have a proper return statement for every branch!
```

The sentence under the title is different when the route returned a
string, a list, or some other value. The Check section below quotes
each form next to its cause.

## What it means

A route is a function that returns a page. When a visitor clicks a
button, Drafter calls the route function the button names and shows
the `Page` that the function returns. Your function ran, but the
value it gave back was not a `Page`, so Drafter had no page to show
and displayed this error page in its place.

Most often the value was `None`. Python gives back `None` from any
function that reaches its last line without running a `return`
statement. Creating a `Page` is not enough, because the function
also has to `return` it.

## Where to look

The message names the route function. Open that function and follow
each path through it from the first line to the last. Every path
must end at a line that begins with `return` and gives back a
`Page`.

## Check

The sentence under the title tells you which mistake to look for.

When the sentence says the function "finished without returning a
Page", the function returned nothing. There are four usual causes:

- **No `return` at all**: the route changes the state and then ends.
  A `feed` route whose only line is
  `state.hunger = state.hunger - 1` is an example.
- **A `Page` that is created but not returned**: the last line reads
  `Page(state, ["Ada has been fed."])` with no `return` in front of
  it. Python creates the page and then discards it.
- **Another route that is called but not returned**: the last line
  reads `index(state)` where it should read `return index(state)`.
- **A `return` that only one branch of an `if` reaches**: the route
  below works while `state.hunger` is above zero. The first click
  after it reaches zero skips the `if` block, reaches the end of the
  function, and produces this error. When the error appears on some
  clicks and not on others, look for this cause first.

```python
@route
def feed(state: State) -> Page:
    if state.hunger > 0:
        state.hunger = state.hunger - 1
        return Page(state, ["Ada has been fed."])
```

The other forms of the sentence each point at one mistake:

- **"returned a plain string of text instead of a Page"**: the route
  returns the text by itself, as in `return "Ada has been fed."`.
- **"returned a list of content by itself, instead of putting that
  list inside a Page"**: the route returns the content list without
  wrapping it, as in
  `return ["Ada has been fed.", Button("Back", "index")]`.
- **"returned a State instead of a Page"**: the route returns some
  other value, here the state from `return state`. The word after
  "returned a" is the type of the value that came back.

## Fix

End every path through the function with a `return` that gives back
a `Page`:

```python
@route
def feed(state: State) -> Page:
    if state.hunger > 0:
        state.hunger = state.hunger - 1
        return Page(state, ["Ada has been fed."])
    return Page(state, ["Ada is already full."])
```

Text and lists go inside the `Page`, after the state:
`return Page(state, ["Ada has been fed."])`. When a route finishes by
showing another route's page, return that call:
`return index(state)`.

## Confirm

Click the same button again, and the page appears where the error
page was. If the route contains an `if`, repeat the click for each
branch. A test for each branch checks the same thing without
clicking:

```python
assert_has(feed(State(3)), "Ada has been fed.")
assert_has(feed(State(0)), "Ada is already full.")
```

With the broken version above, the second test reports a failure,
because `feed(State(0))` gives back `None`.

## Prevent

When you start a new route, write its `return Page(state, [...])`
line first, and then add the other lines above it. Each time you add
an `if` to a route, read the function once more for the case where
the condition is false, and check that this path also reaches a
`return`.

## Understand

[Routes and pages](../../concepts/routes-and-pages.md) explains why
every route must return a page and what Drafter does with it.
[Page](../../reference/page.md) lists what a `Page` can hold.
