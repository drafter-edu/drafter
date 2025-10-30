"""
LLM API Integration for Drafter

This module provides simplified access to popular LLM APIs like GPT and Gemini.
It handles API key management through local storage and provides a student-friendly
interface using only lists and dataclasses.
"""

from dataclasses import dataclass, fields, is_dataclass, MISSING
from typing import List, Optional, Any, Type, get_origin, get_args, Union
import json
import re

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class LLMMessage:
    """
    Represents a single message in an LLM conversation.
    
    :param role: The role of the message sender ('user', 'assistant', or 'system')
    :type role: str
    :param content: The text content of the message
    :type content: str
    """
    role: str
    content: str
    
    def __post_init__(self):
        if self.role not in ('user', 'assistant', 'system'):
            raise ValueError("Role must be 'user', 'assistant', or 'system'")


@dataclass
class LLMResponse:
    """
    Represents a response from an LLM API.
    
    :param content: The generated text response
    :type content: str
    :param model: The model that generated the response
    :type model: str
    :param finish_reason: Why the model stopped generating (e.g., 'stop', 'length')
    :type finish_reason: str
    :param total_tokens: Total number of tokens used in the request and response
    :type total_tokens: int
    """
    content: str
    model: str
    finish_reason: str
    total_tokens: int


@dataclass
class LLMError:
    """
    Represents an error from an LLM API call.
    
    :param error_type: The type of error that occurred
    :type error_type: str
    :param message: A human-readable error message
    :type message: str
    """
    error_type: str
    message: str


def call_gpt(api_key: str, messages: List[LLMMessage], model: str = "gpt-3.5-turbo", 
             temperature: float = 0.7, max_tokens: int = 1000) -> Any:
    """
    Call the OpenAI GPT API with a list of messages.
    
    This function sends a request to the OpenAI API and returns either an LLMResponse
    on success or an LLMError on failure. The function is designed to work with Skulpt's
    `requests` module for client-side execution.
    
    :param api_key: Your OpenAI API key
    :type api_key: str
    :param messages: List of LLMMessage objects representing the conversation history
    :type messages: List[LLMMessage]
    :param model: The GPT model to use (default: "gpt-3.5-turbo")
    :type model: str
    :param temperature: Controls randomness (0.0-2.0, default: 0.7)
    :type temperature: float
    :param max_tokens: Maximum tokens to generate (default: 1000)
    :type max_tokens: int
    :return: LLMResponse on success, LLMError on failure
    :rtype: Union[LLMResponse, LLMError]
    
    Example:
        >>> api_key = "sk-..."
        >>> messages = [
        ...     LLMMessage("user", "What is the capital of France?")
        ... ]
        >>> response = call_gpt(api_key, messages)
        >>> if isinstance(response, LLMResponse):
        ...     print(response.content)
        ... else:
        ...     print(f"Error: {response.message}")
    """
    if not HAS_REQUESTS:
        return LLMError("ImportError", "The requests module is required but not available")
    
    if not api_key:
        return LLMError("AuthenticationError", "API key is required")
    
    if not messages:
        return LLMError("ValueError", "At least one message is required")
    
    # Convert LLMMessage objects to the format expected by OpenAI API
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            choice = data["choices"][0]
            message_content = choice["message"]["content"]
            finish_reason = choice["finish_reason"]
            total_tokens = data["usage"]["total_tokens"]
            
            return LLMResponse(
                content=message_content,
                model=data["model"],
                finish_reason=finish_reason,
                total_tokens=total_tokens
            )
        elif response.status_code == 401:
            return LLMError("AuthenticationError", "Invalid API key")
        elif response.status_code == 429:
            return LLMError("RateLimitError", "Rate limit exceeded or quota reached")
        else:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return LLMError("APIError", error_message)
            
    except Exception as e:
        return LLMError("NetworkError", f"Failed to connect to API: {str(e)}")


