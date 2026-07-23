A **Download** lets the user download a file from your app. It is useful when you want to give the user a text file, image, or other data file to save locally.

Downloads are commonly used for:

- Sample files.
- Generated text or reports.
- Helpful files the user can test or inspect.

## Syntax

```python
Download(text, filename, contents)
Download(text, filename, contents, content_type)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text shown on the download link. |
| `filename` | `str` | The name of the downloaded file. |
| `contents` | `str` | The contents of the file to download. |
| `content_type` | `str` *(optional)* | The MIME type of the file. |

---

## Example: Download a text file

```python drafter
from drafter import *


@route
def index():
	return Page([
		Download("Download the sample text file", "im_a_txt_file.txt", "im a txt file")
	])


start_server()
```

This creates a download link that gives the user a small text file.

## Notes

- Use `Download` when the user should save a file instead of viewing it on the page.
- The file contents must be provided as a string.
