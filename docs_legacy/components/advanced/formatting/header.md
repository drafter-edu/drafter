A **Header** creates a title or heading on the page. Headers are useful for organizing content into sections.

Headers are commonly used for:

- Page titles.
- Section headings.
- Short labels that need emphasis.

## Syntax

```python
Header(body)
Header(body, level)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `body` | `str` | The text to display in the header. |
| `level` | `int` *(optional)* | The header size from 1 to 6. |

---

## Example: Add a title

```python drafter
from drafter import *


@route
def index():
	return Page([
		Header("Welcome to Drafter 1", 1),
        Header("Welcome to Drafter 2", 2),
        Header("Welcome to Drafter 3", 3),
        Header("Welcome to Drafter 4", 4),
        Header("Welcome to Drafter 5", 5),
        Header("Welcome to Drafter 6", 6),
	])


start_server()
```

This adds a multiple heading at each level from 1-6
