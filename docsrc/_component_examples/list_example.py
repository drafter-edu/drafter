from drafter import *

@route
def index(state: str) -> Page:
    fruits = ["Apple", "Banana", "Cherry", "Date"]
    colors = ["Red", "Green", "Blue"]
    
    return Page(state, [
        "List Examples:",
        Header("Bulleted List"),
        BulletedList(fruits),
        
        Header("Numbered List"),
        NumberedList(colors),
        
        Header("Mixed Content List"),
        BulletedList([
            "Plain text item",
            Link("Link item", index),
            "Another text item"
        ])
    ])

start_server("")