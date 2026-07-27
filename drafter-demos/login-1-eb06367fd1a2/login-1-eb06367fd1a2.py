from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    username: str
    logged_in: bool


def check_password(username: str, password: str) -> bool:
    # A stand-in, not security: every visitor can read this code.
    if username == "ada" and password == "lovelace":
        return True
    if username == "admin" and password == "password":
        return True
    return False


@route
def index(state: State) -> Page:
    if state.logged_in:
        body = [
            Header("The Clubhouse"),
            "Welcome back, " + state.username + "!\n",
            Button("Log out", "do_logout")
        ]
    else:
        body = [
            Header("The Clubhouse"),
            "You are not logged in.\n",
            Button("Log in", "ask_login")
        ]
    return Page(state, body)


@route
def ask_login(state: State) -> Page:
    return Page(state, [
        Header("Log in"),
        "Username:",
        TextBox("username", state.username),
        "\nPassword:",
        TextBox("password", "", "password"),
        "\n",
        Button("Log in", "finish_login"),
        Button("Go back", "index")
    ])


@route
def finish_login(state: State, username: str, password: str) -> Page:
    state.username = username
    if check_password(username, password):
        state.logged_in = True
        return index(state)
    return Page(state, [
        "Incorrect username or password.\n",
        Button("Try again", "ask_login"),
        Button("Go back", "index")
    ])


@route
def do_logout(state: State) -> Page:
    state.logged_in = False
    return index(state)


assert_state(finish_login(State("", False), "ada", "lovelace"),
             State("ada", True))
assert_has(finish_login(State("", False), "ada", "wrong"),
           "Incorrect username or password.")
assert_state(do_logout(State("ada", True)), State("ada", False))

start_server(State("", False))
