A **LineBreak** inserts a line break on the page. It is useful when you want to move content onto the next line without starting a new section.

Line breaks are commonly used for:

- Short spacing adjustments.
- Address-style layouts.
- Splitting text across lines.

## Syntax

```python
LineBreak()
```

## Example: Break a line

```python drafter
from drafter import *


@route
def index():
	return Page([
		"First line",
		LineBreak(),
		"Second line",
        LineBreak(),
        "Vs",
        LineBreak(),
        "First line",
        "Same line"
	])


start_server()
```

This places the second line below the first.
