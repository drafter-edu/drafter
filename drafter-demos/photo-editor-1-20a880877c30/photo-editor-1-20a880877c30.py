from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    photo: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Photo Editor"),
        "Current photo:\n",
        state.photo,
        "\n",
        Row("New image file:", FileUpload("new_photo", accept="image/*")),
        Button("Upload", "update_photo"),
        "\n",
        Button("Shrink", "shrink_photo"),
        Button("Rotate", "rotate_photo"),
        Button("Grayscale", "grayscale_photo"),
        "\n",
        Download("Download the photo", "photo.png", state.photo)
    ])


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
    index(State(Picture.new(20, 10, "salmon"))))

start_server(State(Picture.new(60, 40, "salmon")))
