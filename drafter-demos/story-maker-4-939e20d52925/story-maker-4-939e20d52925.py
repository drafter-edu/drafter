from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str
    place: str
    thing: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "A hero:",
        TextBox("hero", state.hero),
        "\nA place:",
        TextBox("place", state.place),
        "\nAn object:",
        TextBox("thing", state.thing),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str, place: str, thing: str) -> Page:
    state.hero = hero
    state.place = place
    state.thing = thing
    return Page(state, [
        "Long ago, " + state.hero + " traveled to " + state.place + ".",
        "Nobody there had ever seen " + state.thing + " before.",
        "By sunset, " + state.hero + " was famous.\n",
        Button("Change the words", "index")
    ])


start_server(State("Ada", "the library", "a tiny robot"))
