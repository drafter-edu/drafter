A **TextArea** lets the user enter a longer block of text.

## Syntax

```python
TextArea(name)
TextArea(name, default_value)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name used to identify the text area when the form is submitted. |
| `default_value` | `str` *(optional)* | The initial text shown in the text area. |

## Returns

Returns a `TextArea` component that collects a multiline text value.

---

## Example 1: Collect a comment

```python drafter
from drafter import *


@route
def index():
	return Page([
		TextArea("comment"),
		Button("Post", post)
	])


@route
def post(comment: str):
	return Page([
		f"Comment: {comment}"
	])


start_server()
```

This example collects a comment and displays it on the next page.

---

## Example 2: Start with existing text

```python drafter
from drafter import *


@route
def index():
	return Page([
		TextArea("notes", "Write your notes here..."),
		Button("Save Notes", save_notes)
	])


@route
def save_notes(notes: str):
	return Page([
		f"Saved notes: {notes}"
	])


start_server()
```

This example starts the text area with pre-filled text.

## Notes

- Use `TextArea` for longer responses like comments or descriptions.
- It behaves like a text input, but with more space for editing.