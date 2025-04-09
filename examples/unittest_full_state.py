import unittest
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    message: str
    likes_dogs: bool

@route
def index(state: State) -> Page:
    return Page(state, [
        "The message is:",
        state.message,
        Button("Change the Message", change_message),
        "Are you okay seeing pictures of dogs?",
        CheckBox("are_dogs_okay", state.likes_dogs),
        "You can use the button below to go see a picture",
        Button("View the picture", view_picture)
    ])

@route
def change_message(state: State) -> Page:
    state.message = "The new message!"
    return Page(state, [
        "Now the message is",
        state.message,
        "Would you like to change the message?",
        TextBox("new_message", state.message),
        Button("Save", set_the_message)
    ])

@route
def set_the_message(state: State, new_message: str) -> Page:
    state.message = new_message
    return index(state)

@route
def view_picture(state: State, are_dogs_okay: bool) -> Page:
    if are_dogs_okay:
        url = "https://placedog.net/500/280?random"
    else:
        url = "https://placekitten.com/500/280?random"
    state.likes_dogs = are_dogs_okay
    return Page(state, [
        Image(url),
        Button("Return to the main page", index)
    ])


class TestFullState(unittest.TestCase):
    def test_full_state(self):
        self.assertEqual(
            index(State("My message", True)),
            Page(State("My message", True), [
                "The message is:",
                "My message",
                Button("Change the Message", change_message),
                "Are you okay seeing pictures of dogs?",
                CheckBox("are_dogs_okay", True),
                "You can use the button below to go see a picture",
                Button("View the picture", view_picture)
            ])
        )

    def test_set_the_message(self):
        self.assertEqual(
            set_the_message(State("My message", True), "New message"),
            Page(State("New message", True), [
                "The message is:",
                "New message",
                Button("Change the Message", change_message),
                "Are you okay seeing pictures of dogs?",
                CheckBox("are_dogs_okay", True),
                "You can use the button below to go see a picture",
                Button("View the picture", view_picture)
            ])
        )

if __name__ == "__main__":
    unittest.main()

start_server(State("The original message", True))