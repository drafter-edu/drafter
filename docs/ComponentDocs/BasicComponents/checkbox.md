# Checkbox

A checkbox lets the user choose `True` or `False` for a named input.

## Syntax

```python
CheckBox(name)
CheckBox(name, default_value)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name used to store the checkbox value. |
| `default_value` | `bool` *(optional)* | The initial checked state. |

## Returns

Returns a `CheckBox` component that collects a boolean value.

---

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		CheckBox("accept_terms", False),
		Button("Submit", submit)
	])


@route
def submit(accept_terms: bool):
	return Page([f"Accepted: {accept_terms}"])


start_server()
```

This example shows a checkbox used for a yes-or-no choice.

## Notes

- A checkbox is useful for yes/no choices.
- The submitted value is a boolean.