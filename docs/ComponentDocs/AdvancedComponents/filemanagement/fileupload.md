A **FileUpload** lets the user choose a file and send it to the server. It is useful when your app needs to work with user-provided files.

File uploads are commonly used for:

- Text files.
- Images.
- Data files or documents.

## Syntax

```python
FileUpload(name)
FileUpload(name, accept)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name used to identify the uploaded file when the form is submitted. |
| `accept` | `str` or `list[str]` *(optional)* | The file types the user can upload. |

---

Use the following text file to test the upload example:

<a href="assets/im_a_txt_file.txt" download>
Download im_a_txt_file.txt
</a>

## Example: Use a text file to test uploading

```python drafter
from drafter import *


@route
def index():
	return Page([
		"Use the previous text file to test uploading:",
		FileUpload("my_file", ".txt"),
		Button("Upload", upload_file)
	])


@route
def upload_file(my_file: str):
	return Page([
		"The uploaded text file says:",
		PreformattedText(my_file)
	])


start_server()
```

This example allows the user to upload a txt file and displays the text inside it.

## Notes

- Use `accept` to limit the file types the user can select.
- File uploads are helpful when the app needs external content from the user.
