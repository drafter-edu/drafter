A **Div** groups components together in a vertical stack. A **Row** groups components together in a horizontal line. These are useful when you want to organize content into simple layouts.

Div and row components are commonly used for:

- Grouping related items.
- Building vertical and horizontal layouts.
- Keeping content organized.

## Syntax

```python
Div(...components)
Row(...components)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `components` | `str` or `Component` | The items to group together. |

## Example 1: USing Div and Row

```python drafter
from drafter import *


@route
def index():
	return Page([
		Div(
			"Header area",
			Row(
				Div("Left card", "Left details "),
				Div("Right card", "Right details")
			),
			"Footer area"
		)
	])


start_server()
```

This example combines both components: `Div` controls the vertical sections, while `Row` places the middle cards horizontally.
