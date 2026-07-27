"""Demonstrates the Picture value type: upload, manipulate, display, download.

Students annotate a route parameter as `Picture` to receive an uploaded
image (or `Picture | None` to allow no file), store it in state like any
other value, transform it with the curated methods, and hand it back to
`Image` and `Download`.
"""

from dataclasses import dataclass

from drafter import *


@dataclass
class State:
    photo: Picture


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "Current photo:",
            state.photo,
            Row("New image file:", FileUpload("new_photo", accept="image/*")),
            Button("Upload", update_photo),
            Button("Shrink", shrink_photo),
            Button("Rotate", rotate_photo),
            Button("Grayscale", grayscale_photo),
            Download("Download Photo", "photo.png", state.photo),
        ],
    )


@route
def update_photo(state: State, new_photo: Picture | None) -> Page:
    if new_photo is not None:
        state.photo = new_photo
    return index(state)


@route
def shrink_photo(state: State) -> Page:
    state.photo = state.photo.scale(0.5)
    return index(state)


@route
def rotate_photo(state: State) -> Page:
    state.photo = state.photo.rotate(90)
    return index(state)


@route
def grayscale_photo(state: State) -> Page:
    state.photo = state.photo.grayscale()
    return index(state)


assert_equal(
    shrink_photo(State(Picture.new(40, 20, "salmon"))),
    index(State(Picture.new(20, 10, "salmon"))),
)

start_server(State(Picture.new(60, 40, "salmon")))
