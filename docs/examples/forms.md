---
page_type: example
title: Big form
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: See every core input in one form.
---

# Big form

## What it does

One page with all four core input types on it: a `TextBox`, a
`CheckBox`, a `SelectBox`, and a `TextArea`, all submitted by a single
button. The top of the page shows what is currently saved, so every
press of Submit visibly moves data from the form into the state and
back onto the page.

## Try it

Change several fields at once, then press Submit.

```python drafter height=430
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str
    available: bool
    favorite: str
    poem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Saved so far"),
        "Name: " + state.name + "\n",
        "Available: " + str(state.available) + "\n",
        "Favorite animal: " + state.favorite + "\n",
        "Poem: " + state.poem + "\n",
        HorizontalRule(),
        Header("Change the data", 2),
        "What is your name?",
        TextBox("new_name", state.name),
        "\n",
        CheckBox("new_availability", state.available),
        " I am available for adventures\n",
        "Dogs, cats, or capybaras?",
        SelectBox("new_animal", ["dogs", "cats", "capybaras"],
                  state.favorite),
        "\nWrite me a poem, please.",
        TextArea("new_poem", state.poem),
        "\n",
        Button("Submit", "save")
    ])


@route
def save(state: State, new_name: str, new_availability: bool,
         new_animal: str, new_poem: str) -> Page:
    state.name = new_name
    state.available = new_availability
    state.favorite = new_animal
    state.poem = new_poem
    return index(state)


assert_state(
    save(State("", False, "dogs", ""), "Ada", True, "capybaras", "wow"),
    State("Ada", True, "capybaras", "wow"))
assert_has(index(State("", False, "dogs", "")), Button("Submit", "save"))

start_server(State("Dr. Bart", False, "dogs", ""))
```

## The code

The `State` has one field per input, and the `save` route has one
parameter per input. The naming shows the pattern: the component
`TextBox("new_name", ...)` fills the parameter `new_name`, which is
then stored into the state field `name`. Three names per piece of
data, and only the component name and parameter name must match.

## How it works

When Submit is pressed, every input on the page is gathered and sent
to the `save` route, bound by name. The annotations do the
conversions: `new_availability: bool` turns the checkbox into
`True`/`False`, and the others arrive as the strings they are.

Each input's `default_value` comes from state (`TextBox("new_name",
state.name)`), which is what makes the form feel saved: after
`save` stores the values and re-renders through `index`, the fields
show what was just submitted rather than resetting to blank.

The `SelectBox` deserves one look: its options list is fixed in the
code, and its default must be one of the options, which
`state.favorite` always is because it can only ever hold a submitted
option.

## Make it yours

1. **Modify**: add a fourth animal to the `SelectBox` options.
2. **Modify**: swap the poem `TextArea` for a `TextBox` and decide
   what you lost.
3. **Complete**: add an `age: int` field: a `TextBox`, an
   `int`-annotated parameter, and a state field.
4. **Combine**: show the poem with its line breaks preserved using
   [PreformattedText](../reference/components/text/pre.md).
5. **Create**: rebuild this as a pet adoption form: name, species
   choice, vaccinated checkbox, and a "why this pet" essay.

## Tests

The first assertion drives the whole form in one call: `save` with
four typed values must produce exactly the expected state. The second
checks the page offers the Submit button. Route parameters make form
logic this easy to test: no clicking required, just a function call
with the values a visitor would have entered.

## Likely errors

- **A component name that matches no parameter**: the value has
  nowhere to go, and the route's unfilled parameter raises a
  [missing parameter](../help/errors/missing-parameter.md) error.
- **Two inputs with the same name** fight over one parameter; see
  [Two components share a name](../help/errors/duplicate-component-name.md).
- **A SelectBox default not in its options** raises a friendly error
  when the page is built; see
  [SelectBox default missing](../help/errors/selectbox-default-missing.md).

## Related

- [Ask the user for information](../add/ask-for-information.md): the
  how-to these inputs come from.
- [Forms and input](../concepts/forms-and-input.md): the
  name-to-parameter contract in full.
- [Calculator](calculator.md): a smaller form with more logic.
- The input reference pages:
  [TextBox](../reference/components/input/textbox.md),
  [CheckBox](../reference/components/input/checkbox.md),
  [SelectBox](../reference/components/input/selectbox.md), and
  [TextArea](../reference/components/input/textarea.md).
