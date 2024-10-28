from bakery import assert_equal
from drafter import *
from dataclasses import dataclass
from PIL import Image as PILImage


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


inital_state = State("", "", PILImage.new("RGB", (1, 1)))
assert_equal(update_data(inital_state, "Hello, world!", b"01010101", PILImage.new("RGB", (100, 100))),
             Page(State("Hello, world!", "b'01010101'", PILImage.new("RGB", (100, 100))), [
                 "You can upload three things here:",
                 HorizontalRule(),
                 Div(
                     Row("Text File:", FileUpload("new_text")),
                     "Here's the text you uploaded:",
                     Div("Hello, world!"),
                     style_margin="4px", style_border="1px solid black"),
                 HorizontalRule(),
                 Div(
                     Row("Bits File:", FileUpload("new_bits")),
                     "Here are the bits you uploaded:",
                     PreformattedText("b'01010101'"),
                     style_margin="4px", style_border="1px solid black"),
                 HorizontalRule(),
                 Div(
                     Row("Image File:", FileUpload("new_image", accept="image/*")),
                     "Here's the image you uploaded:",
                     Image(PILImage.new("RGB", (100, 100))),
                     style_margin="4px", style_border="1px solid black"),
                 HorizontalRule(),
                 Button("Update to uploaded files", "update_data"),
                 Button("Go to download page", "download_page")
             ]))

# assert_equal(update_data(inital_state,