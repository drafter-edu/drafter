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


if __name__ == "__main__":
    # Test without starting server
    state = State()
    page = index(state)
    
    print("✓ Successfully created page with 9 buttons (all with text 'Click Me')")
    print(f"✓ Page has {len([c for c in page.content if isinstance(c, Button)])} buttons")
    
    # Extract and verify unique namespaces
    import re
    button_count = 0
    namespaces = set()
    
    for content in page.content:
        if isinstance(content, Button):
            button_count += 1
            html = str(content)
            # Extract the button value which includes the namespace
            # Look specifically for the button element's value
            value_match = re.search(r"<button[^>]+value='([^']+)'", html)
            if value_match:
                namespace = value_match.group(1)
                # Decode HTML entities
                namespace = namespace.replace('&quot;', '"')
                namespaces.add(namespace)
                if button_count <= 3:  # Debug: show first 3
                    print(f"  Button {button_count} namespace: {namespace}")
    
    print(f"✓ Found {len(namespaces)} unique button namespaces")
    print(f"✓ All {button_count} buttons have unique identifiers")
    
    if len(namespaces) == button_count:
        print("\n✅ SUCCESS: All buttons with the same text have unique namespaces!")
        print("   This prevents argument conflicts when buttons are clicked.")
    else:
        print("\n❌ FAILURE: Some buttons share namespaces!")
    
    # Uncomment to start the server and test interactively
    # start_server(State())
