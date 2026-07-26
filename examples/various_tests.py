import random
from dataclasses import dataclass, field

from drafter import *


@dataclass
class State:
    past_words: list


class CannotBeDeepCopied:
    def __deepcopy__(self, memo):
        raise RuntimeError("This object cannot be deep copied.")


@dataclass
class SimpleTree:
    value: str
    children: list["SimpleTree"] = field(default_factory=list)


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "Welcome!",
            Link("Check out this external site.", "https://example.com"),
            "\n",
            Link("Check out this page that has duplicate names.", "/duped_names"),
            "\n",
            Link("Add a number to the list.", "/add_number"),
            "\n",
            Link("Add something malformed to the list", "/add_malformed"),
            "\n",
            Link("Add a tree to the list", "/add_tree"),
            "\n",
            Link("Add a self-referential tree to the list", "/add_self_ref_tree"),
            "\n",
            "The List:",
            BulletedList([str(word) for word in state.past_words]),
        ],
    )


@route
def duped_names(state: State) -> Page:
    return Page(
        state,
        [
            "Oh no this page won't work.",
            "It has duplicate names in the form.",
            TextBox("name", "First Name"),
            TextBox("name", "Last Name"),
            Link("Go back to the index page.", "/"),
        ],
    )


@route
def add_number(state: State) -> Page:
    number = random.randint(1, 100)
    state.past_words.append(number)
    return Page(
        state,
        [
            f"Added {number} to the list.",
            Link("Go back to the index page.", "/"),
        ],
    )


@route
def add_malformed(state: State) -> Page:
    state.past_words.append(CannotBeDeepCopied())
    return Page(
        state,
        [
            "Added a malformed object to the list.",
            Link("Go back to the index page.", "/"),
        ],
    )


@route
def add_tree(state: State) -> Page:
    tree = SimpleTree("root", [SimpleTree("child1"), SimpleTree("child2")])
    state.past_words.append(tree)
    return Page(
        state,
        [
            "Added a tree to the list.",
            Link("Go back to the index page.", "/"),
        ],
    )


@route
def add_self_ref_tree(state: State) -> Page:
    tree = SimpleTree("root")
    tree.children.append(tree)  # Create a self-reference
    state.past_words.append(tree)
    return Page(
        state,
        [
            "Added a self-referential tree to the list.",
            Link("Go back to the index page.", "/"),
        ],
    )


start_server(State([]))
