# Font / Type

These functions change the typeface or emphasis of text.

## Functions in this section

- `bold(component)`
- `italic(component)`
- `underline(component)`
- `strikethrough(component)`
- `monospace(component)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		bold("Bold text"),
        LineBreak(),
		italic("Italic text"),
        LineBreak(),
		underline("Underlined text"),
        LineBreak(),
		strikethrough("Struck text"),
        LineBreak(),
		monospace("Code-like text")
	])


start_server()
```

These functions are useful when you want to emphasize or distinguish text visually.
