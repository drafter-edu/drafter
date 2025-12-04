.. _pillow:

Pillow Support
==============

Pillow is a popular Python Imaging Library (PIL) fork that adds image processing capabilities to your
Python applications. Drafter has partial support for Pillow when deployed via GitHub Actions.

Here is an example Drafter application that uses Pillow to manipulate images.

.. code-block:: python

    from drafter import *
    from PIL import Image as PIL_Image
    from random import randint


    @dataclass
    class State:
        image: PIL_Image


    @route
    def index(state: State):
        return Page(state, [
            Image(state.image),
            FileUpload("next_image", accept="image/*"),
            Download("Download Image", "my_image.png", state.image),
            Button("Upload New Image", "upload"),
            Button("Recolor randomly", recolor)
        ])


    @route
    def upload(state: State, next_image: bytes):
        state.image = PIL_Image.open(io.BytesIO(next_image)).convert('RGB')
        return index(state)


    MAX_RGB = 255


    @route
    def recolor(state: State):
        width, height = state.image.size
        state.image.putpixel((randint(0, width), randint(0, height)),
                             (randint(0, MAX_RGB), randint(0, MAX_RGB), randint(0, MAX_RGB)))
        return index(state)


    initial_image = PIL_Image.new("RGB", (10, 10))

    initial_image.putpixel((5, 5), (255, 0, 0))
    initial_image.putpixel((5, 6), (255, 0, 0))
    initial_image.putpixel((6, 6), (255, 0, 0))
    initial_image.putpixel((6, 6), (255, 0, 0))

    start_server(State(initial_image))