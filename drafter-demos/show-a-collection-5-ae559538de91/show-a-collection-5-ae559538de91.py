from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pets: list[str]
    search_text: str


def matching_pets(pets: list[str], search_text: str) -> list[str]:
    matches = []
    for pet in pets:
        if search_text.lower() in pet.lower():
            matches.append(pet)
    return matches


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet finder"),
        "Show pets whose description contains:",
        TextBox("search_text", state.search_text),
        Button("Search", "search"),
        "\n",
        BulletedList(matching_pets(state.pets, state.search_text))
    ])


@route
def search(state: State, search_text: str) -> Page:
    state.search_text = search_text
    return index(state)


assert_equal(matching_pets(["Ada the corgi", "Captain the grey cat"], "CAT"),
             ["Captain the grey cat"])
assert_equal(matching_pets(["Ada the corgi", "Captain the grey cat"], ""),
             ["Ada the corgi", "Captain the grey cat"])

start_server(State([
    "Ada the corgi",
    "Babbage the small black mutt",
    "Captain the grey cat",
    "Domino the black cat"
], ""))
