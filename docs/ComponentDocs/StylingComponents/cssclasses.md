# CSS Classes

CSS classes let you style specific components by giving them a class name and writing CSS for that class.

## Example

```python drafter
from drafter import *

STYLE = """
<style>
	.quit-button {
		color: red;
		float: right;
	}
</style>
"""


@route
def index():
	return Page([
		STYLE,
		Button("Quit", index, classes="quit-button")
	])


start_server()
```

This styles only the button with the `quit-button` class.
