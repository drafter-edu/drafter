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
    current_image: PILImage.Image


@route
def index(state: State) -> Page:
    return Page(state, [
        "New Image",
        Row("Image File:", FileUpload("new_image", accept="image/*")),
        Image(state.current_image),
        Button("Update Image", "update_image"),
        Button("Make Image Redder", "make_image_redder")
    ])


@route
def update_image(state: State, new_image: bytes) -> Page:
    state.current_image = PILImage.open(io.BytesIO(new_image))
    return index(state)

@route
def make_image_redder(state: State) -> Page:
    state.current_image = state.current_image.convert("RGB")
    # Make the image redder.
    pixels = state.current_image.load()
    for x in range(state.current_image.width):
        for y in range(state.current_image.height):
            r, g, b = pixels[x, y]
            pixels[x, y] = (r + 50, g, b)
    return index(state)


start_server(State(SIMPLE_IMAGE))