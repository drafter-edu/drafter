A **BulletedList** creates an unordered list on a page. Each item appears with a bullet point, making it easy to scan related ideas quickly.

Bulleted lists are commonly used for:

- Feature highlights.
- Checklists and reminders.
- Grouped items where sequence does not matter.

## Syntax

```python
BulletedList(items)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `list[str]` | The items to display in the bulleted list. Non-string values are converted to text. |

---

## Example 1: Feature highlights

```python drafter
from drafter import *


@route
def index():
	return Page([
		Header("Drafter Features", 2),
		BulletedList([
			"Simple routes",
			"Fast prototyping",
			"Built-in components"
		])
	])


start_server()
```

This is useful when the order of items is not important.

## Notes

- Use `BulletedList` for unordered items.
- If sequence matters, use `NumberedList`.
