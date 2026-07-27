from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    lines: list[str]


@route
def index(state: State) -> Page:
    transcript = ""
    for line in state.lines:
        transcript = transcript + line + "\n"
    return Page(state, [
        Header("Meeting Notes"),
        BulletedList(state.lines),
        "Add a note:",
        TextBox("note"),
        "\n",
        Button("Note it", "note_it"),
        "\n",
        Download("Save the notes", "notes.txt", transcript)
    ])


@route
def note_it(state: State, note: str) -> Page:
    state.lines.append(note)
    return index(state)


start_server(State(["Meeting began late."]))
