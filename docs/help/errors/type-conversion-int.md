---
page_type: error
title: Could not convert text to an int
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix a failed text-to-int conversion.
error_text: "expects int but got"
---

# Could not convert text to an int

## The error

```text
Parameter 'age' expects int but got 'twenty' from the form field
'age'. Try entering a number, or change the parameter type to str.
```

or, when the text is a decimal number:

```text
Parameter 'price' expects int but got '2.5' from the form field
'price'. This looks like a decimal number; use float instead of int,
or enter a whole number.
```

## What it means

A form field's contents are always text; your route asked for an
`int`, so Drafter tried to convert the text into a whole number and
could not. The route did not run.

## Where to look

The message names the parameter and the form field. Find that
component on the page and the parameter on the route's `def` line;
then consider what a visitor might type into that field.

## Check

The hint at the end of the message distinguishes the causes:

- **"Try entering a number"**: the text was not numeric at all
  (`"twenty"`, `""`, `"3 dogs"`).
- **"use float instead of int"**: the text was a number, but not a
  whole one (`"2.5"`).

Then decide the real question: should this field only ever hold whole
numbers?

## Fix

Match the annotation to what the field means:

- A count or a whole quantity: keep `int`, and consider
  `TextBox("age", 0, "number")`, whose `"number"` kind makes the
  browser steer input toward digits.
- A measurement or money: annotate `float` instead.
- Free text that sometimes holds a number: annotate `str` and convert
  yourself when it matters, checking `isdigit()` first, as the
  [Calculator example](../../examples/calculator.md) does.

```python
@route
def set_price(state: State, price: float) -> Page:
    ...
```

## Confirm

Submit the same text again; the route should now run. Add a test that
exercises the conversion, calling the route with a typed value:
`set_price(State(...), 2.5)`.

## Prevent

When you create a `TextBox` destined for a number, decide `int` or
`float` at the same moment you write the route's annotation, and
label the field so visitors know what to type ("Age in years:").

## Understand

[Forms and input](../../concepts/forms-and-input.md) covers the
conversion table: which annotations convert, and what happens to each
kind of typed value.
