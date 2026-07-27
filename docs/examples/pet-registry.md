---
page_type: example
title: Pet registry
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Work with nested data as a list of dataclasses.
---

# Pet registry

## What it does

A registry of pets: each pet is a dataclass with a name, species, and
age, the state holds a list of them, and a `Table` shows the whole
collection at once. New pets arrive through a form whose fields map
one-to-one onto the dataclass.

This is the *nested data* pattern, and it is the shape of most final
projects: a dataclass for the thing, a list of them in state, pages
to view and add.

## Try it

Register a pet of your own, then view the table.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    age: int


@dataclass
class State:
    pets: list[Pet]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Registry"),
        "There are " + str(len(state.pets)) + " pets registered.\n",
        Button("View the pets", "view_pets"),
        Button("Register a pet", "ask_new_pet")
    ])


@route
def view_pets(state: State) -> Page:
    return Page(state, [
        Header("All Pets"),
        Table(state.pets),
        Button("Back", "index")
    ])


@route
def ask_new_pet(state: State) -> Page:
    return Page(state, [
        Header("Register a pet"),
        "Name:",
        TextBox("name"),
        "\nSpecies:",
        SelectBox("species", ["dog", "cat", "capybara"]),
        "\nAge:",
        TextBox("age", 1),
        "\n",
        Button("Register", "save_pet"),
        Button("Cancel", "index")
    ])


@route
def save_pet(state: State, name: str, species: str, age: int) -> Page:
    state.pets.append(Pet(name, species, age))
    return index(state)


assert_state(save_pet(State([]), "Domino", "cat", 3),
             State([Pet("Domino", "cat", 3)]))
assert_has(view_pets(State([Pet("Ada", "dog", 4)])),
           Table([Pet("Ada", "dog", 4)]))

start_server(State([
    Pet("Ada", "dog", 4),
    Pet("Captain", "cat", 7)
]))
```

## The code

Two dataclasses with different jobs: `Pet` describes one thing;
`State` holds the app's whole memory, which here is just the list of
pets. `Table(state.pets)` does the display work: give it a list of
dataclasses and it makes a header row from the field names and a row
per pet.

The form and the dataclass mirror each other on purpose: three
fields, three inputs, three parameters. `save_pet` is one line of
actual work: build the `Pet`, append it.

## How it works

The interesting move is in `save_pet`'s signature:
`age: int`. The text box delivers text, the annotation converts it,
and the `Pet` gets a real number. That matters later: an age stored
as `"3"` would sort and compare as text.

Note what `index` does *not* do: it does not show the pets. Keeping
the big table on its own page keeps the front page fast to read, and
it means the table page can grow features (sorting, filtering)
without crowding the entrance.

## Make it yours

1. **Modify**: add Babbage the small black mutt to the starting
   data.
2. **Modify**: add a `vaccinated: bool` field, a `CheckBox` on the
   form, and watch the table grow a column by itself.
3. **Complete**: show the oldest pet's name on the front page (a
   loop, a comparison, no sorting needed).
4. **Combine**: add per-pet detail pages using an `Argument` with
   the pet's name, the pattern from
   [Show different content](../add/show-different-content.md).
5. **Create**: this app with different nouns is a library, a garden
   log, or a team roster. Rename, adjust fields, go.

## Tests

The first test checks the whole add path: calling `save_pet` with
form values yields a state containing the constructed `Pet`. The
second checks display structurally: the page contains the expected
`Table`. Testing tables needs the component form,
`assert_has(page, Table([...]))`; a text needle does not reach
inside a table's rows.

## Likely errors

- **Ages that refuse to convert**: typing "three" into the age box
  stops the route with a
  [conversion error](../help/errors/type-conversion-int.md). If you
  would rather handle it politely, annotate `str` and convert
  yourself, as the [to-do list](todo-list.md) does with numbers.
- **A `Pet` in the page content**: `Page` cannot render a bare
  dataclass; it goes in a `Table`, or you show its fields as
  strings. See
  [Page content must be a list](../help/errors/page-content-invalid.md).
- **Field order mixed up**: `Pet(name, species, age)` takes its
  values in dataclass field order; swapping them produces pets aged
  "dog".

## Related

- [Show a collection of items](../add/show-a-collection.md): the
  how-to for lists and tables.
- [Table](../reference/components/data/table.md): what it accepts
  and renders.
- [To-do list](todo-list.md): the same shape with plain strings.
- [State](../concepts/state.md): why nested dataclasses are the
  recommended way to grow state.
