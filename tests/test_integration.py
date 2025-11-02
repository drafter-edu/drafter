"""
Integration test demonstrating the full test infrastructure.
This test creates a simple Drafter app and tests it end-to-end.
"""
try:
    import pytest
except ImportError:
    pytest = None
    
from pathlib import Path
from starlette.testclient import TestClient
from drafter.app.app_server import make_app, DevConfig


def test_complete_drafter_workflow():
    """
    Full integration test that demonstrates:
    1. Creating a Drafter application
    2. Launching the server
    3. Accessing the page
    4. Verifying content is served
    """
    # Create a minimal working Drafter application
    test_file = Path(__file__).parent / "fixtures" / "integration_test.py"
    test_file.parent.mkdir(exist_ok=True)
    
    # Write a simple but complete Drafter app
    test_code = '''from drafter import route, Page, Button, TextBox
from dataclasses import dataclass

@dataclass
class State:
    name: str
    greeting: str

@route
def index(state: State) -> Page:
    return Page(state, [
        "Welcome to Drafter!",
        "Enter your name:",
        TextBox("user_name", state.name),
        Button("Greet Me", greet)
    ])

@route
def greet(state: State, user_name: str) -> Page:
    state.name = user_name
    state.greeting = f"Hello, {user_name}!"
    return Page(state, [
        state.greeting,
        Button("Go Back", index)
    ])

# This would normally call start_server(State("", ""))
# but for testing we skip that
'''
    test_file.write_text(test_code)
    
    # Create server configuration
    config = DevConfig(
        title="Integration Test App",
        user_path=test_file,
        inline_py=True,
        host="localhost",
        port=8080
    )
    
    # Create the Starlette app
    app = make_app(config)
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Server responds
    response = client.get("/")
    assert response.status_code == 200, "Server should respond with 200 OK"
    
    # Test 2: Title is in response
    html = response.text
    assert "Integration Test App" in html, "Page title should be in HTML"
    
    # Test 3: Required elements are present
    assert "drafter" in html.lower() or "skulpt" in html.lower(), \
        "Drafter/Skulpt should be referenced"
    assert "<script" in html, "JavaScript should be included"
    assert "drafter-root" in html.lower(), "Root element should exist"
    
    # Test 4: User code is embedded (if inline_py is True)
    if config.inline_py:
        assert "Welcome to Drafter" in html or "index" in html, \
            "User code or its elements should be in the page"
    
    # Cleanup
    test_file.unlink()
    
    print("✓ Complete integration test passed!")


def test_component_creation_and_serialization():
    """
    Test that demonstrates component creation works correctly.
    This is a unit test that doesn't require a server.
    """
    from drafter import Page, TextBox, Button, Header
    from dataclasses import dataclass
    
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


if __name__ == "__main__":
    # Run tests if executed directly
    print("Running integration tests...\n")
    
    try:
        test_component_creation_and_serialization()
        print()
        test_route_registration()
        print()
        test_complete_drafter_workflow()
        print("\n✓ All integration tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
