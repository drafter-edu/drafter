from drafter import *


@dataclass
class State:
    name: str
    email: str


@route
def index(state: State):
    return Page(
        state,
        [
            "Enter your information:",
            Label("Name:", for_id="name_field"),
            TextBox("name_field", state.name),
            Label("Email:", for_id="email_field"),
            TextBox("email_field", state.email, kind="email"),
            f"Name: {state.name}:)",
            f"Email: {state.email}:)",
            Button("Update", update),
        ],
    )


@route
def update(state: State, name_field: str, email_field: str):
    state.name = name_field
    state.email = email_field
    return index(state)


start_server(State("John Doe", "john@example.com"))
