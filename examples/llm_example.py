"""
Example: Using LLM APIs with Drafter

This example demonstrates how to integrate GPT or Gemini API into a Drafter application.
The API key is stored in the browser's local storage for convenience.
"""

from drafter import *
from drafter.llm import LLMMessage, LLMResponse, call_gpt, call_gemini, save_api_key


@dataclass
class State:
    """
    The state of our chatbot application.
    
    :param api_key: The user's API key for the LLM service
    :type api_key: str
    :param service: Which LLM service to use ('gpt' or 'gemini')
    :type service: str
    :param conversation: List of messages in the conversation
    :type conversation: List[LLMMessage]
    """
    api_key: str
    service: str
    conversation: list[LLMMessage]


@route
def index(state: State) -> Page:
    """
    Main page of the chatbot application.
    Shows API key setup if not configured, otherwise shows the chat interface.
    """
    if not state.api_key:
        return Page(state, [
            "Welcome to the LLM Chatbot!",
            "To get started, you need to enter your API key.",
            "",
            "Choose your LLM service:",
            SelectBox("service", ["gemini", "gpt"], state.service),
            "",
            ApiKeyBox("api_key", state.service, "API Key:"),
            "",
            Button("Save and Start Chatting", "chat"),
            "",
            "Note: Your API key is stored locally in your browser and never sent to our servers."
        ])

    return show_chat(state)


def show_chat(state: State) -> Page:
    """Display the chat interface with conversation history."""
    content = [
        f"Chatbot using {state.service.upper()}",
        "---"
    ]

    # Show conversation history
    if state.conversation:
        for msg in state.conversation:
            if msg.role == "user":
                content.append(f"You: {msg.content}")
            elif msg.role == "assistant":
                content.append(f"Bot: {msg.content}")
        content.append("---")

    # Input for new message
    content.extend([
        "Your message:",
        TextArea("user_message", "", rows=3, cols=50),
        "",
        Button("Send", send_message),
        " ",
        Button("Clear Conversation", clear_conversation),
        " ",
        Button("Change API Key", reset_api_key)
    ])

    return Page(state, content)


@route
def chat(state: State, api_key: str, service: str) -> Page:
    """Save the API key and service selection."""
    state.api_key = api_key
    state.service = service

    # Save to local storage
    save_api_key(service, api_key)

    return show_chat(state)


@route
def send_message(state: State, user_message: str) -> Page:
    """Send a message to the LLM and get a response."""
    if not user_message.strip():
        return show_chat(state)

    # Add user message to conversation
    user_msg = LLMMessage("user", user_message)
    state.conversation.append(user_msg)

    # Call the appropriate LLM API
    if state.service == "gpt":
        result = call_gpt(state.api_key, state.conversation)
    else:  # gemini
        result = call_gemini(state.api_key, state.conversation)

    # Handle the result
    if isinstance(result, LLMResponse):
        # Success! Add the response to conversation
        assistant_msg = LLMMessage("assistant", result.content)
        state.conversation.append(assistant_msg)
    else:
        # Error occurred
        error_msg = LLMMessage("assistant", f"Error: {result.message}")
        state.conversation.append(error_msg)

    print(state)

    return show_chat(state)


@route
def clear_conversation(state: State) -> Page:
    """Clear the conversation history."""
    state.conversation = []
    return show_chat(state)


@route
def reset_api_key(state: State) -> Page:
    """Reset the API key to allow changing it."""
    state.api_key = ""
    state.conversation = []
    return index(state)


start_server(State("", "gemini", []), cdn_skulpt_drafter="http://localhost:8000/skulpt-drafter.js")
