"""
Example demonstrating the button namespacing fix.
This creates a grid of buttons with the same text but different arguments.
Before the fix, these buttons would have conflicting parameter names.
After the fix, each button has unique parameter names based on its instance ID.
"""
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    last_clicked: str = "None"
    click_count: int = 0


@route
def index(state: State) -> Page:
    """Create a 3x3 grid of buttons, all with the same text 'Click Me'"""
    content = [
        "Button Namespacing Example",
        "Click any cell to see its coordinates:",
        f"Last clicked: {state.last_clicked}",
        f"Total clicks: {state.click_count}",
        HorizontalRule(),
    ]
    
    # Create a 3x3 grid of buttons
    for y in range(3):
        for x in range(3):
            content.append(Button("Click Me", cell_clicked, [
                Argument("x", x),
                Argument("y", y)
            ]))
        content.append(LineBreak())
    
    return Page(state, content)


@route
def cell_clicked(state: State, x: int, y: int) -> Page:
    """Handle button click from grid"""
    state.last_clicked = f"Cell ({x}, {y})"
    state.click_count += 1
    return index(state)


start_server(State())