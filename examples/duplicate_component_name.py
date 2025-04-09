from drafter import *
from dataclasses import dataclass
import io
import base64

@dataclass
class State:
    choice: str

@route
def index(state: State) -> Page:
    """
    introduces the user to the website,
    gives them the choice whether or not they want to
    encode or decode.
    """
    return Page(state, [
        "Hello!",
        "Would you like to encode or decode?",
        SelectBox('choice', ['Encode', 'Decode', 'Gallery']),
        Button("choice", choice_changer)
        ])

@route
def choice_changer(state : State, choice:str) -> Page:
    """
    checks if the choice is either:
    encode: it's true, and goes to encode
    decode: it's false, and goes to decode
    """
    return Page(state, [
        "You chose to " + choice.lower() + "!",
    ])

start_server(State("Encode"))