from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signatures: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Petition for More Nap Time"),
        str(len(state.signatures)) + " signatures so far.\n",
        "Your name:",
        TextBox("name"),
        "\n",
        Button("Sign", "sign")
    ])


@route
def sign(state: State, name: str) -> Redirect:
    state.signatures.append(name)
    return Redirect("thanks", state, signer=name)


@route
def thanks(state: State, signer: str) -> Page:
    return Page(state, [
        Header("Thank you, " + signer + "!"),
        "Your dedication to napping is noted.\n",
        Link("Back to the petition", "index")
    ])


start_server(State([]))
