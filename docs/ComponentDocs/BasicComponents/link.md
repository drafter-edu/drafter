A **Link** creates a clickable hyperlink on a page. When the user clicks the link, Drafter can either:

- Navigate to another route in your application.
- Open an external URL outside your application.

Links are commonly used for lightweight navigation, references, and external resources.

## Syntax

```python
Link(text, url)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text displayed for the link. |
| `url` | `str` or `function` | The destination URL or route function. |

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
		Link("Visit Drafter", "https://drafter-edu.github.io/drafter/contents.html")
	])


start_server()
```

This link opens the Drafter documentation site.

## Notes

- Use `Link` when you want regular hyperlink behavior.
- If you want a button-style action instead, use `Button`.