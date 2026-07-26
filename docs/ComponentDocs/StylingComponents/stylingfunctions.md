# Styling Functions

Styling functions take a component and return the same component with extra styling applied.

## Available Functions

- `float_left(component)`
- `float_right(component)`
- `bold(component)`
- `italic(component)`
- `underline(component)`
- `strikethrough(component)`
- `monospace(component)`
- `small_font(component)`
- `large_font(component)`
- `change_color(component, color)`
- `change_background_color(component, color)`
- `change_text_size(component, size)`
- `change_text_font(component, font)`
- `change_text_align(component, alignment)`
- `change_text_decoration(component, decoration)`
- `change_text_transform(component, transform)`
- `change_margin(component, margin)`
- `change_border(component, border)`
- `change_padding(component, padding)`
- `change_width(component, width)`
- `change_height(component, height)`

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		bold("Bold text"),
		italic("Italic text"),
		change_color("Red text", "red"),
		float_right(Button("Quit", index))
	])


start_server()
```

This shows a few styling functions working together on one page.
