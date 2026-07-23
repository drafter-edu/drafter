# Adding Website CSS

The `add_website_css` function lets you add CSS to the whole website instead of repeating it on every page.

## Example

```python drafter
from drafter import *

add_website_css("body", "background-color: lightblue;")
add_website_css("button.quit-button", "color: red; float: right;")


@route
def index():
	return Page([
		Button("Quit", index, classes="quit-button")
	])


start_server()
```

This adds website-wide CSS for the body and a button class.
