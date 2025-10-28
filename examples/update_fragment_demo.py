"""
Example demonstrating Update and Fragment return types in Drafter.

This example shows how to use:
1. Update - to update state without changing the page
2. Fragment - to update a specific part of the page without full refresh

Note: This example demonstrates the server-side API.
Full client-side JavaScript support for event handlers is planned for future implementation.
"""

from drafter import *
from dataclasses import dataclass


@dataclass
class CounterState:
    """State tracking multiple counters"""
    main_counter: int = 0
    background_counter: int = 0
    clicks: int = 0


@route
def index(state: CounterState) -> Page:
    """Main page showing counters and buttons"""
    return Page(state, [
        Header("Update and Fragment Demo"),
        
        "This demo shows the new Update and Fragment return types.",
        
        "Main Counter (updates visible on page):",
        Div(f"Count: {state.main_counter}", id="counter-display"),
        Button("Increment Visible Counter", increment_visible_counter),
        
        LineBreak(),
        
        "Background Counter (updates state only):",
        f"Background count: {state.background_counter}",
        Button("Increment Background Counter", increment_background_counter),
        
        LineBreak(),
        
        f"Total button clicks: {state.clicks}",
        Button("Refresh Page", index),
        
        LineBreak(),
        LineBreak(),
        
        "Technical Notes:",
        NumberedList([
            "Update() returns update the state without re-rendering the page",
            "Fragment() returns update a specific element on the page",
            "Full AJAX/event handler support requires client-side JavaScript (planned)",
            "Click 'Refresh Page' to see the background counter updates"
        ])
    ])


@route
def increment_visible_counter(state: CounterState) -> Fragment:
    """
    Increment the main counter and return a Fragment to update only the display.
    
    This demonstrates how Fragment can update just part of the page.
    In a future version with JavaScript support, this would update the #counter-display
    element without refreshing the entire page.
    """
    state.main_counter += 1
    state.clicks += 1
    
    return Fragment(
        state=state,
        target="#counter-display",
        content=[f"Count: {state.main_counter}"]
    )


@route
def increment_background_counter(state: CounterState) -> Update:
    """
    Increment the background counter without updating the page display.
    
    This demonstrates how Update can modify state silently.
    The change won't be visible until the page is refreshed.
    """
    state.background_counter += 1
    state.clicks += 1
    
    return Update(state)


if __name__ == '__main__':
    # Start the server with initial state
    start_server(CounterState())
