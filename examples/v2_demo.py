"""
Example demonstrating new V2 infrastructure features.

This example shows how to use:
- The new Site class
- New ResponsePayload types (Fragment, Redirect, Progress, etc.)
- Channels for additional communication
"""

from drafter import (
    route,
    start_server,
    Page,
    Fragment,
    Redirect,
    Progress,
    Site,
    Channels,
    Button,
    TextBox,
)


# Create a site with metadata
site = Site(
    title="V2 Demo Application",
    description="Demonstration of Drafter V2 features",
    author="Drafter Team",
    language="en",
)


@route
def index(state: dict) -> Page:
    """
    Main index page showing links to different V2 features.
    """
    if state is None:
        state = {"counter": 0}
    
    return Page(
        state,
        [
            "Welcome to Drafter V2 Demo!",
            f"Counter: {state['counter']}",
            Button("Increment Counter", increment),
            Button("Show Progress", show_progress),
            Button("Test Fragment", test_fragment),
        ],
    )


@route
def increment(state: dict) -> Page:
    """
    Increments the counter and returns to index.
    """
    state["counter"] = state.get("counter", 0) + 1
    return index(state)


@route
def show_progress(state: dict) -> Progress:
    """
    Returns a Progress payload.
    """
    return Progress(
        message="Loading data...",
        percentage=75.0,
    )


@route
def test_fragment(state: dict) -> Fragment:
    """
    Returns a Fragment payload.
    """
    return Fragment(
        content="<p>This is a fragment of HTML content.</p>",
        target_id="content-area",
    )


# Initialize with default state
start_server(initial_state={"counter": 0})
