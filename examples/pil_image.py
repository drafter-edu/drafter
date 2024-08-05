from drafter import *
from dataclasses import dataclass
from PIL import Image as PILImage
import io
import base64

@dataclass
class State:
    current_image: str = '''R0lGODlhDwAPAKECAAAAzMzM/////wAAACwAAAAADwAPAAACIISPeQHsrZ5ModrLl
N48CXF8m2iQ3YmmKqVlRtW4MLwWACH+H09wdGltaXplZCBieSBVbGVhZCBTbWFydFNhdmVyIQAAOw=='''


@route
def index(state: State) -> Page:
    image = PILImage.open(io.BytesIO(base64.b64decode(state.current_image)))
    return Page(state, [
        "Hello, world!",
        Image(image),
        TextArea("new_image", state.current_image),
        Button("Update Image", "update_image"),
        Download("Download Image", "image.png", image, )
    ])


@route
def update_image(state: State, new_image: str) -> Page:
    state.current_image = new_image
    return index(state)


start_server(State())