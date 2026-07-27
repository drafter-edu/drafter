from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entries: list[str]


@route
def index(state: State) -> Page:
    journal = ""
    for entry in state.entries:
        journal = journal + entry + "\n"
    return Page(state, [
        Header("Field Journal"),
        BulletedList(state.entries),
        "New entry:",
        TextBox("entry"),
        "\n",
        Button("Record", "record"),
        "\n",
        Download("Download the journal", "journal.txt", journal)
    ])


@route
def record(state: State, entry: str) -> Page:
    state.entries.append(entry)
    return index(state)


start_server(State(["Day 1: Captain ignored me."]))
