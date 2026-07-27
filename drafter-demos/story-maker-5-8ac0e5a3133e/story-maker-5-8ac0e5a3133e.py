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
        Button("Tell it differently", "another_story"),
        Button("Change the words", "index")
    ])


@route
def another_story(state: State) -> Page:
    return Page(state, [
        "Deep in " + state.place + ", something glittered.",
        "It was " + state.thing + ", lost for a hundred years.",
        "Only " + state.hero + " knew what it could do.\n",
        Button("Change the words", "index")
    ])


assert_has(story(State("", "", ""), "Ada", "the moon", "a spoon"), "Ada traveled to the moon")
assert_state(story(State("", "", ""), "Ada", "the moon", "a spoon"), State("Ada", "the moon", "a spoon"))
assert_has(another_story(State("Ada", "the moon", "a spoon")), "Deep in the moon")

start_server(State("Ada", "the library", "a tiny robot"))
