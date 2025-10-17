"""
LLM API Integration for Drafter

This module provides simplified access to popular LLM APIs like GPT and Gemini.
It handles API key management through local storage and provides a student-friendly
interface using only lists and dataclasses.
"""

from dataclasses import dataclass
from typing import List, Optional, Any
import json

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


def call_gemini(api_key: str, messages: List[LLMMessage], model: str = "gemini-pro",
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
