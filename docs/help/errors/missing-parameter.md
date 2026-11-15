---
page_type: error
title: Route is missing a parameter a form expected
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix a route missing a parameter a form expected.
error_text: "expects a value for parameter"
---

# Route is missing a parameter a form expected

## The error

The error page has this title:

```text
Problem With the Route's Arguments
```

The sentence under the title names the route function:

```text
Drafter could not match the information sent by the page to the
parameters of your 'save' function.
```

The technical message below it says which parameter received no
value:

```text
request.argument_parsing_failed: Error while parsing arguments for request
to URL save: The route function 'save' expects a value for parameter
'pet_name', but none was provided. Add a form field, component argument,
or event value named 'pet_name', or give the parameter a default value.
```

When the page sent a value under a similar name, the last sentence is
a suggestion in its place:

```text
Did you mean the request value 'petname'? Check that the form field or
component argument is named 'pet_name'.
```

Drafter uses the same title when a value arrives but cannot be
converted to the parameter's type. Those messages contain "expects
int but got" or a similar phrase, and they are covered in
[Could not convert text to an int](type-conversion-int.md) and
[Could not convert a value to the parameter's type](type-conversion-other.md).

## What it means

The route declares a parameter, and after state injection, form
fields, and button arguments were matched up by name, nothing filled
it. The route cannot run with a missing argument, so the request
stopped.

## Where to look

Compare two places side by side: the route's `def` line, and the
page that submitted to it (the form's components and the button's
arguments). The mismatch is somewhere between those two.

## Check

- **Names differ**: the page has `TextBox("petname")` but the route
  says `pet_name`. The "Did you mean" suggestion catches most of
  these.
- **The component is missing**: the route expects a value, but no
  input with that name is on the submitting page at all.
- **The wrong button**: another page's button also targets this
  route, without the form fields the route needs. Every button that
  targets a route must be accompanied by whatever inputs the route's
  parameters require.
- **It is actually `state`**: if the unfilled parameter is your state,
  make it the first parameter and name it `state`.

## Fix

Make the names agree; you can change either side:

```python
# The page:
TextBox("pet_name")
Button("Save", "save")

# The route:
@route
def save(state: State, pet_name: str) -> Page:
    ...
```

Or, when the value is legitimately optional, give the parameter a
default: `def save(state: State, pet_name: str = "")`.

## Confirm

Submit the form again; the route should run. Then call the route in a
test with the values spelled out,
`assert_state(save(State(...), "Ada"), State(...))`, so a future
rename fails loudly before anyone clicks.

## Prevent

Pick one name per piece of information and use it for both the
component and the parameter. If you write the form and its route in
the same sitting and check each name against its parameter, the
mismatch is unlikely to appear in the first place.

## A related warning: a form field with no matching parameter

The opposite mismatch is not an error. When a page sends a value and
the route has no parameter with that name, the route still runs and
its page appears as usual.

Most leftover values are normal and produce no message. Every button
and link on a page sends all of that page's form fields to its target
route, and many routes need none of them. A Cancel button on a form
page is the usual example: `Button("Cancel", "index")` sends the text
box's value to `index`, which has no use for it.

Drafter lists a warning when a leftover value looks like a mistake.
The Current tab of the debug panel shows a count badge, and under
"Errors & Warnings" it lists a line like this one:

```text
The form field 'petname' was sent to 'adopt', but the function has no
matching parameter.
```

Expanding the warning's Details shows a suggestion:

```text
Did you mean the parameter 'pet_name'?
```

The warning appears in two cases:

- **A near miss**: the name of a form field is close to the name of a
  parameter that received no value. Suppose the page has
  `TextBox("petname")` and the route is
  `def adopt(state: State, pet_name: str = "")`. The route runs with
  the default, and the warning is the only sign that the typed value
  was dropped. When the parameter has no default, the warning arrives
  together with the error page described at the top of this entry,
  and the debug panel lists both.
- **An unused `Argument`**: a value attached to a button with
  [Argument](../../reference/components/actions/argument.md) was
  written for one route, so Drafter reports it whenever that route
  has no parameter with its name. The line begins "The component
  argument". When no parameter has a similar name, the Details say
  to add a parameter with that name or to remove the argument.

The fix in both cases is the one in the Fix section: make the name on
the page and the name of the parameter agree.

## Understand

[Forms and input](../../concepts/forms-and-input.md) explains the
name-to-parameter contract this error enforces.