def call_gemini(api_key: str, messages: List[LLMMessage],
                model: str = "gemini-2.5-flash",
                temperature: float = 0.7, max_tokens: int = 1000) -> Any:
    """
    Call the Google Gemini API with a list of messages.
    
    This function sends a request to the Google Gemini API and returns either an LLMResponse
    on success or an LLMError on failure. The function is designed to work with Skulpt's
    `requests` module for client-side execution.
    
    :param api_key: Your Google API key
    :type api_key: str
    :param messages: List of LLMMessage objects representing the conversation
    :type messages: List[LLMMessage]
    :param model: The Gemini model to use (default: "gemini-pro")
    :type model: str
    :param temperature: Controls randomness (0.0-2.0, default: 0.7)
    :type temperature: float
    :param max_tokens: Maximum tokens to generate (default: 1000)
    :type max_tokens: int
    :return: LLMResponse on success, LLMError on failure
    :rtype: Union[LLMResponse, LLMError]
    
    Example:
        >>> api_key = "AIza..."
        >>> messages = [
        ...     LLMMessage("user", "What is the capital of France?")
        ... ]
        >>> response = call_gemini(api_key, messages)
        >>> if isinstance(response, LLMResponse):
        ...     print(response.content)
        ... else:
        ...     print(f"Error: {response.message}")
    """
    if not HAS_REQUESTS:
        return LLMError("ImportError", "The requests module is required but not available")
    
    if not api_key:
        return LLMError("AuthenticationError", "API key is required")
    
    if not messages:
        return LLMError("ValueError", "At least one message is required")
    
    # Convert messages to Gemini format
    # Gemini uses a "contents" array with "parts"
    contents = []
    for msg in messages:
        # Map roles: Gemini uses 'user' and 'model' instead of 'user' and 'assistant'
        role = "model" if msg.role == "assistant" else "user"
        # Skip system messages for now as Gemini handles them differently
        if msg.role != "system":
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if "candidates" not in data or not data["candidates"]:
                return LLMError("APIError", "No response generated")
            
            candidate = data["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            finish_reason = candidate.get("finishReason", "STOP")
            
            # Gemini doesn't always provide token counts in the same way
            total_tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
            
            return LLMResponse(
                content=content,
                model=model,
                finish_reason=finish_reason,
                total_tokens=total_tokens
            )
        elif response.status_code == 400:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", "Invalid request")
            return LLMError("ValueError", error_message)
        elif response.status_code == 403:
            return LLMError("AuthenticationError", "Invalid API key or permission denied")
        elif response.status_code == 429:
            return LLMError("RateLimitError", "Rate limit exceeded or quota reached")
        else:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return LLMError("APIError", error_message)
            
    except Exception as e:
        return LLMError("NetworkError", f"Failed to connect to API: {str(e)}")


def _parse_google_docstring(docstring: str) -> dict:
    """
    Parse Google-style docstring to extract Attributes section.
    
    Returns a dictionary mapping attribute names to their descriptions.
    """
    if not docstring:
        return {}
    
    # Look for "Attributes:" section
    attributes_pattern = r'Attributes:\s*\n((?:\s+\w+.*\n)*)'
    match = re.search(attributes_pattern, docstring)
    
    if not match:
        return {}
    
    attributes_section = match.group(1)
    result = {}
    
    # Parse each attribute line (format: "    name: description" or "    name (type): description")
    lines = attributes_section.split('\n')
    current_attr = None
    current_desc = []
    
    for line in lines:
        if not line.strip():
            continue
            
        # Check if this is a new attribute (starts with spaces followed by word and colon)
        attr_match = re.match(r'\s+(\w+)(?:\s*\([^)]+\))?\s*:\s*(.*)', line)
        if attr_match:
            # Save previous attribute if exists
            if current_attr:
                result[current_attr] = ' '.join(current_desc).strip()
            # Start new attribute
            current_attr = attr_match.group(1)
            current_desc = [attr_match.group(2)]
        elif current_attr and line.startswith('        '):
            # Continuation of previous description
            current_desc.append(line.strip())
    
    # Save last attribute
    if current_attr:
        result[current_attr] = ' '.join(current_desc).strip()
    
    return result


def _dataclass_to_schema(dataclass_type: Type, descriptions: dict = None) -> dict:
    """
    Convert a dataclass to JSON Schema format.
    
    Supports nested dataclasses, lists, and primitive types.
    Extracts field descriptions from the class docstring using Google-style format.
    """
    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")
    
    # Parse docstring for field descriptions if not provided
    if descriptions is None:
        descriptions = _parse_google_docstring(dataclass_type.__doc__)
    
    schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
    
    for field in fields(dataclass_type):
        field_name = field.name
        field_type = field.type
        
        # Determine if field is required
        if field.default is MISSING and field.default_factory is MISSING:
            schema["required"].append(field_name)
        
        # Get field description
        description = descriptions.get(field_name, "")
        
        # Convert type to JSON Schema
        field_schema = _type_to_schema(field_type, description)
        schema["properties"][field_name] = field_schema
    
    return schema


def _type_to_schema(field_type: Type, description: str = "") -> dict:
    """Convert a Python type annotation to JSON Schema."""
    # Get origin for generic types (List, Optional, etc.)
    origin = get_origin(field_type)
    
    # Handle Optional (Union with None)
    if origin is Union:
        args = get_args(field_type)
        # Check if it's Optional (Union with None)
        if type(None) in args:
            # Get the non-None type
            actual_type = next(arg for arg in args if arg is not type(None))
            schema = _type_to_schema(actual_type, description)
            # Optional fields are nullable
            return schema
        # For other Unions, just use the first type
        return _type_to_schema(args[0], description)
    
    # Handle List
    if origin is list or origin is List:
        args = get_args(field_type)
        item_type = args[0] if args else Any
        item_schema = _type_to_schema(item_type, "")
        schema = {
            "type": "array",
            "items": item_schema
        }
        if description:
            schema["description"] = description
        return schema
    
    # Handle dataclasses (nested objects)
    if is_dataclass(field_type):
        nested_schema = _dataclass_to_schema(field_type)
        if description:
            nested_schema["description"] = description
        return nested_schema
    
    # Handle primitive types
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean"
    }
    
    json_type = type_mapping.get(field_type, "string")
    schema = {"type": json_type}
    if description:
        schema["description"] = description
    
    return schema


