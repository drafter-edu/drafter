"""
Tests for LLM API integration functionality
"""
import pytest
from drafter.llm import LLMMessage, LLMResponse, LLMError, call_gpt, call_gemini
from drafter.llm import call_gpt_structured, call_gemini_structured
from drafter import ApiKeyBox
from dataclasses import dataclass
from typing import List


def test_llm_message_creation():
    """Test that LLMMessage can be created with valid roles."""
    msg = LLMMessage("user", "Hello, world!")
    assert msg.role == "user"
    assert msg.content == "Hello, world!"
    
    msg2 = LLMMessage("assistant", "Hi there!")
    assert msg2.role == "assistant"
    
    msg3 = LLMMessage("system", "You are a helpful assistant")
    assert msg3.role == "system"


def test_llm_message_invalid_role():
    """Test that LLMMessage rejects invalid roles."""
    with pytest.raises(ValueError, match="Role must be"):
        LLMMessage("invalid", "test")


def test_llm_response_creation():
    """Test that LLMResponse can be created."""
    response = LLMResponse(
        content="Hello!",
        model="gpt-3.5-turbo",
        finish_reason="stop",
        total_tokens=100
    )
    assert response.content == "Hello!"
    assert response.model == "gpt-3.5-turbo"
    assert response.finish_reason == "stop"
    assert response.total_tokens == 100


def test_llm_error_creation():
    """Test that LLMError can be created."""
    error = LLMError("AuthenticationError", "Invalid API key")
    assert error.error_type == "AuthenticationError"
    assert error.message == "Invalid API key"


def test_call_gpt_no_api_key():
    """Test that call_gpt returns error when no API key provided."""
    messages = [LLMMessage("user", "Hello")]
    result = call_gpt("", messages)
    assert isinstance(result, LLMError)
    assert result.error_type == "AuthenticationError"


def test_call_gpt_no_messages():
    """Test that call_gpt returns error when no messages provided."""
    result = call_gpt("fake-key", [])
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"


def test_call_gemini_no_api_key():
    """Test that call_gemini returns error when no API key provided."""
    messages = [LLMMessage("user", "Hello")]
    result = call_gemini("", messages)
    assert isinstance(result, LLMError)
    assert result.error_type == "AuthenticationError"


def test_call_gemini_no_messages():
    """Test that call_gemini returns error when no messages provided."""
    result = call_gemini("fake-key", [])
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"


def test_api_key_box_creation():
    """Test that ApiKeyBox component can be created."""
    box = ApiKeyBox("api_key", "gpt", "Enter your GPT API key:")
    assert box.name == "api_key"
    assert box.service == "gpt"
    assert box.label == "Enter your GPT API key:"


def test_api_key_box_renders():
    """Test that ApiKeyBox renders to HTML."""
    box = ApiKeyBox("gpt_key", "gpt", "GPT API Key:")
    html = str(box)
    assert "type='password'" in html
    assert "name='gpt_key'" in html
    assert "GPT API Key:" in html
    assert "drafterLLM" in html  # Should include JavaScript for local storage


def test_api_key_box_invalid_name():
    """Test that ApiKeyBox validates parameter name."""
    with pytest.raises(ValueError):
        ApiKeyBox("invalid name", "gpt")


def test_message_list_conversion():
    """Test that messages can be used as a list."""
    messages = [
        LLMMessage("system", "You are helpful"),
        LLMMessage("user", "Hello"),
        LLMMessage("assistant", "Hi!"),
        LLMMessage("user", "How are you?")
    ]
    assert len(messages) == 4
    assert messages[0].role == "system"
    assert messages[-1].content == "How are you?"


def test_structured_output_simple_dataclass():
    """Test that a simple dataclass can be defined for structured output."""
    @dataclass
    class SimpleResponse:
        """Simple response format.
        
        Attributes:
            message: The response message
            confidence: Confidence score from 0-100
        """
        message: str
        confidence: int
    
    # Just test that we can create the dataclass
    response = SimpleResponse("Hello", 95)
    assert response.message == "Hello"
    assert response.confidence == 95


def test_structured_output_nested_dataclass():
    """Test that nested dataclasses work for structured output."""
    @dataclass
    class Author:
        """Author information.
        
        Attributes:
            name: Author's name
            country: Author's country
        """
        name: str
        country: str
    
    @dataclass
    class Book:
        """Book information.
        
        Attributes:
            title: Book title
            author: Book author
            year: Publication year
        """
        title: str
        author: Author
        year: int
    
    # Test that we can create nested structures
    author = Author("Jane Doe", "USA")
    book = Book("Test Book", author, 2024)
    assert book.title == "Test Book"
    assert book.author.name == "Jane Doe"
    assert book.year == 2024


def test_structured_output_with_lists():
    """Test that dataclasses with lists work for structured output."""
    @dataclass
    class Recipe:
        """Recipe information.
        
        Attributes:
            name: Recipe name
            ingredients: List of ingredients
            steps: Cooking steps
        """
        name: str
        ingredients: List[str]
        steps: List[str]
    
    # Test that we can create dataclasses with lists
    recipe = Recipe("Pasta", ["pasta", "sauce"], ["boil", "mix"])
    assert recipe.name == "Pasta"
    assert len(recipe.ingredients) == 2
    assert len(recipe.steps) == 2


def test_call_gpt_structured_no_api_key():
    """Test that call_gpt_structured returns error when no API key provided."""
    @dataclass
    class TestFormat:
        """Test format.
        
        Attributes:
            value: Test value
        """
        value: str
    
    messages = [LLMMessage("user", "Hello")]
    result = call_gpt_structured("", messages, TestFormat)
    assert isinstance(result, LLMError)
    assert result.error_type == "AuthenticationError"


def test_call_gpt_structured_no_messages():
    """Test that call_gpt_structured returns error when no messages provided."""
    @dataclass
    class TestFormat:
        """Test format.
        
        Attributes:
            value: Test value
        """
        value: str
    
    result = call_gpt_structured("fake-key", [], TestFormat)
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"


def test_call_gpt_structured_invalid_format():
    """Test that call_gpt_structured returns error when format is not a dataclass."""
    messages = [LLMMessage("user", "Hello")]
    result = call_gpt_structured("fake-key", messages, str)  # str is not a dataclass
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"


def test_call_gemini_structured_no_api_key():
    """Test that call_gemini_structured returns error when no API key provided."""
    @dataclass
    class TestFormat:
        """Test format.
        
        Attributes:
            value: Test value
        """
        value: str
    
    messages = [LLMMessage("user", "Hello")]
    result = call_gemini_structured("", messages, TestFormat)
    assert isinstance(result, LLMError)
    assert result.error_type == "AuthenticationError"


def test_call_gemini_structured_no_messages():
    """Test that call_gemini_structured returns error when no messages provided."""
    @dataclass
    class TestFormat:
        """Test format.
        
        Attributes:
            value: Test value
        """
        value: str
    
    result = call_gemini_structured("fake-key", [], TestFormat)
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"


def test_call_gemini_structured_invalid_format():
    """Test that call_gemini_structured returns error when format is not a dataclass."""
    messages = [LLMMessage("user", "Hello")]
    result = call_gemini_structured("fake-key", messages, dict)  # dict is not a dataclass
    assert isinstance(result, LLMError)
    assert result.error_type == "ValueError"
