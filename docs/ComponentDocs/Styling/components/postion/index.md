# Postion

Position-related styling helps place components on the page and adjust spacing around them.

## Functions in this section

- `float_left(component)`
- `float_right(component)`
- `change_padding(component, padding)`
- `change_margin(component, margin)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		float_left(Div("Left side")),
		float_right(Div("Right side")),
        Linebreak(),
		change_margin(Div("Outer spacing"), "16px"),
        Linebreak(),
		change_padding(Div("Inner spacing"), "16px")
	])


start_server()
```

Use these functions when you want to move components around the page or give them breathing room.
