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
- **You reloaded the tab, or opened a saved link, on a page that came
  from a form**: the address bar keeps the name of the last route,
  for example `?route=save`. Reloading the tab starts the app again,
  returns the state to its starting value, and runs that route with
  no form values, so its parameters receive nothing. Choose "Return
  to Index Page" on the error page to continue from the first page.

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

The opposite mismatch produces a warning, not an error page. When a
page sends a form field and the route has no parameter with that
name, the route still runs and its page appears as usual. The
Current tab of the debug panel shows a count badge, and under
"Errors & Warnings" it lists a line like this one:

```text
The form field 'new_name' was sent to 'index', but the function has no
matching parameter.
```

Every button and link on a page sends all of that page's form fields
to its target route. Whether the warning matters depends on which
route received the field:

- **Harmless**: a Cancel button on a form page. `Button("Cancel",
  "index")` sends the text box's value to `index`, which does not
  need it. You can leave this warning alone.
- **A real bug**: a misspelled name. If the page has
  `TextBox("petname")` and the route's parameter is `pet_name`, the
  field has no parameter and the parameter has no value. The warning
  then arrives together with the error page described at the top of
  this entry, and the debug panel lists both.
- **A real bug with no error page**: a misspelled name on a
  parameter that has a default value. The route runs with the
  default, and the warning is the only sign that the typed value was
  dropped.

The fix for both bugs is the one in the Fix section: make the
component's name and the parameter's name agree.

## Understand

[Forms and input](../../concepts/forms-and-input.md) explains the
name-to-parameter contract this error enforces.
