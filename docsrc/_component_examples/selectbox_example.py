from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "SelectBox Examples:",
        Header("Choose a Color"),
        SelectBox("color", ["Red", "Green", "Blue"]),
        Header("Choose a Size (with default)"),
        SelectBox("size", ["Small", "Medium", "Large"], "Medium"),
        Button("Submit", show_choices)
    ])

@route 
def show_choices(state: str, color: str, size: str) -> Page:
    return Page(state, [
        f"You chose: {color} {size}",
        Link("Choose again", index)
    ])

start_server("")