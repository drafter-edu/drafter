# Shape

Shape-related styling controls size and borders.

## Functions in this section

- `change_width(component, width)`
- `change_height(component, height)`
- `change_border(component, border)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		change_width(change_Color(Div("Wide box"), "red"), "300px"),
		change_height(change_Color(Div("Tall box"), "blue"), "100px"),
		change_border(Div("Bordered box with solid border"), "solid 2px red"),
        change_border(Div("Bordered box with none border"), "none 2px red"),
        change_border(Div("Bordered box with dotted border"), "dotted 2px blue"),
        change_border(Div("Bordered box with dashed border"), "dashed 2px red"),
        change_border(Div("Bordered box with double border"), "double 2px blue"),
        change_border(Div("Bordered box with groove border"), "groove 2px red"),
	])


start_server()
```

Use these functions when you want to control the physical shape of a component.
