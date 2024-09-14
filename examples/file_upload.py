from drafter import *
from dataclasses import dataclass
from PIL import Image as PILImage
import io
import base64

RAW_SIMPLE_IMAGE = '''R0lGODlhDwAPAKECAAAAzMzM/////wAAACwAAAAADwAPAAACIISPeQHsrZ5ModrLl
N48CXF8m2iQ3YmmKqVlRtW4MLwWACH+H09wdGltaXplZCBieSBVbGVhZCBTbWFydFNhdmVyIQAAOw=='''
SIMPLE_IMAGE = PILImage.open(io.BytesIO(base64.b64decode(RAW_SIMPLE_IMAGE)))

@dataclass
class State:
    current_text: str
    current_bits: str
    current_image: PILImage.Image


@route
def index(state: State) -> Page:
    return Page(state, [
        "You can upload three things here:",
        HorizontalRule(),
        Div(
            Row("Text File:", FileUpload("new_text")),
            "Here's the text you uploaded:",
            Div(state.current_text),
            style_margin="4px", style_border="1px solid black"),
        HorizontalRule(),
        Div(
            Row("Bits File:", FileUpload("new_bits")),
            "Here are the bits you uploaded:",
            PreformattedText(state.current_bits),
            style_margin="4px", style_border="1px solid black"),
        HorizontalRule(),
        Div(
            Row("Image File:", FileUpload("new_image", accept="image/*")),
            "Here's the image you uploaded:",
            Image(state.current_image),
            style_margin="4px", style_border="1px solid black"),
        HorizontalRule(),
        Button("Update to uploaded files", "update_data"),
        Button("Go to download page", "download_page")
    ])


@route
def update_data(state: State, new_text: str, new_bits: bytes, new_image: PILImage.Image) -> Page:
    state.current_text = new_text
    state.current_bits = str(new_bits)
    state.current_image = new_image
    return index(state)

@route
def download_page(state: State) -> Page:
    return Page(state, [
        "Download the image?",
        Download("Download Image", "my_image.png", state.current_image, "image/png"),
        HorizontalRule(),
        "Return to", Button("the upload page", "index")
    ])


start_server(State("NO TEXT YET", b"NO BITS YET".decode('utf-8'), SIMPLE_IMAGE))