from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    username: str
    password: str

@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Welcome to my site!"),
        "You are not logged in.",
        Button("Log in", ask_login)
    ])

@route
def index (state: State) -> Page:
    return Page(state, [
        "What should I call you?",
        TextBox("new_name", state.username),
        Button("Save", save_changes),
        "What would you like sugggestions for?",
        "Password?",
        CheckBox("password", False)
        ])

@route
def save_changes(state: State, new_name: str) -> Page:
    state.username = new_name
    return index(state)


start_server(State("", ""))