# CSS Style Tags

You can embed CSS directly into a page by including a `<style>` tag in the page content.

## Example

```python drafter
from drafter import *


@route
def index():
	return Page([
		"""
		<style>
			button {
				color: red;
				float: right;
			}
		</style>
		""",
		Button("Quit", index)
	])


start_server()
```

This changes the style of all buttons on the page.
