A **Span** groups inline content together. It is useful when you want several pieces of text or components to appear on the same line.

Spans are commonly used for:

- Inline text styling.
- Small labels or captions.
- Combining text and components in one line.

## Syntax

```python
Span(...components)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `components` | `str` or `Component` | The inline items to display together. |

---

## Example: Inline content

```python drafter
from drafter import *


@route
def index():
	return Page([
		Span("Hello, ", "world!")
	])


start_server()
```

This keeps content on the same line.

---

## Example 2: Use Multiple Spans

```python drafter
from drafter import *


@route
def index():
	return Page([
		Span("The ", "first ", "span "),
		Span("puts ", "words ", "together.")
	])


start_server()
```

This shows how multiple spans can be placed next to each other to build a longer inline line of text.
