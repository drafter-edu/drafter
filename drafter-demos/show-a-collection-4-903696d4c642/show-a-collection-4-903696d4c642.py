from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    chores: list[str]


def chore_rows(chores: list[str]) -> list:
    rows = []
    position = 0
    for chore in chores:
        rows.append(chore + " ")
        rows.append(Button("Rename", "edit_chore", Argument("position", position)))
        rows.append(Button("Done", "finish_chore", Argument("position", position)))
        rows.append("\n")
        position = position + 1
    return rows


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Today's chores")
    ] + chore_rows(state.chores))


@route
def finish_chore(state: State, position: int) -> Page:
    state.chores.pop(position)
    return index(state)


@route
def edit_chore(state: State, position: int) -> Page:
    return Page(state, [
        "Rename this chore:",
        TextBox("new_name", state.chores[position]),
        "\n",
        Button("Save", "save_chore", Argument("position", position)),
        Button("Cancel", "index")
    ])


@route
def save_chore(state: State, position: int, new_name: str) -> Page:
    state.chores[position] = new_name
    return index(state)


assert_state(finish_chore(State(["Feed the cats", "Walk the dogs"]), 0),
             State(["Walk the dogs"]))
assert_state(save_chore(State(["Feed the cats", "Walk the dogs"]), 1, "Walk Ada"),
             State(["Feed the cats", "Walk Ada"]))

start_server(State(["Feed the cats", "Walk the dogs", "Water the plants"]))
