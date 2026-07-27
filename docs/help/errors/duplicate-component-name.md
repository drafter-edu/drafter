---
page_type: error
title: Two components share a name
level: L2
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Fix two components sharing a name.
error_text: "has multiple components with the same name"
---

# Two components share a name

## The error

```text
The page returned from save has multiple components with the same
name:
  'answer' is used by: TextBox, SelectBox
Each component must have a unique name, because the name is how
values are matched to route parameters. Rename the duplicates.
```

The friendly title is "Components Share a Name".

## What it means

Two or more inputs on one page use the same `name`. Names are how
submitted values find route parameters; two components fighting
over one name means one value would silently win, so Drafter stops
the page instead of guessing.

## Where to look

The route named in the message. Search its content list for the
quoted name; the message lists which component types are using it.

## Check

- **A copy-paste**: a duplicated `TextBox("answer")` from cloning a
  line and forgetting to rename.
- **Two questions, one name**: two genuinely different inputs
  (`TextBox("answer")` and `SelectBox("answer", ...)`) that each
  deserve their own parameter.
- **A checkbox group on purpose**: several checkboxes meant to
  submit together should be
  [RelatedCheckBox](../../reference/components/input/relatedcheckbox.md),
  which is designed to share one name (and delivers a list).

## Fix

Rename so each input has its own name, with a matching parameter on
the receiving route:

```python
TextBox("guess"),
SelectBox("category", ["animals", "history"]),
Button("Submit", "save")
```

```python
@route
def save(state: State, guess: str, category: str) -> Page:
    ...
```

## Confirm

The page renders again, and submitting fills both parameters. An
`assert_has(index(state), TextBox("guess"))` keeps the rename from
quietly regressing.

## Prevent

Name inputs after the specific question they ask (`pet_name`,
`pet_age`), not after generic slots (`input1`, `answer`), and the
collisions mostly stop happening.

## Understand

[Forms and input](../../concepts/forms-and-input.md): the
name-to-parameter contract that uniqueness protects.
