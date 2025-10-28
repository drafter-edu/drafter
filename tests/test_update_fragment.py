"""
Tests for Update and Fragment return types
"""
from tests.helpers import *


def test_update_creation():
    """Test that Update objects can be created with state"""
    state = {"count": 5}
    update = Update(state)
    assert update.state == state


def test_fragment_creation_with_string():
    """Test that Fragment objects can be created with a string content"""
    state = {"count": 5}
    fragment = Fragment(state, "#target", "Hello World")
    assert fragment.state == state
    assert fragment.target == "#target"
    assert fragment.content == ["Hello World"]


def test_fragment_creation_with_list():
    """Test that Fragment objects can be created with list content"""
    state = {"count": 5}
    content = ["Line 1", "Line 2"]
    fragment = Fragment(state, "#target", content)
    assert fragment.state == state
    assert fragment.target == "#target"
    assert fragment.content == content


def test_fragment_creation_with_component():
    """Test that Fragment objects can be created with PageContent"""
    state = {"count": 5}
    button = Button("Click", "index")
    fragment = Fragment(state, "#target", button)
    assert fragment.state == state
    assert fragment.target == "#target"
    assert fragment.content == [button]


def test_fragment_render_content():
    """Test that Fragment can render its content"""
    from drafter.configuration import ServerConfiguration
    
    state = {"count": 5}
    content = ["Line 1", "Line 2"]
    fragment = Fragment(state, "#target", content)
    
    config = ServerConfiguration()
    rendered = fragment.render_content(state, config)
    
    assert "<p>Line 1</p>" in rendered
    assert "<p>Line 2</p>" in rendered


def test_fragment_invalid_content():
    """Test that Fragment raises error for invalid content"""
    state = {"count": 5}
    try:
        fragment = Fragment(state, "#target", 123)  # Invalid: number
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be a string, PageContent, or a list" in str(e)


def test_update_response_basic():
    """Test that Update can be returned from a route function"""
    drafter_server = TestServer()
    
    @route(server=drafter_server.server)
    def index(state: int) -> Page:
        return Page(state, [f"Count: {state}"])
    
    @route(server=drafter_server.server)
    def increment(state: int) -> Update:
        return Update(state + 1)
    
    # Set up the server
    drafter_server.server.setup(0)
    
    # Test calling the increment route directly
    result = drafter_server.server.routes['/increment']()
    
    # Verify it returns JSON with the right structure
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["type"] == "update"
    assert data["success"] is True


def test_fragment_response_basic():
    """Test that Fragment can be returned from a route function"""
    drafter_server = TestServer()
    
    @route(server=drafter_server.server)
    def index(state: int) -> Page:
        return Page(state, [f"Count: {state}"])
    
    @route(server=drafter_server.server)
    def increment_fragment(state: int) -> Fragment:
        new_state = state + 1
        return Fragment(new_state, "#counter", [f"Count: {new_state}"])
    
    # Set up the server
    drafter_server.server.setup(0)
    
    # Test calling the fragment route directly
    result = drafter_server.server.routes['/increment_fragment']()
    
    # Verify it returns JSON with the right structure
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["type"] == "fragment"
    assert data["target"] == "#counter"
    assert "Count: 1" in data["content"]


def test_fragment_with_multiple_components():
    """Test Fragment with multiple PageContent components"""
    from drafter.configuration import ServerConfiguration
    
    state = {"items": ["A", "B", "C"]}
    fragment = Fragment(
        state,
        "#list",
        [
            "Items:",
            NumberedList(state["items"]),
            Button("Add", "add_item")
        ]
    )
    
    config = ServerConfiguration()
    rendered = fragment.render_content(state, config)
    
    assert "<p>Items:</p>" in rendered
    assert "<ol" in rendered  # May have attributes, so just check for opening tag
    assert "<button" in rendered


def test_update_preserves_state_type():
    """Test that Update preserves the state type"""
    from dataclasses import dataclass
    
    @dataclass
    class State:
        count: int
        name: str
    
    state = State(count=5, name="Test")
    update = Update(state)
    
    assert isinstance(update.state, State)
    assert update.state.count == 5
    assert update.state.name == "Test"


def test_fragment_preserves_state_type():
    """Test that Fragment preserves the state type"""
    from dataclasses import dataclass
    
    @dataclass
    class State:
        count: int
        items: list
    
    state = State(count=5, items=["A", "B"])
    fragment = Fragment(state, "#target", ["Updated"])
    
    assert isinstance(fragment.state, State)
    assert fragment.state.count == 5
    assert fragment.state.items == ["A", "B"]
