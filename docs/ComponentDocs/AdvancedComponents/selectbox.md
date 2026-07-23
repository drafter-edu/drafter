A **SelectBox** lets the user choose one option from a list. It is useful when you want a small set of choices in a compact control.

Select boxes are commonly used for:

- Choosing a category.
- Picking one option from a menu.
- Limiting input to known values.

## Syntax

```python
SelectBox(name, options)
SelectBox(name, options, default_value)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name used to identify the select box when the form is submitted. |
| `options` | `list[str]` | The available choices. |
| `default_value` | `str` *(optional)* | The initial selected option. |

---

## Example: Choose a pet

```python drafter
from drafter import *


@route
def index():
	return Page([
		SelectBox("pet", ["Dog", "Cat", "Fih"], "Cat"),
		Button("Submit", show_pet)
	])


@route
def show_pet(pet: str):
	return Page([
		"You chose: " + pet
	])


start_server()
```

This example shows a select box with a default choice.

## Notes

- The submitted value will match the selected option.
- Use `SelectBox` when you want a single choice from a short list.
