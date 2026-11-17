from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    entries: list[str]


def entries_to_text(entries: list[str]) -> str:
    text = ""
    for entry in entries:
        text = text + entry + "\n"
    return text


def text_to_entries(text: str) -> list[str]:
    entries = []
    for line in text.split("\n"):
        if line.strip() != "":
            entries.append(line.strip())
    return entries


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Field Journal"),
        BulletedList(state.entries),
        "New entry:",
        TextBox("entry"),
        Button("Record", "record"),
        "\n",
        Download("Save my journal", "journal.txt",
                 entries_to_text(state.entries)),
        " or ",
        Link("load a saved journal", "ask_for_file")
    ])


@route
def record(state: State, entry: str) -> Page:
    state.entries.append(entry)
    return index(state)


@route
def ask_for_file(state: State) -> Page:
    return Page(state, [
        "Choose the journal.txt file you saved earlier:",
        FileUpload("saved_file", accept=".txt"),
        "\n",
        Button("Load", "load_journal"),
        Link("Cancel", "index")
    ])


@route
def load_journal(state: State, saved_file: str) -> Page:
    if saved_file != "":
        state.entries = text_to_entries(saved_file)
    return index(state)


assert_equal(entries_to_text(["Day 1", "Day 2"]), "Day 1\nDay 2\n")
assert_equal(text_to_entries("Day 1\nDay 2\n"), ["Day 1", "Day 2"])
assert_state(load_journal(State(["Old entry"]), "Day 1\nDay 2\n"),
             State(["Day 1", "Day 2"]))
assert_state(load_journal(State(["Old entry"]), ""), State(["Old entry"]))

start_server(State(["Day 1: Captain ignored me."]))
