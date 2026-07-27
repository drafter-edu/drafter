LLM API Integration
===================

Drafter provides built-in support for integrating with popular Large Language Model (LLM) APIs,
including OpenAI's GPT and Google's Gemini. This feature is designed to work seamlessly in both
traditional Bottle deployments and Skulpt client-side environments.

.. note::
   LLM functions must be explicitly imported from ``drafter.llm``. Only the ``ApiKeyBox`` 
   component is available through the standard Drafter import.

Overview
--------

The LLM integration provides:

* **Simple API access**: Easy-to-use functions for calling GPT and Gemini APIs
* **Student-friendly design**: Uses only lists and dataclasses (no dictionaries required)
* **Structured outputs**: Generate responses in specific formats using dataclasses
* **API key management**: Built-in component for capturing and storing API keys in browser local storage
* **Skulpt compatible**: Works with client-side Python execution via Skulpt

Importing LLM Functions
------------------------

LLM functions require explicit import::

    from drafter import ApiKeyBox  # Available through standard import
    from drafter.llm import LLMMessage, call_gpt, call_gemini
    from drafter.llm import call_gpt_structured, call_gemini_structured

Core Components
---------------

LLMMessage
~~~~~~~~~~

Represents a single message in an LLM conversation::

    from drafter.llm import LLMMessage
    
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

    from drafter.llm import call_gpt
    
    response = call_gpt(api_key, messages)
    if isinstance(response, LLMResponse):
        print(response.content)        # The generated text
        print(response.model)          # Model used
        print(response.finish_reason)  # Why generation stopped
        print(response.total_tokens)   # Tokens used

LLMError
~~~~~~~~

Contains error information when an API call fails::

    from drafter.llm import call_gpt, LLMError
    
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

    from drafter.llm import call_gpt, LLMMessage
    
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

Structured Output Functions
----------------------------

For applications that need responses in a specific format, use the structured output functions.
These functions use dataclasses to define the expected response structure and automatically
parse the JSON response into dataclass instances.

Defining Response Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a dataclass with a Google-style docstring that includes an ``Attributes:`` section::

    from dataclasses import dataclass
    from typing import List
    
    @dataclass
    class RecipeInfo:
        """Recipe information.
        
        Attributes:
            name: The name of the recipe
            prep_time: Preparation time in minutes
            ingredients: List of ingredients needed
            steps: List of preparation steps
        """
        name: str
        prep_time: int
        ingredients: List[str]
        steps: List[str]

**Important**: The docstring must include an ``Attributes:`` section with descriptions for
each field. This helps the LLM understand what information to provide.

call_gpt_structured()
~~~~~~~~~~~~~~~~~~~~~

Call GPT with a structured output format::

    from drafter.llm import call_gpt_structured, LLMMessage
    
    messages = [
        LLMMessage("user", "Give me a simple pasta recipe")
    ]
    
    result = call_gpt_structured(
        api_key="sk-...",
        messages=messages,
        response_format=RecipeInfo,
        model="gpt-4o-2024-08-06",  # Structured output requires this model or newer
        temperature=0.7,
        max_tokens=1000
    )
    
    if isinstance(result, RecipeInfo):
        print(f"Recipe: {result.name}")
        print(f"Time: {result.prep_time} minutes")
        for ingredient in result.ingredients:
            print(f"  - {ingredient}")

Parameters:

* ``api_key`` (str): Your OpenAI API key
* ``messages`` (List[LLMMessage]): Conversation history
* ``response_format`` (Type): A dataclass type defining the response structure
* ``model`` (str): Model to use (default: "gpt-4o-2024-08-06" - structured output requires GPT-4o or newer)
* ``temperature`` (float): Randomness 0.0-2.0 (default: 0.7)
* ``max_tokens`` (int): Maximum response length (default: 1000)

Returns an instance of ``response_format`` on success or ``LLMError`` on failure.

call_gemini_structured()
~~~~~~~~~~~~~~~~~~~~~~~~

Call Gemini with a structured output format::

    from drafter.llm import call_gemini_structured, LLMMessage
    
    @dataclass
    class MovieReview:
        """Movie review information.
        
        Attributes:
            title: The movie title
            rating: Rating from 1 to 10
            pros: List of positive aspects
            cons: List of negative aspects
            summary: Brief review summary
        """
        title: str
        rating: int
        pros: List[str]
        cons: List[str]
        summary: str
    
    messages = [
        LLMMessage("user", "Review the movie Inception")
    ]
    
    result = call_gemini_structured(
        api_key="AIza...",
        messages=messages,
        response_format=MovieReview,
        model="gemini-1.5-pro"
    )
    
    if isinstance(result, MovieReview):
        print(f"{result.title}: {result.rating}/10")
        print(result.summary)

Nested Dataclasses
~~~~~~~~~~~~~~~~~~

You can nest dataclasses for complex structures::

    @dataclass
    class Author:
        """Author information.
        
        Attributes:
            name: Author's full name
            country: Author's country of origin
        """
        name: str
        country: str
    
    @dataclass
    class Book:
        """Book information.
        
        Attributes:
            title: Book title
            author: Book author information
            year: Publication year
            genres: List of genres
        """
        title: str
        author: Author
        year: int
        genres: List[str]
    
    messages = [LLMMessage("user", "Tell me about The Great Gatsby")]
    result = call_gpt_structured(api_key, messages, Book)

Local Storage Functions
-----------------------

These functions help manage API keys in browser local storage:

save_api_key()
~~~~~~~~~~~~~~

Save an API key to local storage::

    from drafter.llm import save_api_key
    
    save_api_key("gpt", "sk-...")
    save_api_key("gemini", "AIza...")

get_stored_api_key()
~~~~~~~~~~~~~~~~~~~~

Retrieve a stored API key::

    from drafter.llm import get_stored_api_key
    
    api_key = get_stored_api_key("gpt")
    if api_key:
        response = call_gpt(api_key, messages)

clear_api_key()
~~~~~~~~~~~~~~~

Clear a stored API key::

    from drafter.llm import clear_api_key
    
    clear_api_key("gpt")

Complete Example
----------------

Here's a complete chatbot example::

    from drafter import *
    from drafter.llm import LLMMessage, LLMResponse, call_gpt, save_api_key
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
