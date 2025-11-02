"""
Simplified integration test that demonstrates the test infrastructure works
without requiring external dependencies.
"""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_component_creation():
    """
    Test that demonstrates component creation works correctly.
    This is a unit test that doesn't require a server.
    """
    from drafter import Page, TextBox, Button, Header
    from dataclasses import dataclass
    
    print("Testing component creation...")
    
    @dataclass
    class SimpleState:
        value: str
    
    # Create a handler function
    def handle_submit(state: SimpleState, input_value: str) -> Page:
        state.value = input_value
        return Page(state, [f"You entered: {state.value}"])
    
    # Create a page with components
    state = SimpleState(value="")
    page = Page(state, [
        Header("Test Page"),
        "Enter something:",
        TextBox("input_value"),
        Button("Submit", handle_submit)
    ])
    
    # Verify page was created
    assert page is not None, "Page should be created"
    assert page.state == state, "State should be attached"
    assert len(page.content) == 4, "Should have 4 content items"
    
    print("✓ Component creation test passed!")


def test_route_registration():
    """
    Test that demonstrates route registration works correctly.
    """
    from drafter import route, Page
    from drafter.client_server.client_server import ClientServer
    
    print("Testing route registration...")
    
    # Create a test server
    server = ClientServer(custom_name="INTEGRATION_TEST")
    
    # Register a route
    @route(server=server)
    def test_route(state: str) -> Page:
        return Page(state, ["Test Route Content"])
    
    # Verify route was registered
    assert len(server.router.routes) > 0, "Route should be registered"
    
    # Call the route function directly
    result = test_route("test_state")
    assert isinstance(result, Page), "Route should return a Page"
    assert result.content == ["Test Route Content"], "Content should match"
    
    print("✓ Route registration test passed!")


def test_state_management():
    """
    Test that state objects work correctly across routes.
    """
    from drafter import route, Page, Button
    from drafter.client_server.client_server import ClientServer
    from dataclasses import dataclass
    
    print("Testing state management...")
    
    @dataclass
    class Counter:
        count: int
    
    server = ClientServer(custom_name="STATE_TEST")
    
    @route(server=server)
    def index(state: Counter) -> Page:
        return Page(state, [
            f"Count: {state.count}",
            Button("Increment", increment)
        ])
    
    @route(server=server)
    def increment(state: Counter) -> Page:
        state.count += 1
        return index(state)
    
    # Test state persistence
    initial_state = Counter(count=0)
    
    # First page load
    page1 = index(initial_state)
    assert initial_state.count == 0, "Initial count should be 0"
    
    # Increment
    page2 = increment(initial_state)
    assert initial_state.count == 1, "Count should be incremented to 1"
    
    # Increment again
    page3 = increment(initial_state)
    assert initial_state.count == 2, "Count should be incremented to 2"
    
    print("✓ State management test passed!")


def test_multiple_components():
    """
    Test creating pages with various component types.
    """
    from drafter import (
        Page, TextBox, Button, Header, TextArea, SelectBox, CheckBox,
        NumberedList, BulletedList, LineBreak, HorizontalRule
    )
    from dataclasses import dataclass
    
    print("Testing multiple component types...")
    
    @dataclass
    class FormState:
        name: str
        bio: str
        favorite: str
        subscribed: bool
    
    state = FormState(name="", bio="", favorite="option1", subscribed=False)
    
    # Create a complex page
    page = Page(state, [
        Header("User Registration"),
        "Please fill out the form:",
        LineBreak(),
        "Name:",
        TextBox("name"),
        "Biography:",
        TextArea("bio"),
        "Favorite option:",
        SelectBox("favorite", ["option1", "option2", "option3"]),
        CheckBox("subscribed"),
        "Subscribe to newsletter",
        HorizontalRule(),
        "Your tasks:",
        NumberedList(["Task 1", "Task 2", "Task 3"]),
        "Features:",
        BulletedList(["Feature A", "Feature B", "Feature C"]),
    ])
    
    assert page is not None, "Page should be created"
    assert len(page.content) > 10, "Page should have many components"
    
    print("✓ Multiple components test passed!")


def test_nested_content():
    """
    Test that components can be nested.
    """
    from drafter import Page, Div, Span, Header
    
    print("Testing nested content...")
    
    page = Page(None, [
        Header("Main Page"),
        Div([
            "This is a div with",
            Span(["nested", "content"]),
        ]),
    ])
    
    assert page is not None, "Page with nested content should be created"
    
    print("✓ Nested content test passed!")


if __name__ == "__main__":
    print("="*60)
    print("Running Drafter Integration Tests")
    print("="*60)
    print()
    
    try:
        test_component_creation()
        print()
        test_route_registration()
        print()
        test_state_management()
        print()
        test_multiple_components()
        print()
        test_nested_content()
        
        print()
        print("="*60)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print()
        print("="*60)
        print(f"✗ TEST FAILED: {e}")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ UNEXPECTED ERROR: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
