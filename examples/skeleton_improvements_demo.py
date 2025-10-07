"""
Before/After example showing how the Skeleton theme improvements make styling easier.
This demonstrates that students no longer need complex selectors to override theme styles.
"""
from drafter import *

# ========== BEFORE (What students had to do) ==========
# With the old Skeleton theme, you needed complex selectors like this:
BEFORE_STYLE = """
<style>
    /* Had to be specific with selectors to override theme */
    button.my-custom-button {
        color: red !important;
        background-color: yellow !important;
    }
    
    a.my-link {
        color: purple !important;
    }
</style>
"""

# ========== AFTER (What students can now do) ==========
# With the improved Skeleton theme, simple class selectors work:
AFTER_STYLE = """
<style>
    /* Simple class selectors now work! */
    .my-custom-button {
        color: red;
        background-color: yellow;
    }
    
    .my-link {
        color: purple;
    }
    
    .highlight {
        background-color: lightgreen;
        padding: 5px;
    }
</style>
"""


@route
def index(state: str) -> Page:
    return Page([
        AFTER_STYLE,
        Header("Skeleton Theme Improvements Demo", level=1),
        
        LineBreak(),
        bold("✅ Simple class selectors now work without needing element.class syntax!"),
        LineBreak(),
        LineBreak(),
        
        Header("Custom Button Styling:", level=2),
        Button("Default Button", index),
        " ",
        Button("Custom Button", index, classes="my-custom-button"),
        LineBreak(),
        LineBreak(),
        
        Header("Custom Link Styling:", level=2),
        Link("https://example.com", "Default Link"),
        " | ",
        Link("https://example.com", "Custom Link", classes="my-link"),
        LineBreak(),
        LineBreak(),
        
        Header("Better Layout in Lists:", level=2),
        Text("Buttons and text now align properly in lists:"),
        BulletedList([
            Span("Buy ", Button("Item 1", index), " for 10 coins"),
            Span("Buy ", Button("Item 2", index), " for 20 coins"),
            Span("Buy ", Button("Item 3", index), " for 30 coins"),
        ]),
        LineBreak(),
        
        Header("Inline Elements:", level=2),
        Text("Images and buttons align nicely: "),
        Button("Click", index),
        Text(" next to text ", classes="highlight"),
        Button("Another", index),
        LineBreak(),
        LineBreak(),
        
        italic("The theme is now less pushy and easier to customize!"),
    ])


start_server("")
