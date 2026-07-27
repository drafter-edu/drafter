---
page_type: example
title: To-do list
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Add and remove items from list state.
---

# To-do list

## What it does

A to-do list with three pages: the list itself, a page for adding a
task, and a page for removing one by its number. It is the smallest
honest version of a whole family of apps (inventories, journals,
playlists): a list in state, and routes that grow and shrink it.

## Try it

Add a few tasks, then remove one by its number. Try removing task 99.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    tasks: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("To-Do"),
        NumberedList(state.tasks),
        Button("Add a task", "ask_new_task"),
        Button("Remove a task", "ask_remove_task")
    ])


@route
def ask_new_task(state: State) -> Page:
    return Page(state, [
        Header("Add a task"),
        "What needs doing?",
        TextBox("description"),
        "\n",
        Button("Save", "save_task"),
        Button("Cancel", "index")
    ])


@route
def save_task(state: State, description: str) -> Page:
    state.tasks.append(description)
    return index(state)


@route
def ask_remove_task(state: State) -> Page:
    return Page(state, [
        Header("Remove a task"),
        NumberedList(state.tasks),
        "Which number is done?",
        TextBox("number"),
        "\n",
        Button("Remove", "remove_task"),
        Button("Cancel", "index")
    ])


@route
def remove_task(state: State, number: str) -> Page:
    if number.isdigit():
        position = int(number)
        if 1 <= position <= len(state.tasks):
            state.tasks.pop(position - 1)
            return index(state)
    return Page(state, [
        "There is no task number " + number + ".\n",
        Button("Try again", "ask_remove_task"),
        Button("Back to the list", "index")
    ])


assert_state(save_task(State([]), "walk Babbage"),
             State(["walk Babbage"]))
assert_state(remove_task(State(["a", "b", "c"]), "2"),
             State(["a", "c"]))
assert_has(remove_task(State(["a"]), "99"), "There is no task number 99.")

start_server(State(["walk Babbage", "feed Captain"]))
```

## The code

The state is one field: `tasks`, a list of strings. Around it, the
routes pair up: `ask_new_task` shows the form, `save_task` receives
its value; `ask_remove_task` shows the form, `remove_task` acts on
it. Every path ends by handing the visitor back to `index`, directly
or through a button.

## How it works

Two details carry the design:

**People count from one, lists from zero.** The page shows tasks
numbered 1, 2, 3 (that is what `NumberedList` renders), so
`remove_task` translates: `state.tasks.pop(position - 1)`. Forgetting
the `- 1` removes the wrong task, off by one, every time.

**Bad input is a page, not a crash.** The number arrives as a string
and the route asks two questions before acting: is it digits, and is
it in range? Anything else falls through to an apologetic page with
a way back. Notice the parameter is annotated `str`, not `int`, so
the route sees whatever was typed and gets to be polite about it;
compare with the [calculator](calculator.md), which makes the same
choice for the same reason.

## Make it yours

1. **Modify**: start the list empty, and make `index` say something
   encouraging when there is nothing to do.
2. **Modify**: change "Remove" so a wrong number returns to the
   remove page directly, keeping the list visible.
3. **Complete**: add a "Remove everything" button with its own
   confirmation page.
4. **Combine**: make tasks a dataclass with `description` and
   `urgent: bool`, show urgent ones in
   [bold](../reference/styling-functions.md), and let the add form
   set it with a `CheckBox`.
5. **Create**: turn it into a packing list, a reading queue, or a
   chore rotation; the bones do not change.

## Tests

Three assertions, one per behavior worth protecting: adding appends,
removing translates the visitor's one-based number correctly (`"2"`
removes `"b"`), and a bad number produces the error page rather than
an exception. The off-by-one test is the important one; it fails
loudly if the `- 1` ever disappears.

## Likely errors

- **`IndexError` on remove**: the range check `1 <= position <=
  len(state.tasks)` is missing or wrong; without it, `pop` runs on
  positions that do not exist.
- **A `conversion error` page you did not design**: the `number`
  parameter got annotated `int`; typing "two" then bypasses your
  polite fallback. Keep it `str` and convert inside the route.
- **The list never changes**: `save_task` must `append` to
  `state.tasks`, not to a local copy, and the route must return a
  freshly built page (`return index(state)`), not a stale one.

## Related

- [Show a collection of items](../add/show-a-collection.md): the
  how-to behind the list display.
- [Pet registry](pet-registry.md): the same shape with dataclasses
  in the list.
- [NumberedList](../reference/components/lists/numberedlist.md):
  why the numbering starts at 1.
