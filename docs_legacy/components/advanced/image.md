A **Image** displays an image on the page. This is useful for screenshots, illustrations, and other visual content.

Images are commonly used for:

- Logos and icons.
- Photos and illustrations.
- Helpful visual examples.

## Syntax

```python
Image(url)
Image(url, width, height)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | The URL or local file path for the image. |
| `width` | `int` *(optional)* | The width of the image in pixels. |
| `height` | `int` *(optional)* | The height of the image in pixels. |

---

## Example: Show an image

```python drafter
from drafter import *


@route
def index():
	return Page([
		"A simple image:"
		,Image("https://images.unsplash.com/photo-1592194996308-7b43878e84a6?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", 697, 1030)
	])


start_server()
```

This shows an image on the page.

## Notes

- Use a full URL or a local file path.
- Width and height are optional.
