from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Link Examples:",
        Header("External Link"),
        Link("Visit Google", "https://www.google.com"),
        LineBreak(),
        Header("Internal Page Link"),
        Link("Go to Page 2", page2),
        LineBreak(),
        Header("Link with Custom Content"),
        Link("Click this image to go to Page 2", page2,
             Image("https://via.placeholder.com/100x50/purple/white?text=Link"))
    ])

@route
def page2(state: str) -> Page:
    return Page(state, [
        "Welcome to Page 2!",
        LineBreak(),
        Link("Back to index", index)
    ])

start_server("")