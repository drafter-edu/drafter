A **CheckBox** creates a toggle input for a yes-or-no choice. When selected, it submits `True`; when unselected, it submits `False`.

Checkboxes are commonly used for options such as:

- Accepting terms or policies.
- Enabling or disabling a feature.
- Marking a preference as on or off.

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
	return Page(["Accepted:" + str(accept_terms)])


start_server()
```

This example shows a checkbox used for a yes-or-no choice.

## Notes

- A checkbox is useful for yes/no choices.
- The submitted value is a boolean.