A **TextBox** lets the user enter a short line of text.

## Syntax

```python
TextBox(name)
TextBox(name, default_value)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name used to identify the text box when the form is submitted. |
| `default_value` | `str` *(optional)* | The initial value shown in the text box. |

## Returns

Returns a `TextBox` component that collects a single text value.

---

## Example 1: Ask for a name

```python drafter
from drafter import *


@route
def index():
	return Page([
		TextBox("name"),
		Button("Submit", submit)
	])


@route
def submit(name: str):
	return Page([
		f"Hello, {name}!"
	])


start_server()
```

This page collects a name and shows a greeting after submission.

---

## Example 2: Use a default value

```python drafter
from drafter import *


@route
def index():
	return Page([
		TextBox("city", "Seattle"),
		Button("Save", save)
	])


@route
def save(city: str):
	return Page([
		f"City: {city}"
	])


start_server()
```

This example shows a text box with a pre-filled default value.

## Notes

- The `name` should match the parameter name in the linked route.
- Use `TextBox` for short text input like names, titles, and labels.