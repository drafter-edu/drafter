from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    unread: int


def inbox_badge(unread: int) -> PageContent:
    if unread == 0:
        return "No new messages.\n"
    return bold(change_color(str(unread) + " new messages!\n", "crimson"))


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pigeon Post"),
        inbox_badge(state.unread),
        Button("A pigeon arrives", "arrive"),
        Button("Read everything", "read_all")
    ])


@route
def arrive(state: State) -> Page:
    state.unread = state.unread + 1
    return index(state)


@route
def read_all(state: State) -> Page:
    state.unread = 0
    return index(state)


start_server(State(0))
