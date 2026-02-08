"""Example demonstrating event handlers on components."""

from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    """State for tracking interactions."""
    text: str
    last_event: str
    event_count: int


@route
def index(state: State) -> Page:
    """Main page with various event handlers."""
    return Page(state, [
        Header("Event Handlers Demo"),
        "This demo shows how to use event handlers on components.",
        HorizontalRule(),
        
        Header("Text Box with Events", level=2),
        "Type in the box below. Events will be triggered:",
        TextBox("text", state.text, 
                on_input=handle_input,
                on_change=handle_change,
                on_focus=handle_focus,
                on_blur=handle_blur),
        
        HorizontalRule(),
        
        Header("Current State", level=2),
        Output("status", [
            f"Text: {state.text or '(empty)'}",
            LineBreak(),
            f"Last event: {state.last_event}",
            LineBreak(),
            f"Event count: {state.event_count}",
        ]),
        
        HorizontalRule(),
        Button("Reset", reset_state),
    ])


@route
def handle_input(state: State, text: str) -> Fragment:
    """Handle input event (fires on every keystroke)."""
    state.text = text
    state.last_event = "input"
    state.event_count += 1
    return Fragment(
        state,
        [
            f"Text: {text or '(empty)'}",
            LineBreak(),
            f"Last event: input",
            LineBreak(),
            f"Event count: {state.event_count}",
        ],
        target="#status"
    )


@route
def handle_change(state: State, text: str) -> Fragment:
    """Handle change event (fires when value changes and loses focus)."""
    state.text = text
    state.last_event = "change"
    state.event_count += 1
    return Fragment(
        state,
        [
            f"Text: {text or '(empty)'}",
            LineBreak(),
            f"Last event: change",
            LineBreak(),
            f"Event count: {state.event_count}",
        ],
        target="#status"
    )


@route
def handle_focus(state: State) -> Fragment:
    """Handle focus event."""
    state.last_event = "focus"
    state.event_count += 1
    return Fragment(
        state,
        [
            f"Text: {state.text or '(empty)'}",
            LineBreak(),
            f"Last event: focus",
            LineBreak(),
            f"Event count: {state.event_count}",
        ],
        target="#status"
    )


@route
def handle_blur(state: State, text: str) -> Fragment:
    """Handle blur event (fires when element loses focus)."""
    state.text = text
    state.last_event = "blur"
    state.event_count += 1
    return Fragment(
        state,
        [
            f"Text: {text or '(empty)'}",
            LineBreak(),
            f"Last event: blur",
            LineBreak(),
            f"Event count: {state.event_count}",
        ],
        target="#status"
    )


@route
def reset_state(state: State) -> Page:
    """Reset the state to initial values."""
    state.text = ""
    state.last_event = "none"
    state.event_count = 0
    return index(state)


start_server(State(text="", last_event="none", event_count=0))
