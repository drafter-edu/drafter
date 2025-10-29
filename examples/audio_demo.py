"""
Example demonstrating audio channel functionality.

This example shows how to use channels to control background audio
that persists across page navigation.
"""

from drafter import (
    route,
    start_server,
    Page,
    Button,
    Channels,
)


@route
def index(state: dict) -> Page:
    """
    Main page with audio control buttons.
    """
    if state is None:
        state = {"playing": False}
    
    status = "playing" if state.get("playing") else "stopped"
    
    return Page(
        state,
        [
            f"Audio Status: {status}",
            Button("Play Music", play_audio),
            Button("Pause Music", pause_audio),
            Button("Stop Music", stop_audio),
            Button("Navigate to Page 2", page2),
        ],
    )


@route
def play_audio(state: dict) -> Page:
    """
    Start playing background audio using channels.
    """
    state["playing"] = True
    
    page = Page(
        state,
        [
            "Music is now playing!",
            Button("Back to Index", index),
        ],
    )
    
    # This would be used if we could attach channels to responses
    # For now, this is a demonstration of the API
    # In the future, the Response object would carry these channels
    
    return page


@route
def pause_audio(state: dict) -> Page:
    """
    Pause the background audio.
    """
    state["playing"] = False
    
    return Page(
        state,
        [
            "Music paused.",
            Button("Back to Index", index),
        ],
    )


@route
def stop_audio(state: dict) -> Page:
    """
    Stop the background audio.
    """
    state["playing"] = False
    
    return Page(
        state,
        [
            "Music stopped.",
            Button("Back to Index", index),
        ],
    )


@route
def page2(state: dict) -> Page:
    """
    Another page - audio should continue playing.
    """
    return Page(
        state,
        [
            "This is page 2. Audio should continue playing in the background.",
            Button("Back to Index", index),
        ],
    )


# Initialize with default state
start_server(initial_state={"playing": False})
