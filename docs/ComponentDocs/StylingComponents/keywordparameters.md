# Keyword Parameters

Another way to style components is to use `style_` keyword parameters. Drafter converts those keyword parameters into inline CSS styles.

## How It Works

- If a keyword does not start with `style_`, it becomes a normal HTML attribute.
- If a keyword starts with `style_`, it becomes an inline CSS style.
- Underscores are converted to hyphens.

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		Button("Quit", index, style_color="red", style_float="right")
	])


start_server()
```

This makes the button red and floats it to the right.
