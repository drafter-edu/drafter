from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Basic TextBox:",
        TextBox("user_input"),
        Button("Submit", process_input)
    ])

@route 
def process_input(state: str, user_input: str) -> Page:
    return Page(state, [
        f"You entered: {user_input}",
        Link("Go back", index)
    ])

start_server("")