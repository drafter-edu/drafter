"""
Example demonstrating dataclass-based storage API.

This approach uses the Storable mixin to add save() and load() methods
directly to dataclasses, making it object-oriented and intuitive.
"""

from drafter import *
from dataclasses import dataclass

set_website_style('none')

set_site_information(
    "Drafter Storage Team",
    "Example demonstrating dataclass-based storage API",
    "https://github.com/drafter-edu/drafter",
    "storage_dataclass.py",
    ["https://github.com/drafter-edu/drafter"]
)


@dataclass
class State(Storable):
    """
    Application state with built-in storage capabilities.
    
    The Storable mixin adds save() and load() methods to the dataclass.
    """
    username: str
    high_score: int
    games_played: int
    favorite_color: str


@route
def index(state: State) -> Page:
    """Main page showing user profile."""
    return Page(state, [
        Header("Dataclass-based Storage Demo"),
        SubHeader("User Profile"),
        Div(
            Bold("Username: "), state.username,
            style_padding="10px",
            style_background_color="#ffe0ff",
            style_border_radius="5px",
            style_margin_bottom="10px"
        ),
        Div(
            Bold("High Score: "), str(state.high_score),
            style_padding="10px",
            style_background_color="#e0ffff",
            style_border_radius="5px",
            style_margin_bottom="10px"
        ),
        Div(
            Bold("Games Played: "), str(state.games_played),
            style_padding="10px",
            style_background_color="#ffffe0",
            style_border_radius="5px",
            style_margin_bottom="10px"
        ),
        Div(
            Bold("Favorite Color: "), state.favorite_color,
            style_padding="10px",
            style_background_color=state.favorite_color.lower(),
            style_border_radius="5px",
            style_margin_bottom="10px"
        ),
        HorizontalRule(),
        Button("Edit Profile", edit_profile),
        Button("Play Game", play_game),
        HorizontalRule(),
        Div(
            Button("Save Profile", save_profile),
            Button("Load Profile", load_profile),
            Button("Reset to Default", reset_profile),
            style_padding="10px",
            style_background_color="#f0f0f0"
        ),
        Div(
            "Note: The dataclass has save() and load() methods.",
            "You can call state.save('key') to save the state.",
            style_font_size="0.9em",
            style_color="#666",
            style_margin_top="20px"
        )
    ])


@route
def edit_profile(state: State) -> Page:
    """Edit profile page."""
    return Page(state, [
        Header("Edit Profile"),
        "Username:",
        TextBox("username", state.username),
        "Favorite Color:",
        SelectBox("favorite_color", [
            "Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink"
        ], state.favorite_color),
        Button("Save Changes", update_profile),
        Button("Cancel", index)
    ])


@route
def update_profile(state: State, username: str, favorite_color: str) -> Page:
    """Update profile information."""
    state.username = username
    state.favorite_color = favorite_color
    return index(state)


@route
def play_game(state: State) -> Page:
    """Simulate playing a game."""
    import random
    score = random.randint(50, 150)
    state.games_played += 1
    
    if score > state.high_score:
        state.high_score = score
        message = "New high score!"
    else:
        message = "Better luck next time!"
    
    return Page(state, [
        Header("Game Over!"),
        Div(
            f"You scored: {score} points",
            style_font_size="2em",
            style_color="blue",
            style_text_align="center",
            style_padding="20px"
        ),
        Div(
            message,
            style_font_size="1.5em",
            style_text_align="center",
            style_padding="10px"
        ),
        Div(
            f"High Score: {state.high_score}",
            style_padding="10px",
            style_background_color="#ffffcc"
        ),
        Div(
            f"Games Played: {state.games_played}",
            style_padding="10px",
            style_background_color="#ccffff"
        ),
        HorizontalRule(),
        Button("Play Again", play_game),
        Button("Back to Profile", index)
    ])


@route
def save_profile(state: State) -> Page:
    """Save the profile using the dataclass save() method."""
    # Using the Storable mixin's save() method
    state.save("user_profile")
    
    return Page(state, [
        Header("Profile Saved!"),
        "Your profile has been saved successfully.",
        Div(
            "Username: ", Bold(state.username),
            style_padding="10px",
            style_background_color="#d0ffd0"
        ),
        Div(
            "High Score: ", Bold(str(state.high_score)),
            style_padding="10px",
            style_background_color="#c0ffc0"
        ),
        Div(
            "Games Played: ", Bold(str(state.games_played)),
            style_padding="10px",
            style_background_color="#b0ffb0"
        ),
        Button("Back to Profile", index)
    ])


@route
def load_profile(state: State) -> Page:
    """Load the profile using the dataclass load() class method."""
    # Using the Storable mixin's load() class method
    default_state = State("Guest", 0, 0, "Blue")
    loaded_state = State.load("user_profile", default_state)
    
    return Page(loaded_state, [
        Header("Profile Loaded!"),
        "Your profile has been loaded from storage.",
        Div(
            "Username: ", Bold(loaded_state.username),
            style_padding="10px",
            style_background_color="#d0d0ff"
        ),
        Div(
            "High Score: ", Bold(str(loaded_state.high_score)),
            style_padding="10px",
            style_background_color="#c0c0ff"
        ),
        Div(
            "Games Played: ", Bold(str(loaded_state.games_played)),
            style_padding="10px",
            style_background_color="#b0b0ff"
        ),
        Button("Back to Profile", index)
    ])


@route
def reset_profile(state: State) -> Page:
    """Reset to default profile."""
    default_state = State("New Player", 0, 0, "Blue")
    return Page(default_state, [
        Header("Profile Reset!"),
        "Your profile has been reset to default values.",
        Button("Back to Profile", index)
    ])


# Start with a default profile
start_server(State("Player One", 100, 5, "Blue"))
