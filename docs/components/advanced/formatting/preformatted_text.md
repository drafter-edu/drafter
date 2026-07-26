A **PreformattedText** component displays text exactly as written. It is useful when spacing and line breaks should stay unchanged.

Preformatted text is commonly used for:

- Code snippets.
- Logs or output.
- Text that should keep its spacing.

## Syntax

```python
PreformattedText(text)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text to display exactly as written. |

---

## Example: Show formatted text

```python drafter
from drafter import *


@route
def index():
	return Page([
		PreformattedText("Line 1\n    Line 2\nLine 3")
	])


start_server()
```

This keeps the spacing and line breaks in the text.
