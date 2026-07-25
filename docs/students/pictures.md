# Working with Images

Drafter treats images as ordinary values, just like strings and numbers.
The `Picture` type holds an image: you can receive one from a file upload
or the camera, store it in your `State`, change it, show it on a page, and
let the user download it - all without any extra libraries.

## Making a Picture

A `Picture` can be created from a filename, a web URL, or from scratch:

```python
from drafter import *

logo = Picture("logo.png")                          # a file next to your code
dog = Picture("https://placedog.net/300/200")       # an image on the web
canvas = Picture.new(100, 50, "lightblue")          # a brand new image
```

A `Picture` made from a URL is not downloaded until you actually need its
pixels, so it is cheap to create and display. A `Picture` made from a
filename is read immediately. If the file does not exist, you find out on
that exact line.

## Showing a Picture

Put a `Picture` in your page content, or hand it to the `Image` component
if you want to control its size:

```python
from drafter import *

@route
def index(state) -> Page:
    logo = Picture("logo.png")
    return Page(state, [
        "Here is the logo:",
        logo,                          # shows at natural size
        Image(logo, width=64),         # same picture, smaller
    ])

start_server()
```

The `Image` is a component, but the `Picture` is just a simple dataclass. If you are going to have an image in your state, you should use `Picture` for the type of the attribute, not `Image`. The `Image` component is only for displaying a picture on a page, and has more useful properties.

## Uploading a Picture

Add a `FileUpload` component to a form, and annotate the matching route
parameter as `Picture`:

```python
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    photo: Picture | None

@route
def index(state: State) -> Page:
    content = ["Choose an image:", FileUpload("new_photo", "image/*"),
               Button("Upload", show_photo)]
    if state.photo is not None:
        content.append(state.photo)
    return Page(state, content)

@route
def show_photo(state: State, new_photo: Picture) -> Page:
    state.photo = new_photo
    return Page(state, ["You uploaded:", state.photo,
                        Link("Back", index)])

start_server(State(None))
```

If the user presses the button without choosing a file, Drafter shows a
friendly error explaining that no file was chosen. If it is okay for the
file to be missing, annotate the parameter as `Picture | None` instead, and
you will receive `None` in that case.

## Taking a Photo with the Camera

The `Camera` component lets the user take a photo with their device's camera.
You can use the `Photo` type to inspect the result:

```python
from drafter import *

@route
def index(state) -> Page:
    return Page(state, [
        Camera("selfie"),
        Button("Use this photo", show_selfie),
    ])

@route
def show_selfie(state, photo: Photo) -> Page:
    if photo.status == "granted":
        return Page(state, ["Looking good!", photo.picture.scale(0.5)])
    else:
        return Page(state, ["Camera permission was denied."])


start_server()
```

The `Camera` component can also work the same way as the `FileUpload` component: annotate the parameter as
`Picture` to get the captured image directly:

```python
from drafter import *

@route
def index(state) -> Page:
    return Page(state, [
        Camera("selfie"),
        Button("Use this photo", show_selfie),
    ])

@route
def show_selfie(state, selfie: Picture) -> Page:
    return Page(state, ["Looking good!", selfie.scale(0.5)])

start_server()
```

If the user denies camera permission, a bare `Picture` parameter produces a
friendly error. Annotate the parameter as `Photo` instead when you want to
inspect what happened (`photo.status` is `"granted"`, `"denied"`, etc., and
`photo.picture` is the `Picture` once one was captured), or as
`Picture | None` to simply receive `None`.

## Changing a Picture

Every manipulation returns a **new** `Picture`, leaving the original alone:

```python
# TODO: Make all of these into fully working examples
smaller = pic.resize(320, 240)     # exact size in pixels
half = pic.scale(0.5)              # relative size
sideways = pic.rotate(90)          # degrees counter-clockwise
closeup = pic.crop(10, 10, 90, 90) # left, top, right, bottom
mirrored = pic.flip_horizontal()   # or flip_vertical()
moody = pic.grayscale()
```

You can also work with individual pixels, which is great for building
filters yourself:

```python
color = pic.get_pixel(0, 0)        # (red, green, blue) tuple
pic.set_pixel(0, 0, "red")         # a color name, "#ff0000", or a tuple
```

Note that `set_pixel` is the one method that changes the picture in place.

Pictures also know their own size and metadata:

```python
pic.width, pic.height              # size in pixels
pic.filename                       # original filename, if there was one
pic.mime_type                      # e.g. "image/png"
```

## Downloading and Saving

Give a `Picture` to the `Download` component to let the user save it:

```python
# TODO: This should be expanded into a fully working example with a form and a picture in state.
Download("Save your pic", "pic.png", state.pic)
```

## Pictures in State and Tests

Pictures can be stored in your `State` like any other value, and two
Pictures are equal (`==`) when their pixels are the same - the filename
does not matter. That means `assert_equal` works naturally on pages and
states that contain images:

```python
assert_equal(
    show_photo(State(None), Picture.new(2, 2, "red")),
    Page(State(Picture.new(2, 2, "red")),
         ["You uploaded:", Picture.new(2, 2, "red"), Link("Back", index)]),
)
```

## Advanced: the Full PIL Toolbox

`Picture` is built on the [Pillow](https://pillow.readthedocs.io/) library.
If you need something beyond the built-in methods, convert to a PIL image,
do your work, and wrap it back up:

```python
from PIL import ImageFilter

pil_image = photo.to_pil()
blurred = Picture(pil_image.filter(ImageFilter.BLUR))
```
