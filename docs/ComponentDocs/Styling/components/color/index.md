# Color

Color styling changes text or background colors.

## Functions in this section

- `change_color(component, color)`
- `change_background_color(component, color)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		change_color("Red text", "red"),
		change_background_color(Div("Blue background"), "lightblue")
	])


start_server()
```

Use these functions when you want to highlight content with color.
