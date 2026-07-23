# Transformations

These functions change how text is displayed or aligned.

## Functions in this section

- `change_text_size(component, size)`
- `change_text_font(component, font)`
- `change_text_align(component, alignment)`
- `change_text_decoration(component, decoration)`
- `change_text_transform(component, transform)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		change_text_size("Bigger text", 24),
		change_text_font("Different font", "Courier New"),
		change_text_align("Centered text", "center"),
		change_text_decoration("Underlined text", "underline"),
		# change_text_transform("Uppercase text", "uppercase")
	])


start_server()
```

These functions are useful when you want direct control over the way text is shown.
