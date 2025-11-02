"""
Unit tests for Python client library components.
These tests verify that components can be created and have correct properties.
"""
import pytest
from drafter import (
    Page, TextBox, Button, Header, TextArea, SelectBox, CheckBox,
    NumberedList, BulletedList, Table, Link, Image, LineBreak, HorizontalRule,
    Div, Span, Text
)
from dataclasses import dataclass


def test_page_creation():
    """Test that Page objects can be created with various content types."""
    # Simple page with string content
    page = Page(None, ["Hello, World!"])
    assert page.content == ["Hello, World!"]
    assert page.state is None
    
    # Page with state
    @dataclass
    class State:
        name: str
    
    state = State(name="Alice")
    page = Page(state, ["Welcome!"])
    assert page.state == state
    assert isinstance(page.content, list)


def test_textbox_creation():
    """Test TextBox component creation."""
    textbox = TextBox("username")
    assert hasattr(textbox, 'name') or hasattr(textbox, 'key')
    
    # TextBox with default value
    textbox_with_default = TextBox("email", "user@example.com")
    assert textbox_with_default is not None


def test_button_creation():
    """Test Button component creation."""
    def dummy_handler(state):
        return Page(state, ["Handled"])
    
    button = Button("Click Me", dummy_handler)
    assert button is not None
    
    # Button with text label
    button_with_label = Button("Submit Form", dummy_handler)
    assert button_with_label is not None


def test_header_creation():
    """Test Header component creation."""
    header = Header("Main Title")
    assert header is not None
    
    # Header with level
    header_h2 = Header("Subtitle", 2)
    assert header_h2 is not None


def test_textarea_creation():
    """Test TextArea component creation."""
    textarea = TextArea("description")
    assert textarea is not None
    
    # TextArea with default value
    textarea_with_default = TextArea("bio", "Enter your bio here")
    assert textarea_with_default is not None


def test_selectbox_creation():
    """Test SelectBox component creation."""
    options = ["Option 1", "Option 2", "Option 3"]
    selectbox = SelectBox("choice", options)
    assert selectbox is not None
    
    # SelectBox with default selection
    selectbox_with_default = SelectBox("color", ["red", "blue", "green"], "blue")
    assert selectbox_with_default is not None


def test_checkbox_creation():
    """Test CheckBox component creation."""
    checkbox = CheckBox("agree_terms")
    assert checkbox is not None
    
    # CheckBox with default checked state
    checkbox_checked = CheckBox("newsletter", True)
    assert checkbox_checked is not None


def test_list_creation():
    """Test list components creation."""
    items = ["Item 1", "Item 2", "Item 3"]
    
    # Numbered list
    numbered_list = NumberedList(items)
    assert numbered_list is not None
    
    # Bulleted list
    bulleted_list = BulletedList(items)
    assert bulleted_list is not None


def test_table_creation():
    """Test Table component creation."""
    data = [
        ["Name", "Age"],
        ["Alice", "25"],
        ["Bob", "30"]
    ]
    table = Table(data)
    assert table is not None


def test_link_creation():
    """Test Link component creation."""
    def target_page(state):
        return Page(state, ["Target Page"])
    
    link = Link("Go to page", target_page)
    assert link is not None


def test_image_creation():
    """Test Image component creation."""
    image = Image("test.png")
    assert image is not None
    
    # Image with alt text
    image_with_alt = Image("logo.png", "Company Logo")
    assert image_with_alt is not None


def test_simple_components():
    """Test simple layout components."""
    # LineBreak
    line_break = LineBreak()
    assert line_break is not None
    
    # HorizontalRule
    hr = HorizontalRule()
    assert hr is not None
    
    # Text
    text = Text("Some text")
    assert text is not None
    
    # Div
    div = Div(["Content"])
    assert div is not None
    
    # Span
    span = Span(["Inline content"])
    assert span is not None


def test_complex_page_structure():
    """Test creating a page with multiple component types."""
    @dataclass
    class FormState:
        name: str
        email: str
        subscribed: bool
    
    def submit_handler(state, name, email, subscribed):
        state.name = name
        state.email = email
        state.subscribed = subscribed
        return Page(state, ["Form submitted!"])
    
    state = FormState(name="", email="", subscribed=False)
    
    page = Page(state, [
        Header("Registration Form"),
        "Please fill out the form:",
        LineBreak(),
        "Name:",
        TextBox("name", state.name),
        "Email:",
        TextBox("email", state.email),
        CheckBox("subscribed", state.subscribed),
        "Subscribe to newsletter",
        HorizontalRule(),
        Button("Submit", submit_handler)
    ])
    
    assert page is not None
    assert len(page.content) > 0


def test_nested_content():
    """Test that components can contain nested content."""
    nested_page = Page(None, [
        Header("Main Page"),
        Div([
            "This is a div",
            Span(["with nested", "content"]),
        ]),
        BulletedList([
            "First item",
            "Second item",
        ])
    ])
    
    assert nested_page is not None
    assert len(nested_page.content) > 0
