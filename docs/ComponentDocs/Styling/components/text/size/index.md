# Size

These functions change the size of text.

## Functions in this section

- `small_font(component)`
- `large_font(component)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		small_font("Small text"),
		large_font("Large text")
	])


start_server()
```

Use these when you want text to look less important or more important without changing its meaning.
