"""
Example demonstrating function-based storage API for saving and loading state.

This approach uses simple functions like save_state() and load_state(),
similar to traditional file handling in Python.
"""

from drafter import *
from dataclasses import dataclass

set_website_style('none')

set_site_information(
    "Drafter Storage Team",
    "Example demonstrating function-based storage API",
    "https://github.com/drafter-edu/drafter",
    "storage_functions.py",
    ["https://github.com/drafter-edu/drafter"]
)


@dataclass
class State:
    """Application state containing a message and counter."""
    message: str
    count: int


@route
def index(state: State) -> Page:
    """Main page showing the current state and save/load options."""
    return Page(state, [
        Header("Function-based Storage Demo"),
        Div(
            "Current Message: ", Bold(state.message),
            style_padding="10px",
            style_background_color="#f0f0f0"
        ),
        Div(
            "Counter: ", Bold(str(state.count)),
            style_padding="10px",
            style_background_color="#e0e0e0"
        ),
        HorizontalRule(),
        "Change the message:",
        TextBox("new_message", state.message),
        Button("Update Message", update_message),
        HorizontalRule(),
        Button("Increment Counter", increment_counter),
        Button("Reset Counter", reset_counter),
        HorizontalRule(),
        Div(
            Button("Save State", save_current_state),
            Button("Load State", load_saved_state),
            Button("Delete Saved State", delete_saved_state),
            style_padding="10px",
            style_background_color="#ffe0e0"
        ),
        Div(
            "Note: When running locally, state is saved to ~/.drafter_storage/",
            "When deployed, state is saved to browser localStorage.",
            style_font_size="0.9em",
            style_color="#666",
            style_margin_top="20px"
        )
    ])


@route
def update_message(state: State, new_message: str) -> Page:
    """Update the message in the state."""
    state.message = new_message
    return index(state)


@route
def increment_counter(state: State) -> Page:
    """Increment the counter."""
    state.count += 1
    return index(state)


@route
def reset_counter(state: State) -> Page:
    """Reset the counter to zero."""
    state.count = 0
    return index(state)


@route
def save_current_state(state: State) -> Page:
    """Save the current state to storage."""
    save_state("my_app_state", state)
    return Page(state, [
        Header("State Saved!"),
        "Your state has been saved successfully.",
        Div(
            "Saved message: ", Bold(state.message),
            style_padding="10px",
            style_background_color="#d0ffd0"
        ),
        Div(
            "Saved counter: ", Bold(str(state.count)),
            style_padding="10px",
            style_background_color="#c0ffc0"
        ),
        Button("Back to Home", index)
    ])


@route
def load_saved_state(state: State) -> Page:
    """Load the saved state from storage."""
    loaded = load_state("my_app_state", State, State("No saved state", 0))
    return Page(loaded, [
        Header("State Loaded!"),
        "Your state has been loaded from storage.",
        Div(
            "Loaded message: ", Bold(loaded.message),
            style_padding="10px",
            style_background_color="#d0d0ff"
        ),
        Div(
            "Loaded counter: ", Bold(str(loaded.count)),
            style_padding="10px",
            style_background_color="#c0c0ff"
        ),
        Button("Back to Home", index)
    ])


@route
def delete_saved_state(state: State) -> Page:
    """Delete the saved state from storage."""
    delete_state("my_app_state")
    return Page(state, [
        Header("State Deleted!"),
        "Your saved state has been deleted.",
        Button("Back to Home", index)
    ])


# Start the server with initial state
start_server(State("Welcome to Drafter Storage!", 0))