def call_gpt_structured(api_key: str, messages: List[LLMMessage], 
                       response_format: Type, model: str = "gpt-4o-2024-08-06",
                       temperature: float = 0.7, max_tokens: int = 1000) -> Any:
    """
    Call the OpenAI GPT API with structured output format.
    
    This function requests a response in a specific JSON structure defined by a dataclass.
    The dataclass should have a Google-style docstring with an Attributes section describing
    each field. Nested dataclasses and lists are supported.
    
    :param api_key: Your OpenAI API key
    :type api_key: str
    :param messages: List of LLMMessage objects representing the conversation history
    :type messages: List[LLMMessage]
    :param response_format: A dataclass type defining the expected response structure
    :type response_format: Type
    :param model: The GPT model to use (default: "gpt-4o-2024-08-06", supports structured output)
    :type model: str
    :param temperature: Controls randomness (0.0-2.0, default: 0.7)
    :type temperature: float
    :param max_tokens: Maximum tokens to generate (default: 1000)
    :type max_tokens: int
    :return: An instance of response_format on success, LLMError on failure
    :rtype: Union[response_format, LLMError]
    
    Example:
        >>> @dataclass
        ... class RecipeInfo:
        ...     '''Recipe information.
        ...     
        ...     Attributes:
        ...         name: The name of the recipe
        ...         ingredients: List of ingredients needed
        ...         steps: List of preparation steps
        ...     '''
        ...     name: str
        ...     ingredients: List[str]
        ...     steps: List[str]
        >>> 
        >>> messages = [LLMMessage("user", "Give me a simple pasta recipe")]
        >>> result = call_gpt_structured(api_key, messages, RecipeInfo)
        >>> if isinstance(result, RecipeInfo):
        ...     print(f"Recipe: {result.name}")
        ...     print(f"Ingredients: {', '.join(result.ingredients)}")
    """
    if not HAS_REQUESTS:
        return LLMError("ImportError", "The requests module is required but not available")
    
    if not api_key:
        return LLMError("AuthenticationError", "API key is required")
    
    if not messages:
        return LLMError("ValueError", "At least one message is required")
    
    if not is_dataclass(response_format):
        return LLMError("ValueError", "response_format must be a dataclass")
    
    # Convert dataclass to JSON Schema
    try:
        schema = _dataclass_to_schema(response_format)
    except Exception as e:
        return LLMError("ValueError", f"Failed to convert dataclass to schema: {str(e)}")
    
    # Convert LLMMessage objects to the format expected by OpenAI API
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": response_format.__name__,
                "strict": True,
                "schema": schema
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            choice = data["choices"][0]
            message_content = choice["message"]["content"]
            
            # Parse JSON response and create dataclass instance
            try:
                json_data = json.loads(message_content)
                result = _dict_to_dataclass(json_data, response_format)
                return result
            except Exception as e:
                return LLMError("ParseError", f"Failed to parse structured response: {str(e)}")
            
        elif response.status_code == 401:
            return LLMError("AuthenticationError", "Invalid API key")
        elif response.status_code == 429:
            return LLMError("RateLimitError", "Rate limit exceeded or quota reached")
        else:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return LLMError("APIError", error_message)
            
    except Exception as e:
        return LLMError("NetworkError", f"Failed to connect to API: {str(e)}")


