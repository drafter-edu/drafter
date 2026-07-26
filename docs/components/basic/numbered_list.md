A **NumberedList** creates an ordered list on a page. Each item appears with a number (`1.`, `2.`, `3.`, ...), so readers can follow a clear sequence.

Numbered lists are commonly used for:

- Step-by-step instructions.
- Ranked or prioritized items.
- Any content where order is important.

## Syntax

```python
NumberedList(items)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `list[str]` | The items to display in the ordered list. Non-string values are converted to text. |

---

## Example 1: Simple numbered steps

```python drafter
from drafter import *


@route
def index():
	return Page([
		Header("How to Submit Homework", 2),
		NumberedList([
			"Open your class portal",
			"Upload your file",
			"Click Submit"
		])
	])


start_server()
```

This creates a clear step-by-step sequence for users.

## Notes

- Use `NumberedList` when order matters.
- If order does not matter, use `BulletedList`.
