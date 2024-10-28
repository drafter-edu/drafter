from drafter import *
from bakery import assert_equal
from dataclasses import dataclass


@dataclass
class State:
    """ The state of the adventure game. """


@route
def index(state: State) -> Page:
    """ The main page of the adventure game, letting the player enter their name. """


@route
def begin(state: State, name: str) -> Page:
    """ Updates the state with the new player name, then redirects to small_field. """


@route
def small_field(state: State) -> Page:
    """ The page for the small field location. """


@route
def cave(state: State) -> Page:
    """ The page for the cave location, which has a locked door. """


@route
def woods(state: State) -> Page:
    """ The page for the woods location, which will have a key if the player has not yet picked it up. """


@route
def take_key(state: State) -> Page:
    """ Updates the state to indicate that the player has picked up the key, then redirects to the woods. """


@route
def ending(state: State) -> Page:
    """ The victory screen """


assert_equal(
    ending(State(has_key=True, name="Ada")),
    Page(
        state=State(has_key=True, name="Ada"),
        content=[
            "You unlock the door.",
            "You find a treasure chest.",
            "You win!",
            Image(url="victory.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    cave(State(has_key=True, name="Ada")),
    Page(
        state=State(has_key=True, name="Ada"),
        content=[
            "You enter the cave.",
            "You see a locked door.",
            Button(text="Unlock door", url="/ending"),
            Button(text="Leave", url="/small_field"),
            Image(url="cave.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    small_field(State(has_key=True, name="Ada")),
    Page(
        state=State(has_key=True, name="Ada"),
        content=[
            "You are Ada.",
            "You are in a small field.",
            "You see paths to the woods and a cave.",
            Button(text="Cave", url="/cave"),
            Button(text="Woods", url="/woods"),
            Image(url="field.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    take_key(State(has_key=False, name="Ada")),
    Page(
        state=State(has_key=True, name="Ada"),
        content=[
            "You are in the woods.",
            Button(text="Leave", url="/small_field"),
            Image(url="woods.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    woods(State(has_key=False, name="Ada")),
    Page(
        state=State(has_key=False, name="Ada"),
        content=[
            "You are in the woods.",
            "You see a key on the ground.",
            Button(text="Take key", url="/take_key"),
            Button(text="Leave", url="/small_field"),
            Image(url="woods.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    small_field(State(has_key=False, name="Ada")),
    Page(
        state=State(has_key=False, name="Ada"),
        content=[
            "You are Ada.",
            "You are in a small field.",
            "You see paths to the woods and a cave.",
            Button(text="Cave", url="/cave"),
            Button(text="Woods", url="/woods"),
            Image(url="field.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    cave(State(has_key=False, name="Ada")),
    Page(
        state=State(has_key=False, name="Ada"),
        content=[
            "You enter the cave.",
            "You see a locked door.",
            Button(text="Leave", url="/small_field"),
            Image(url="cave.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    begin(State(has_key=False, name=""), "Ada"),
    Page(
        state=State(has_key=False, name="Ada"),
        content=[
            "You are Ada.",
            "You are in a small field.",
            "You see paths to the woods and a cave.",
            Button(text="Cave", url="/cave"),
            Button(text="Woods", url="/woods"),
            Image(url="field.png", width=None, height=None),
        ],
    ),
)

assert_equal(
    index(State(has_key=False, name="")),
    Page(
        state=State(has_key=False, name=""),
        content=[
            "Welcome to the adventure! What is your name?",
            TextBox(name="name", kind="text", default_value="Adventurer"),
            Button(text="Begin", url="/begin"),
        ],
    ),
)

start_server(State(False, ""))
