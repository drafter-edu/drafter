"""Tests for the API Explorer feature"""
from drafter import Server, Page, route


def test_api_explorer_basic():
    """Test that the API explorer endpoint exists and returns HTML"""
    server = Server(_custom_name="TEST_API_EXPLORER")
    
    @route(server=server)
    def index(state: str) -> Page:
        """Main page"""
        return Page(["Hello world"])

    @route(server=server)
    def greet(state: str, name: str, age: int) -> Page:
        """Greet a user"""
        return Page([f"Hello {name}, age {age}"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    assert 'API Explorer' in result
    assert 'Test your route endpoints' in result


def test_api_explorer_shows_routes():
    """Test that the API explorer shows all routes"""
    server = Server(_custom_name="TEST_API_EXPLORER")

    @route(server=server)
    def index(state: str) -> Page:
        """Main page"""
        return Page(["Hello world"])

    @route(server=server)
    def greet(state: str, name: str) -> Page:
        """Greet a user"""
        return Page([f"Hello {name}"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    # Check that routes are displayed
    assert 'index' in result
    assert 'greet' in result
    # Check that function signatures are shown
    assert 'state: str' in result
    assert 'name: str' in result


def test_api_explorer_shows_docstrings():
    """Test that the API explorer displays function docstrings"""
    server = Server(_custom_name="TEST_API_EXPLORER")

    @route(server=server)
    def index(state: str) -> Page:
        """This is the main page"""
        return Page(["Hello world"])

    @route(server=server)
    def greet(state: str, name: str) -> Page:
        """Greet a user by name"""
        return Page([f"Hello {name}"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    # Check that docstrings are displayed
    assert 'This is the main page' in result
    assert 'Greet a user by name' in result


def test_api_explorer_shows_forms_for_parameters():
    """Test that the API explorer generates forms for routes with parameters"""
    server = Server(_custom_name="TEST_API_EXPLORER")

    @route(server=server)
    def index(state: str) -> Page:
        """Main page"""
        return Page(["Hello world"])

    @route(server=server)
    def greet(state: str, name: str, age: int) -> Page:
        """Greet a user"""
        return Page([f"Hello {name}, age {age}"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    # Check that form elements are present
    assert 'Test this endpoint' in result
    assert 'name' in result
    assert 'age' in result
    # Check for input types
    assert 'type="text"' in result or 'type=\'text\'' in result
    assert 'type="number"' in result or 'type=\'number\'' in result


def test_api_explorer_no_form_for_state_only():
    """Test that routes with only state parameter don't show a form"""
    server = Server(_custom_name="TEST_API_EXPLORER")

    @route(server=server)
    def index(state: str) -> Page:
        """Main page"""
        return Page(["Hello world"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    # Routes with only state should have a "Visit this route" link
    assert 'Visit this route' in result


def test_api_explorer_has_javascript():
    """Test that the API explorer includes the testing JavaScript"""
    server = Server(_custom_name="TEST_API_EXPLORER")

    @route(server=server)
    def index(state: str) -> Page:
        """Main page"""
        return Page(["Hello world"])

    server._state = None  # Set state without calling setup
    
    result = server.api_explorer()
    # Check for JavaScript function
    assert 'function testRoute' in result
    assert 'fetch(' in result

