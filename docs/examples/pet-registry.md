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

This example keeps a registry of pets. Each pet is a dataclass with
a name, a species, and an age; the state holds a list of pets; and a
`Table` shows the whole collection at once. New pets are added
through a form whose fields map one-to-one onto the dataclass
fields.

This is the *nested data* pattern, and it is the structure behind
most final projects: a dataclass that describes one kind of thing, a
list of those objects in the state, and pages to view the collection
and add to it.

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

The two dataclasses have different jobs. `Pet` describes a single
pet, while `State` holds the app's whole memory, which in this case
is only the list of pets. `Table(state.pets)` handles the display:
given a list of dataclasses, it builds a header row from the field
names and one row per pet.

The form and the dataclass deliberately mirror each other: three
dataclass fields, three form inputs, and three route parameters.
`save_pet` does its work in a single line: it builds the `Pet` and
appends it to the list.

## How it works

The most important detail is in `save_pet`'s signature: `age: int`.
The text box delivers text, but the annotation tells Drafter to
convert it, so the `Pet` receives a real number. The conversion
matters later, because an age stored as the string `"3"` would sort
and compare as text.

Note what `index` does *not* do: it does not show the pets. Keeping
the big table on its own page keeps the front page fast to read, and
it leaves room for the table page to grow features (sorting,
filtering) later.

## Make it yours

1. **Modify**: add Babbage the small black mutt to the starting
   data.
2. **Modify**: add a `vaccinated: bool` field and a `CheckBox` on
   the form, and notice that the table gains a column automatically.
3. **Complete**: show the oldest pet's name on the front page. A
   loop and a comparison are enough; no sorting is needed.
4. **Combine**: add per-pet detail pages using an `Argument` with
   the pet's name, following the pattern from
   [Show different content](../add/show-different-content.md).
5. **Create**: with different nouns, this app becomes a library, a
   garden log, or a team roster. Rename the dataclasses, adjust the
   fields, and build from there.

## Tests

The first test checks the whole add path: calling `save_pet` with
form values yields a state containing the constructed `Pet`. The
second checks the display structurally: the page must contain the
expected `Table`. Testing a table requires the component form,
`assert_has(page, Table([...]))`, because searching for a plain
string will not match content inside a table's rows.

## Likely errors

- **An age that cannot be converted**: typing "three" into the age
  box stops the route with a
  [conversion error](../help/errors/type-conversion-int.md). If you
  would rather handle bad input politely, annotate the parameter as
  `str` and convert the value yourself, as the
  [to-do list](todo-list.md) does with numbers.
- **A `Pet` in the page content**: `Page` cannot render a bare
  dataclass. Put the pet in a `Table`, or show its fields as
  strings. See
  [Page content must be a list](../help/errors/page-content-invalid.md).
- **Field order mixed up**: `Pet(name, species, age)` takes its
  values in dataclass field order, so swapping the values produces
  nonsense, such as a pet whose age is "dog".

## Related

- [Show a collection of items](../add/show-a-collection.md) is the
  how-to guide for lists and tables.
- [Table](../reference/components/data/table.md) describes what the
  component accepts and renders.
- [To-do list](todo-list.md) uses the same structure with plain
  strings.
- [State](../concepts/state.md) explains why nested dataclasses are
  the recommended way to grow state.
