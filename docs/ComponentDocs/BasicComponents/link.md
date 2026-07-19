A **Link** creates a clickable hyperlink on a page. It is useful for sending the user to another page or to an external URL.

## Syntax

```python
Link(text, url)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text displayed for the link. |
| `url` | `str` or `function` | The destination URL or route function. |

## Returns

Returns a `Link` component that appears as a normal underlined hyperlink.

---

## Example 1: Go to another page

```python drafter
from drafter import *


@route
def index():
	return Page([
		Link("Go to About", about)
	])


@route
def about():
	return Page([
		"Welcome to the about page."
	])


start_server()
```

This link navigates to the `about` route when clicked.

---

## Example 2: Open an external website

```python drafter
from drafter import *


@route
def index():
	return Page([
		Link("Visit Drafter", "https://drafter-edu.github.io/drafter/")
	])


start_server()
```

This link opens the Drafter documentation site.

## Notes

- Use `Link` when you want regular hyperlink behavior.
- If you want a button-style action instead, use `Button`.