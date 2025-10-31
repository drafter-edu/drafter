"""
Unit tests for the Python client library.
These tests verify the core functionality of components and the Page class.
"""
import pytest
from drafter import Page, TextBox, Button, Text, Table, route, Server
from drafter import Header, LineBreak, HorizontalRule, CheckBox, SelectBox, TextArea
from drafter import Link, Image, Div, Span


class TestPage:
    """Test suite for the Page class."""

    def test_page_with_state_and_content(self):
        """Test creating a Page with state and content."""
        state = {"key": "value"}
        content = ["Hello, world!"]
        page = Page(state, content)
        
        assert page.state == state
        assert page.content == content

    def test_page_with_only_content(self):
        """Test creating a Page with only content (state defaults to None)."""
        content = ["Hello, world!"]
        page = Page(content)
        
        assert page.state is None
        assert page.content == content

    def test_page_converts_single_string_to_list(self):
        """Test that a single string is converted to a list."""
        page = Page("Hello, world!")
        assert page.content == ["Hello, world!"]

    def test_page_with_components(self):
        """Test creating a Page with component objects."""
        content = [
            "Welcome!",
            TextBox("username"),
            Button("Submit", lambda s: Page(s, ["Submitted!"]))
        ]
        page = Page(None, content)
        
        assert len(page.content) == 3
        assert isinstance(page.content[1], TextBox)
        assert isinstance(page.content[2], Button)

    def test_page_rejects_invalid_content_type(self):
        """Test that Page raises ValueError for invalid content types."""
        with pytest.raises(ValueError, match="must be a list"):
            Page(None, 123)

    def test_page_rejects_invalid_content_item(self):
        """Test that Page raises ValueError for invalid items in content list."""
        with pytest.raises(ValueError, match="must be a list of strings or components"):
            Page(None, ["Valid string", 123])


class TestTextComponents:
    """Test suite for text-based components."""

    def test_text_component(self):
        """Test creating a Text component."""
        text = Text("Hello, world!")
        assert text is not None
        assert "Hello, world!" in str(text)

    def test_text_component_with_markup(self):
        """Test that Text component handles HTML in the string."""
        text = Text("<b>Bold</b> text")
        text_str = str(text)
        assert text_str is not None

    def test_header_component(self):
        """Test creating a Header component."""
        header = Header("My Title")
        assert header is not None
        text_str = str(header)
        assert "My Title" in text_str

    def test_header_with_level(self):
        """Test creating a Header with specific level."""
        header = Header("Subtitle", 2)
        text_str = str(header)
        assert "Subtitle" in text_str


class TestInputComponents:
    """Test suite for input components."""

    def test_textbox_component(self):
        """Test creating a TextBox component."""
        textbox = TextBox("username")
        assert textbox is not None
        assert textbox.name == "username"

    def test_textbox_with_default_value(self):
        """Test creating a TextBox with a default value."""
        textbox = TextBox("username", "default_user")
        assert textbox.name == "username"
        assert textbox.default_value == "default_user"

    def test_textbox_name_validation(self):
        """Test that TextBox validates parameter names."""
        # Valid names
        TextBox("valid_name")
        TextBox("_valid")
        TextBox("valid123")
        
        # Invalid names should raise ValueError
        with pytest.raises(ValueError):
            TextBox("invalid name")  # space
        
        with pytest.raises(ValueError):
            TextBox("123invalid")  # starts with digit
        
        with pytest.raises(ValueError):
            TextBox("")  # empty string

    def test_textarea_component(self):
        """Test creating a TextArea component."""
        textarea = TextArea("message")
        assert textarea is not None
        assert textarea.name == "message"

    def test_textarea_with_default(self):
        """Test creating a TextArea with default value."""
        textarea = TextArea("message", "Default text")
        assert textarea.default_value == "Default text"

    def test_checkbox_component(self):
        """Test creating a CheckBox component."""
        checkbox = CheckBox("agree")
        assert checkbox is not None
        assert checkbox.name == "agree"

    def test_checkbox_default_value(self):
        """Test CheckBox with default value."""
        checkbox_checked = CheckBox("agree", True)
        assert checkbox_checked.default_value == True
        
        checkbox_unchecked = CheckBox("disagree", False)
        assert checkbox_unchecked.default_value == False

    def test_selectbox_component(self):
        """Test creating a SelectBox component."""
        options = ["Option 1", "Option 2", "Option 3"]
        selectbox = SelectBox("choice", options)
        assert selectbox is not None
        assert selectbox.name == "choice"
        assert selectbox.options == options

    def test_selectbox_with_default(self):
        """Test SelectBox with default selection."""
        options = ["A", "B", "C"]
        selectbox = SelectBox("letter", options, "B")
        assert selectbox.default_value == "B"


