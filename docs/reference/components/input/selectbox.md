---
page_type: component
title: SelectBox
level: L3
audience: S
priority: P1
prereqs: []
symbols:
  - SelectBox
outcome: Choose one option from a list.
---

# SelectBox

Group: [Input](../index.md#input)

## Description

A `SelectBox` is a dropdown menu. The visitor picks exactly one
option from a list you define, and the chosen option's text arrives
at the route as a parameter with the box's name. Use it when there
are many options or little room on the page; when all the options
should be visible at once, use a
[RadioButtonGroup](radiobuttongroup.md). With `multiple=True`, the
visitor can pick several options, and the route receives a list.

## Syntax

```python
SelectBox(name, options)
SelectBox(name, options, default_value)
SelectBox(name, options, multiple=True)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `options` | `list[str]` | required | The choices, shown in order. Non-string values are converted to text. |
| `default_value` | `str` | first option | The pre-chosen option. Must be one of the options, or the page stops with a [friendly error](../../../help/errors/selectbox-default-missing.md). |
| `allow_missing` | `bool` | `False` | Skip the default-must-be-an-option check. Rarely wanted. |

Like every component, `SelectBox` also accepts
[styling and attribute keywords](../../keyword-attributes.md). The
HTML attributes it recognizes as keywords are `multiple`, `size`, and
`required`. `multiple=True` lets the visitor choose several options,
as the second example below shows, and `size=4` displays four options
at once in a list instead of a dropdown. `required=True` adds the
attribute, but a button still runs its route when nothing is chosen.

`disabled` is not on that list. Drafter turns a keyword it does not
recognize into a CSS style, which the browser ignores, and it reports
no error. [Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains the keyword rule.

## Examples

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    destination: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Trip Planner"),
        "Current destination: " + state.destination + "\n",
        SelectBox("choice",
                  ["aquarium", "museum", "volcano", "library"],
                  state.destination),
        "\n",
        Button("Choose", "choose")
    ])


@route
def choose(state: State, choice: str) -> Page:
    state.destination = choice
    return index(state)


start_server(State("aquarium"))
```

With `multiple=True`, the box becomes a list in which the visitor can
select several options, and the route receives all of them as a list.
Annotate the receiving parameter as `list[str]`:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    toppings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pizza Order"),
        "Toppings on the order: " + str(len(state.toppings)) + "\n",
        BulletedList(state.toppings),
        "Choose your toppings:\n",
        SelectBox("chosen",
                  ["cheese", "olives", "basil", "peppers"],
                  multiple=True),
        "\n",
        Button("Order", "order")
    ])


@route
def order(state: State, chosen: list[str]) -> Page:
    state.toppings = chosen
    return index(state)


start_server(State([]))
```

## Notes

- The route always receives one of the option strings, which makes
  `SelectBox` the input least in need of validation: the visitor
  cannot type something unexpected.
- Passing the current state value as the default, as above, keeps
  the box showing what was last chosen.
- Each option is both the display text and the submitted value.
  `SelectBox` cannot show one label while sending a different code;
  if you need that, receive the label and look up the matching code
  inside the route.
- With `multiple=True`, a parameter annotated `list[str]` receives
  the chosen options as a list of strings. When nothing is selected
  the list is empty, and the route still runs. A bare `list`
  annotation, or no annotation, receives the same list. A parameter
  annotated `str` receives one option's text when exactly one is
  selected, and otherwise the text of the whole list, such as
  `"['cheese', 'basil']"` or `"[]"`, which is rarely what a route
  needs.
- On a computer, the visitor selects several options by holding
  Ctrl (Command on a Mac) while clicking each one.
- `default_value` preselects at most one option, even when
  `multiple=True`.

## Accessibility

Give the box a visible label (the "Current destination:" text or a
[Label](label.md)); without one, the dropdown's purpose is unclear
to everyone, and especially to screen-reader users.

## Related components

- [RadioButtonGroup](radiobuttongroup.md): the same kind of choice
  with all options visible.
- [RelatedCheckBox](relatedcheckbox.md): choose several options
  instead.
- [Ask the user for information](../../../add/ask-for-information.md)
  is the how-to guide, with a recipe that puts a dropdown in a form.

## External links

- [The select element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/select)
