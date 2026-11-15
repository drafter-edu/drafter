---
page_type: component
title: TextBox
level: L2
audience: S
priority: P0
prereqs: []
symbols:
  - TextBox
outcome: Collect a line of text or a number.
---

# TextBox

Group: [Input](../index.md#input)

## Description

A `TextBox` collects a single line of typed input. When a button on
the page is clicked, the box's contents are delivered to the target
route as a parameter with the same name as the box. The parameter's
type annotation decides what arrives: `str` for text, `int` or `float`
for numbers, converted for you.

## Syntax

```python
TextBox(name)
TextBox(name, default_value)
TextBox(name, default_value, kind)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, which must match a parameter of the route that receives it. Must be a valid Python parameter name. |
| `default_value` | `str`, `int`, or `float` | `""` | What the box contains before the visitor types. Converted to text for display. |
| `kind` | `str` | `"text"` | The HTML input type: `"text"`, `"password"`, `"email"`, `"number"`, or another valid type. |

Like every component, `TextBox` also accepts
[styling and attribute keywords](../../keyword-attributes.md). The
HTML attributes it recognizes as keywords are `placeholder`,
`maxlength`, `minlength`, `size`, `pattern`, `alt`, `min`, `max`,
`step`, `list`, `required`, `disabled`, `readonly`, and
`autocomplete`. (`list` takes the `id` of an HTML `<datalist>`, not a
Python list.) Drafter turns any other keyword it does not recognize
into a CSS style;
[Plain HTML attributes](../../keyword-attributes.md#plain-html-attributes)
explains that rule.

Some of these keywords change what the box itself allows.
`maxlength=20` stops typing after 20 characters. With
`kind="number"`, the `min`, `max`, and `step` keywords set where the
box's arrow buttons stop and how far each click moves.
`disabled=True` and `readonly=True` both block typing. A read-only
box still sends its value to the route. A disabled box does not, so
the route's parameter needs a default value.

None of these keywords stops a route from running, because Drafter
does not ask the browser to check the form when a button is clicked.
A box marked `required=True` can be left empty, and
`TextBox("age", kind="number", min=0, max=10)` still lets the visitor
type `50` and send it. Check the value inside the route.

## Examples

This first example collects text and shows it back:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    motto: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current motto: " + state.motto + "\n",
        "A new motto:",
        TextBox("new_motto", state.motto),
        "\n",
        Button("Update", "update")
    ])


@route
def update(state: State, new_motto: str) -> Page:
    state.motto = new_motto
    return index(state)


start_server(State("Onward!"))
```

Annotate the parameter as `int` and Drafter converts the typed text
into a number before your route sees it:

```python drafter height=220
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Total so far: " + str(state.total) + "\n",
        "Add this much:",
        TextBox("amount", 5),
        "\n",
        Button("Add", "add")
    ])


@route
def add(state: State, amount: int) -> Page:
    state.total = state.total + amount
    return index(state)


start_server(State(0))
```

## Notes

- Passing the current state value as `default_value`, as both examples
  do, keeps the box filled in with what the visitor last entered.
- If the visitor types something that cannot become the annotated
  type, the route does not run; a friendly
  [conversion error](../../../help/errors/type-conversion-int.md)
  explains the problem. For example, `2.5` cannot become an `int`;
  if decimal values should be accepted, annotate the parameter as
  `float`.
- An empty box gives a `str` parameter `""`. For an `int` or `float`
  parameter, an empty box is an error unless the parameter has a
  default value, which is then used, or allows `None`, as in
  `age: int | None`. [Blank values](../../route.md#blank-values) has
  the full rule.
- A box whose `name` matches no parameter of the target route is not
  an error, and its value is dropped. The debug panel lists a
  [warning](../../../help/errors/missing-parameter.md#a-related-warning-a-form-field-with-no-matching-parameter)
  when the name is close to a parameter that received nothing. A route
  parameter no box fills produces a
  [missing parameter](../../../help/errors/missing-parameter.md) error.
- For multi-line input, use [TextArea](textarea.md).

## Accessibility

Put a visible label before every box, either a plain string (as in the
examples) or a [Label](label.md) component associated with the box, so
visitors and screen readers know what to type.

## Related components

- [TextArea](textarea.md): multi-line text.
- [SelectBox](selectbox.md), [CheckBox](checkbox.md): choices instead
  of typing.
- [Label](label.md): captions for inputs.
- [Ask the user for information](../../../add/ask-for-information.md)
  is the how-to guide for building a form from inputs like this one.

## External links

- [The input element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input)
