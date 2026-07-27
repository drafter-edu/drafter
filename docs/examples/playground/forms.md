---
page_type: playground
title: Forms
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Tinker with every input type.
---

# Forms

Every input, one at a time, each in a tiny app. The pattern is
always the same: the input's `name` matches a parameter of the route
the button targets. Edit freely; reloading resets everything.

The full story for all of these:
[Ask the user for information](../../add/ask-for-information.md) and
[Forms and input](../../concepts/forms-and-input.md).

## TextBox: a line of text

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Hello, " + state.name + "!\n",
        "Change my name:",
        TextBox("new_name", state.name),
        "\n",
        Button("Rename", "rename")
    ])


@route
def rename(state: State, new_name: str) -> Page:
    state.name = new_name
    return index(state)


start_server(State("stranger"))
```

## TextBox with int: typed conversion

The annotation `int` converts the text for you. Type `2.5`, then
type `cat`, and read the errors you get.

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "The jar holds " + str(state.total) + " marbles.\n",
        "Add how many?",
        TextBox("amount", 1),
        "\n",
        Button("Add", "add")
    ])


@route
def add(state: State, amount: int) -> Page:
    state.total = state.total + amount
    return index(state)


start_server(State(10))
```

## CheckBox: a yes or no

Unchecked arrives as `False`, not as nothing.

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    subscribed: bool


@route
def index(state: State) -> Page:
    return Page(state, [
        "Subscribed: " + str(state.subscribed) + "\n",
        CheckBox("wants_news", state.subscribed),
        " Send me the pigeon newsletter\n",
        Button("Save", "save")
    ])


@route
def save(state: State, wants_news: bool) -> Page:
    state.subscribed = wants_news
    return index(state)


start_server(State(False))
```

## SelectBox: one from a dropdown

Add a fourth flavor. Then make the default something else.

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    flavor: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current scoop: " + state.flavor + "\n",
        SelectBox("choice", ["vanilla", "pistachio", "blackberry"],
                  state.flavor),
        "\n",
        Button("Scoop it", "scoop")
    ])


@route
def scoop(state: State, choice: str) -> Page:
    state.flavor = choice
    return index(state)


start_server(State("vanilla"))
```

## RadioButtonGroup: one, with all options visible

The same choice as a `SelectBox`, but every option shows at once.

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    size: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Ordered size: " + state.size + "\n",
        RadioButtonGroup("picked", ["small", "medium", "absurd"],
                         state.size),
        "\n",
        Button("Order", "order")
    ])


@route
def order(state: State, picked: str) -> Page:
    state.size = picked
    return index(state)


start_server(State("small"))
```

## RelatedCheckBox: choose several, receive a list

Checkboxes sharing a name arrive together as one list parameter.

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    packed: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        "Packed so far:",
        BulletedList(state.packed),
        RelatedCheckBox("supplies", "rope"),
        " rope\n",
        RelatedCheckBox("supplies", "lantern"),
        " lantern\n",
        RelatedCheckBox("supplies", "snacks"),
        " snacks\n",
        Button("Pack", "pack")
    ])


@route
def pack(state: State, supplies: list[str]) -> Page:
    state.packed = supplies
    return index(state)


start_server(State([]))
```

## TextArea: room to write

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    note: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The fridge note says: " + state.note + "\n",
        "Rewrite it:",
        TextArea("new_note", state.note, rows=3),
        "\n",
        Button("Stick it on", "update")
    ])


@route
def update(state: State, new_note: str) -> Page:
    state.note = new_note
    return index(state)


start_server(State("buy more snacks"))
```

## DateInput and TimeInput: calendars and clocks

Date and time fields arrive as text in ISO form (`2026-07-27`,
`13:30`); annotate `str` and slice, or see the
[DateInput reference](../../reference/components/input/dateinput.md)
for richer types.

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    when: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The picnic is planned for: " + state.when + "\n",
        "Date:",
        DateInput("day"),
        "\nTime:",
        TimeInput("moment"),
        "\n",
        Button("Plan it", "plan")
    ])


@route
def plan(state: State, day: str, moment: str) -> Page:
    state.when = day + " at " + moment
    return index(state)


start_server(State("not planned yet"))
```

## Where next

- [Big form](../forms.md): several inputs cooperating on one page.
- [Lists and tables](lists-and-tables.md): displaying what forms
  collect.
