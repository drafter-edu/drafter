LLM API Integration
===================

Drafter provides built-in support for integrating with popular Large Language Model (LLM) APIs,
including OpenAI's GPT and Google's Gemini. This feature is designed to work seamlessly in both
traditional Bottle deployments and Skulpt client-side environments.

Overview
--------

The LLM integration provides:

* **Simple API access**: Easy-to-use functions for calling GPT and Gemini APIs
* **Student-friendly design**: Uses only lists and dataclasses (no dictionaries required)
* **API key management**: Built-in component for capturing and storing API keys in browser local storage
* **Skulpt compatible**: Works with client-side Python execution via Skulpt

Core Components
---------------

LLMMessage
~~~~~~~~~~

Represents a single message in an LLM conversation::

    from drafter import LLMMessage
    
    # Create messages
    system_msg = LLMMessage("system", "You are a helpful assistant")
    user_msg = LLMMessage("user", "What is the capital of France?")
    
Valid roles are:

* ``"user"`` - Messages from the user
* ``"assistant"`` - Responses from the LLM
* ``"system"`` - System instructions (for GPT)

LLMResponse
~~~~~~~~~~~

Contains the response from an LLM API call::

    response = call_gpt(api_key, messages)
    if isinstance(response, LLMResponse):
        print(response.content)        # The generated text
        print(response.model)          # Model used
        print(response.finish_reason)  # Why generation stopped
        print(response.total_tokens)   # Tokens used

LLMError
~~~~~~~~

Contains error information when an API call fails::

    result = call_gpt(api_key, messages)
    if isinstance(result, LLMError):
        print(result.error_type)  # e.g., "AuthenticationError"
        print(result.message)     # Human-readable error message

ApiKeyBox Component
~~~~~~~~~~~~~~~~~~~

A specialized input component for capturing API keys::

    from drafter import ApiKeyBox
    
    # In your page
    page = Page([
        "Enter your API key:",
        ApiKeyBox("api_key", service="gpt", label="GPT API Key:"),
        Button("Submit", handle_key)
    ])

The ``ApiKeyBox`` automatically:

* Displays a password-style input field
* Saves the API key to browser local storage
* Loads previously saved keys automatically

API Functions
-------------

call_gpt()
~~~~~~~~~~

Call the OpenAI GPT API::

    from drafter import call_gpt, LLMMessage
    
    messages = [
        LLMMessage("system", "You are a helpful assistant"),
        LLMMessage("user", "Tell me a joke")
    ]
    
    result = call_gpt(
        api_key="sk-...",
        messages=messages,
        model="gpt-3.5-turbo",  # or "gpt-4"
        temperature=0.7,
        max_tokens=1000
    )

Parameters:

* ``api_key`` (str): Your OpenAI API key
* ``messages`` (List[LLMMessage]): Conversation history
* ``model`` (str): Model to use (default: "gpt-3.5-turbo")
* ``temperature`` (float): Randomness 0.0-2.0 (default: 0.7)
* ``max_tokens`` (int): Maximum response length (default: 1000)

Returns either ``LLMResponse`` on success or ``LLMError`` on failure.

call_gemini()
~~~~~~~~~~~~~

Call the Google Gemini API::

    from drafter import call_gemini, LLMMessage
    
    messages = [
        LLMMessage("user", "What is machine learning?")
    ]
    
    result = call_gemini(
        api_key="AIza...",
        messages=messages,
        model="gemini-pro",
        temperature=0.7,
        max_tokens=1000
    )

Parameters are similar to ``call_gpt()`` but use Gemini-specific model names.

Local Storage Functions
-----------------------

These functions help manage API keys in browser local storage:

save_api_key()
~~~~~~~~~~~~~~

Save an API key to local storage::

    from drafter import save_api_key
    
    save_api_key("gpt", "sk-...")
    save_api_key("gemini", "AIza...")

get_stored_api_key()
~~~~~~~~~~~~~~~~~~~~

Retrieve a stored API key::

    from drafter import get_stored_api_key
    
    api_key = get_stored_api_key("gpt")
    if api_key:
        response = call_gpt(api_key, messages)

clear_api_key()
~~~~~~~~~~~~~~~

Clear a stored API key::

    from drafter import clear_api_key
    
    clear_api_key("gpt")

Complete Example
----------------

Here's a complete chatbot example::

    from drafter import *
    from dataclasses import field
    
    @dataclass
    class ChatState:
        api_key: str = ""
        conversation: list = field(default_factory=list)
    
    @route
    def index(state: ChatState) -> Page:
        if not state.api_key:
            return Page([
                "Enter your GPT API key:",
                ApiKeyBox("api_key", "gpt"),
                Button("Start", save_key)
            ])
        
        # Show conversation
        messages = []
        for msg in state.conversation:
            if msg.role == "user":
                messages.append(f"You: {msg.content}")
            elif msg.role == "assistant":
                messages.append(f"Bot: {msg.content}")
        
        return Page(messages + [
            TextBox("message"),
            Button("Send", send_message)
        ])
    
    @route
    def save_key(state: ChatState, api_key: str) -> Page:
        state.api_key = api_key
        save_api_key("gpt", api_key)
        return index(state)
    
    @route
    def send_message(state: ChatState, message: str) -> Page:
        # Add user message
        state.conversation.append(LLMMessage("user", message))
        
        # Get response
        result = call_gpt(state.api_key, state.conversation)
        
        if isinstance(result, LLMResponse):
            state.conversation.append(
                LLMMessage("assistant", result.content)
            )
        else:
            state.conversation.append(
                LLMMessage("assistant", f"Error: {result.message}")
            )
        
        return index(state)
    
    if __name__ == "__main__":
        start_server(ChatState())

Best Practices
--------------

1. **Always check the result type**: Use ``isinstance()`` to determine if you got an ``LLMResponse`` or ``LLMError``

2. **Handle errors gracefully**: Display meaningful error messages to users when API calls fail

3. **Use local storage**: Let users save their API keys so they don't have to re-enter them

4. **Keep conversations in lists**: Use Python lists to maintain conversation history

5. **Validate API keys**: Check that API keys are provided before making calls

6. **Test with small limits**: Start with smaller ``max_tokens`` values during development

Common Error Types
------------------

* ``AuthenticationError``: Invalid or missing API key
* ``RateLimitError``: Too many requests or quota exceeded
* ``NetworkError``: Connection problems
* ``ValueError``: Invalid parameters (e.g., empty messages list)
* ``APIError``: Other API-specific errors

Getting API Keys
----------------

**OpenAI GPT**:

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key

**Google Gemini**:

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create an API key

.. warning::
   API keys should be kept secure. Never share them publicly or commit them to version control.
   The ``ApiKeyBox`` component stores keys in browser local storage, which is client-side only.

Limitations
-----------

* Requires the ``requests`` module (available in Skulpt)
* Local storage only works in browser environments
* Some advanced LLM features may not be supported
* System messages are not used in Gemini calls (they use a different format)

Troubleshooting
---------------

**"requests module not available"**
    The requests module is required. In Skulpt environments, it should be available by default.

**"Invalid API key"**
    Double-check that your API key is correct and hasn't expired.

**"Rate limit exceeded"**
    You've made too many requests. Wait a bit and try again, or upgrade your API plan.

**Empty or no response**
    Check that you're passing at least one message and that your messages are properly formatted.
