---
page_type: error
title: Could not convert a value to the parameter's type
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Fix a failed parameter type conversion.
error_text: "expects float but got"
---

# Could not convert a value to the parameter's type

## The error

```text
Parameter 'price' expects float but got 'free' from the form field
'price'. Try entering a number, or change the parameter type to str.
```

The same shape appears for other target types, always naming the
parameter, the expected type, the value that arrived, and where it
came from, plus a hint. (The `int` version has
[its own entry](type-conversion-int.md), being the most common.)

## What it means

Form values arrive as text, and Drafter converts them to whatever
type the route's parameter is annotated with. This value could not
become that type, so the route did not run.

## Where to look

The component named as the source, and the annotation on the
route's `def` line. Then think about what a visitor could type or
choose there.

## Check

The expected type in the message tells you which conversion failed:

- **`float`**: the text was not a number at all.
- **`bool`**: normally cannot fail; checkboxes send clean values.
  Seeing one usually means a text box is feeding a `bool` parameter.
- **`date`, `time`, or `datetime`**: the text was not ISO-formatted;
  the hint suggests forms like `2024-01-31` or `13:30:00`, which
  the [date and time inputs](../../reference/components/input/dateinput.md)
  produce automatically.
- **A dataclass**: the data was missing a required field; the
  message names it.

## Fix

Match the annotation to what the field really provides, or the
field to what the annotation really needs. The three standard
moves:

1. Loosen the annotation to `str` and convert inside the route,
   politely handling bad input yourself.
2. Fix the input side: a `DateInput` for a date parameter, a
   number-kind `TextBox` for numeric ones.
3. Keep the strict annotation and accept that bad input stops with
   this friendly error; for many course apps, that is fine.

## Confirm

Submit the same value again and the route runs (or your polite
in-page message appears, if you chose move 1). Add a test calling
the route with a typed value of the right type.

## Prevent

Decide each parameter's type when you create its input component,
and label inputs so visitors know what belongs in them.

## Understand

[Forms and input](../../concepts/forms-and-input.md) has the full
conversion table.
