---
page_type: error
title: Page content must be a list of strings, numbers, booleans, or components
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix invalid Page content.
error_text: "must be a list of strings, numbers, booleans, or components"
---

# Page content must be a list of strings, numbers, booleans, or components

## The error

The error page has this title:

```text
Page Content Problem
```

The sentence under the title says which item is the problem:

```text
Item number 0 in this Page's content list is a Pet, but every item needs
to be text, a number, a boolean, or a component.
```

The technical message below it reads:

```text
request.route_execution_failed: Error while processing request for URL 'index':
The content of a Page must be a list of strings, numbers, booleans, or
components. Found Pet at index 0 instead.
```

The position counts from zero, so "index 0" is the first item of the
content list and "index 1" is the second.

Two other forms of this error have the same title. When the value
sits where the whole list belongs, the messages leave out the position
("The content you returned in this Page was a Pet", and "Found Pet
instead."). When the value is inside another component, such as a
`Div` or a `BulletedList`, the sentence under the title says where the
value is:

```text
Your page content includes a value that Drafter does not know how to
display: a Pet value (Pet(name='Ada', age=3)). It is located at: the Div
at index 0, the item at index 0.
```

## What it means

A `Page` displays a list of strings, numbers, booleans, and
components. Something you put into that list, or in place of the
list itself, was none of those. It may have been a dataclass, a
dictionary, or a nested list. Drafter stopped rather than guess how
to display it.

## Where to look

Start with the route named in the technical message. Look at the
`Page(...)` call it returns and count through the content list to the
position the message gives.

## Check

Each cause below is followed by the end of the technical message it
produces:

- **A dataclass in the list**: `Page(state, [state.pet])` produces
  "Found Pet at index 0 instead." Show its fields
  (`state.pet.name`) or use a component like
  [Table](../../reference/components/data/table.md) built for
  structured data.
- **A nested list**: `Page(state, ["Pets:", state.names])` puts a
  whole list inside the content list and produces "Found list at
  index 1 instead." Join it into one string
  (`", ".join(state.names)`) or use
  [BulletedList](../../reference/components/lists/bulletedlist.md).
- **A dictionary in the list**: `Page(state, ["Ages:", {"Ada": 3}])`
  produces "Found dict at index 1 instead." Pull out the values you
  want to show, or give the dictionary to a component built for it.
- **`None` in the list**: the message says "Found NoneType at index
  1 instead." This usually comes from a helper function that has no
  `return` statement, so calling it inside the list puts `None`
  there.
- **A value where the list belongs**: `Page(state, state.pet)`
  produces "Found Pet instead." The same message with your state
  class's name ("Found State instead.") means the two arguments are
  in the wrong order, as in `Page(["Hello"], state)`. The state comes
  first.
- **Missing square brackets around several items**:
  `Page(state, "Hello", Button("Go", "index"))` produces "The content
  of a Page must be given as one list, but more was written after the
  content: a Button." A `Page` takes the state, then one content
  list, and nothing else without a name. The first hint under "What To
  Try Next" shows the call with the brackets added, as in
  `Page(state, ['Hello', Button(...)])`.
- **CSS or JavaScript given without its name**:
  `Page(state, ["Hello"], "h1 { color: red; }")` produces the same
  message, ending "a str". Name the value, as in
  `Page(state, ["Hello"], css="h1 { color: red; }")`. The `css` and
  `js` values must be text or a list of text. `css=5` produces "The
  css of a Page must be a string or a list of strings, but got an
  int."

A single string, number, or component in place of the list is not an
error. `Page(state, "Hello")` shows the same page as
`Page(state, ["Hello"])`. Plain numbers and booleans are also
accepted as items: `Page(state, ["Score:", state.score])` displays
the score directly, with no `str()` needed.

## Fix

Keep everything inside one flat list of strings, numbers, booleans,
and components:

```python
@route
def index(state: State) -> Page:
    return Page(state, [
        "Score:",
        state.score,
        Button("Play", "play")
    ])
```

## Confirm

The page renders. A structural test pins it down:
`assert_has(index(State(3)), "3")`.

## Prevent

Keep the content list flat: helper functions that produce several
components should return a list you add with `+`, not nest as an
item. Structured values (dataclasses, dictionaries, lists) need to
be unpacked into their parts or given to a component that knows how
to display them.

## Understand

[Page](../../reference/page.md) documents exactly what content can
hold; [Routes and pages](../../concepts/routes-and-pages.md)
explains the underlying concept.
