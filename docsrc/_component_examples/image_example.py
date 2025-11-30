from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Image Examples:",
        Header("Basic Image"),
        Image("https://via.placeholder.com/150x100/blue/white?text=Drafter"),
        Header("Image with Custom Size"),
        Image("https://via.placeholder.com/200x150/green/white?text=Custom+Size", width=200, height=150),
        Header("Image as Link"),
        Link("Click this image", other_page, 
             Image("https://via.placeholder.com/100x100/red/white?text=Link"))
    ])

@route
def other_page(state: str) -> Page:
    return Page(state, [
        "You clicked the image!",
        Link("Go back", index)
    ])

start_server("")