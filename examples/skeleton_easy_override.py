"""
Example demonstrating that the Skeleton theme is now less specific and easier to override.
"""
from drafter import *

# Simple CSS to override button colors - no need for complex selectors!
CUSTOM_STYLE = """
<style>
    .red-button {
        color: red;
        background-color: pink;
    }
    
    .green-button {
        color: white;
        background-color: green;
    }
    
    .large-text {
        font-size: 24px;
    }
</style>
"""


@route
def index(state: str) -> Page:
    return Page([
        CUSTOM_STYLE,
        Header("Skeleton Theme - Easy Override Demo"),
        Text("The Skeleton theme is now easier to customize!", classes="large-text"),
        LineBreak(),
        Text("Notice how the custom button styles work without needing complex selectors:"),
        LineBreak(),
        Button("Default Button", index),
        Button("Red Button", index, classes="red-button"),
        Button("Green Button", index, classes="green-button"),
        LineBreak(),
        LineBreak(),
        Text("Components in lists now align properly:"),
        BulletedList([
            Span("Item 1 with ", Button("Button", index), " inline"),
            Span("Item 2 with ", Button("Another", index), " button"),
            "Simple text item",
        ]),
    ])


start_server("")