def call_gemini_structured(api_key: str, messages: List[LLMMessage],
                          response_format: Type, model: str = "gemini-1.5-pro",
                          temperature: float = 0.7, max_tokens: int = 1000) -> Any:
    """
    Call the Google Gemini API with structured output format.
    
    This function requests a response in a specific JSON structure defined by a dataclass.
    The dataclass should have a Google-style docstring with an Attributes section describing
    each field. Nested dataclasses and lists are supported.
    
    :param api_key: Your Google API key
    :type api_key: str
    :param messages: List of LLMMessage objects representing the conversation
    :type messages: List[LLMMessage]
    :param response_format: A dataclass type defining the expected response structure
    :type response_format: Type
    :param model: The Gemini model to use (default: "gemini-1.5-pro")
    :type model: str
    :param temperature: Controls randomness (0.0-2.0, default: 0.7)
    :type temperature: float
    :param max_tokens: Maximum tokens to generate (default: 1000)
    :type max_tokens: int
    :return: An instance of response_format on success, LLMError on failure
    :rtype: Union[response_format, LLMError]
    
    Example:
        >>> @dataclass
        ... class MovieReview:
        ...     '''Movie review information.
        ...     
        ...     Attributes:
        ...         title: The movie title
        ...         rating: Rating from 1-10
        ...         summary: Brief review summary
        ...     '''
        ...     title: str
        ...     rating: int
        ...     summary: str
        >>> 
        >>> messages = [LLMMessage("user", "Review the movie Inception")]
        >>> result = call_gemini_structured(api_key, messages, MovieReview)
        >>> if isinstance(result, MovieReview):
        ...     print(f"{result.title}: {result.rating}/10")
    """
    if not HAS_REQUESTS:
        return LLMError("ImportError", "The requests module is required but not available")
    
    if not api_key:
        return LLMError("AuthenticationError", "API key is required")
    
    if not messages:
        return LLMError("ValueError", "At least one message is required")
    
    if not is_dataclass(response_format):
        return LLMError("ValueError", "response_format must be a dataclass")
    
    # Convert dataclass to JSON Schema
    try:
        schema = _dataclass_to_schema(response_format)
    except Exception as e:
        return LLMError("ValueError", f"Failed to convert dataclass to schema: {str(e)}")
    
    # Convert messages to Gemini format
    contents = []
    for msg in messages:
        role = "model" if msg.role == "assistant" else "user"
        if msg.role != "system":
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if "candidates" not in data or not data["candidates"]:
                return LLMError("APIError", "No response generated")
            
            candidate = data["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            
            # Parse JSON response and create dataclass instance
            try:
                json_data = json.loads(content)
                result = _dict_to_dataclass(json_data, response_format)
                return result
            except Exception as e:
                return LLMError("ParseError", f"Failed to parse structured response: {str(e)}")
            
        elif response.status_code == 400:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", "Invalid request")
            return LLMError("ValueError", error_message)
        elif response.status_code == 403:
            return LLMError("AuthenticationError", "Invalid API key or permission denied")
        elif response.status_code == 429:
            return LLMError("RateLimitError", "Rate limit exceeded or quota reached")
        else:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            return LLMError("APIError", error_message)
            
    except Exception as e:
        return LLMError("NetworkError", f"Failed to connect to API: {str(e)}")


def _dict_to_dataclass(data: dict, dataclass_type: Type) -> Any:
    """
    Convert a dictionary to a dataclass instance, handling nested dataclasses and lists.
    """
    if not is_dataclass(dataclass_type):
        return data
    
    field_values = {}
    for field in fields(dataclass_type):
        field_name = field.name
        if field_name not in data:
            # Use default value if available
            if field.default is not MISSING:
                field_values[field_name] = field.default
            elif field.default_factory is not MISSING:
                field_values[field_name] = field.default_factory()
            continue
        
        value = data[field_name]
        field_type = field.type
        
        # Handle Optional types
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            if type(None) in args:
                field_type = next(arg for arg in args if arg is not type(None))
                origin = get_origin(field_type)
        
        # Handle List types
        if origin is list or origin is List:
            args = get_args(field_type)
            if args and is_dataclass(args[0]):
                # List of dataclasses
                field_values[field_name] = [_dict_to_dataclass(item, args[0]) for item in value]
            else:
                field_values[field_name] = value
        # Handle nested dataclasses
        elif is_dataclass(field_type):
            field_values[field_name] = _dict_to_dataclass(value, field_type)
        else:
            field_values[field_name] = value
    
    return dataclass_type(**field_values)


# JavaScript code for local storage management (injected into Skulpt environment)
LOCAL_STORAGE_JS = """
<script>
// Drafter LLM Local Storage Helper Functions
window.drafterLLM = {
    saveApiKey: function(service, apiKey) {
        localStorage.setItem('drafter_llm_' + service, apiKey);
    },
    loadApiKey: function(service) {
        return localStorage.getItem('drafter_llm_' + service) || '';
    },
    clearApiKey: function(service) {
        localStorage.removeItem('drafter_llm_' + service);
    }
};
</script>
"""


def get_stored_api_key(service: str) -> str:
    """
    Retrieve a stored API key from local storage.
    
    This function works in Skulpt environments by using JavaScript's localStorage.
    In non-Skulpt environments, it returns an empty string.
    
    :param service: The service name ('gpt' or 'gemini')
    :type service: str
    :return: The stored API key or empty string if not found
    :rtype: str
    
    Example:
        >>> api_key = get_stored_api_key('gpt')
        >>> if api_key:
        ...     response = call_gpt(api_key, messages)
    """
    try:
        # Try to use JavaScript localStorage if in Skulpt environment
        import sys
        if sys.platform == 'skulpt':
            # In Skulpt, we can access JavaScript through the js module
            import js
            key = js.window.drafterLLM.loadApiKey(service)
            return str(key) if key else ""
    except (ImportError, AttributeError):
        pass
    
    # In non-Skulpt environments, return empty string
    return ""


def save_api_key(service: str, api_key: str) -> bool:
    """
    Save an API key to local storage.
    
    This function works in Skulpt environments by using JavaScript's localStorage.
    In non-Skulpt environments, it does nothing and returns False.
    
    :param service: The service name ('gpt' or 'gemini')
    :type service: str
    :param api_key: The API key to store
    :type api_key: str
    :return: True if successful, False otherwise
    :rtype: bool
    
    Example:
        >>> save_api_key('gpt', 'sk-...')
        True
    """
    try:
        import sys
        if sys.platform == 'skulpt':
            import js
            js.window.drafterLLM.saveApiKey(service, api_key)
            return True
    except (ImportError, AttributeError):
        pass
    
    return False


def clear_api_key(service: str) -> bool:
    """
    Clear a stored API key from local storage.
    
    :param service: The service name ('gpt' or 'gemini')
    :type service: str
    :return: True if successful, False otherwise
    :rtype: bool
    
    Example:
        >>> clear_api_key('gpt')
        True
    """
    try:
        import sys
        if sys.platform == 'skulpt':
            import js
            js.window.drafterLLM.clearApiKey(service)
            return True
    except (ImportError, AttributeError):
        pass
    
    return False