class TestButtonAndLink:
    """Test suite for Button and Link components."""

    def test_button_component(self):
        """Test creating a Button component."""
        def on_click(state):
            return Page(state, ["Clicked!"])
        
        button = Button("Click me", on_click)
        assert button is not None
        assert button.text == "Click me"

    def test_button_with_callable_url(self):
        """Test button with function reference as URL."""
        def target_page(state):
            return Page(state, ["Target"])
        
        button = Button("Go", target_page)
        assert button is not None

    def test_link_component(self):
        """Test creating a Link component."""
        link = Link("Click here", "page2")
        assert link is not None
        assert link.text == "Click here"
        assert "page2" in link.url


class TestLayoutComponents:
    """Test suite for layout components."""

    def test_linebreak_component(self):
        """Test creating a LineBreak component."""
        lb = LineBreak()
        assert lb is not None
        assert "<br" in str(lb).lower()

    def test_horizontal_rule_component(self):
        """Test creating a HorizontalRule component."""
        hr = HorizontalRule()
        assert hr is not None
        assert "<hr" in str(hr).lower()

    def test_div_component(self):
        """Test creating a Div component."""
        div = Div("content")
        assert div is not None
        text_str = str(div)
        assert "content" in text_str

    def test_span_component(self):
        """Test creating a Span component."""
        span = Span("inline text")
        assert span is not None
        text_str = str(span)
        assert "inline text" in text_str


class TestTableComponent:
    """Test suite for Table component."""

    def test_table_component(self):
        """Test creating a Table component."""
        data = [["A", "B"], ["C", "D"]]
        table = Table(data)
        assert table is not None
        assert table.rows == data

    def test_table_with_header(self):
        """Test creating a Table with a header."""
        data = [["Alice", "25"], ["Bob", "30"]]
        header = ["Name", "Age"]
        table = Table(data, header=header)
        assert table.header == header

    def test_table_renders_html(self):
        """Test that Table renders to HTML."""
        data = [["1", "2"]]
        table = Table(data)
        html = str(table)
        assert "<table" in html
        assert "<tr" in html
        assert "<td" in html


class TestRouteDecorator:
    """Test suite for the route decorator."""

    def test_route_decorator_basic(self):
        """Test basic route decorator usage."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route("index", server=server)
        def index(state):
            return Page(state, ["Index page"])
        
        assert "index" in server.routes
        assert server.routes["index"] == index

    def test_route_decorator_preserves_function(self):
        """Test that route decorator preserves the original function."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route("test", server=server)
        def test_func(state):
            return Page(state, ["Test"])
        
        # Function should still be callable
        result = test_func(None)
        assert isinstance(result, Page)

    def test_route_with_function_name_as_url(self):
        """Test route decorator using function name as URL."""
        server = Server(_custom_name="TEST_SERVER")
        
        @route(server=server)
        def my_custom_page(state):
            return Page(state, ["Custom"])
        
        assert "my_custom_page" in server.routes


class TestImageComponent:
    """Test suite for Image component."""

    def test_image_component(self):
        """Test creating an Image component."""
        image = Image("logo.png")
        assert image is not None
        assert image.url == "logo.png"

    def test_image_with_dimensions(self):
        """Test Image with width and height."""
        image = Image("photo.jpg", width=300, height=200)
        assert image.width == 300
        assert image.height == 200


class TestComponentRendering:
    """Test suite for component HTML rendering."""

    def test_textbox_renders_input(self):
        """Test that TextBox renders an input element."""
        textbox = TextBox("email")
        html = str(textbox)
        assert "<input" in html
        assert 'name="email"' in html

    def test_button_renders_button(self):
        """Test that Button renders a button element."""
        button = Button("Submit", lambda s: Page(s, []))
        html = str(button)
        assert "<button" in html
        assert "Submit" in html

    def test_header_renders_heading(self):
        """Test that Header renders a heading element."""
        header = Header("Title", 1)
        html = str(header)
        assert "<h1" in html
        assert "Title" in html
