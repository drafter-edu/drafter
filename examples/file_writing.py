from drafter import *
from dataclasses import dataclass

DEFAULT_FILENAME = "existing.txt"

@dataclass
class State:
    filename: str
    file_content: str


try:
    with open(DEFAULT_FILENAME, "r") as f:
        initial_content = f.read()
except FileNotFoundError:
    initial_content = "*No existing file content found*.\n"

@route
def index(state: State):
    return Page(state, [
        "File:", state.filename,
        "Current content in state:",
        state.file_content,
        "Enter new content to write to the file:",
        TextArea("new_content"),
        Button("Write to file", write_file_page),
        Button("View actual file", load_file_page),
        Button("Change filename", change_filename_page)
    ])

@route
def write_file_page(state: State, new_content: str):
    with open(state.filename, "w") as f:
        f.write(new_content)
    return Page(state, [
        f"File {state.filename} has been updated. New content:",
        new_content,
        Button("Go back", index)
    ])

@route
def load_file_page(state: State):
    try:
        with open(state.filename, "r") as f:
            file_content = f.read()
    except FileNotFoundError:
        file_content = "*File not found*."
    return Page(state, [
        "Actual file content:",
        file_content,
        Button("Go back", index)
    ])

@route
def change_filename_page(state: State):
    return Page(state, [
        "Enter new filename:",
        TextBox("new_filename"),
        Button("Change filename", finish_change_filename_page),
        Button("Go back", index)
    ])

@route
def finish_change_filename_page(state: State, new_filename: str):
    state.filename = new_filename
    return index(state)


start_server(State(filename=DEFAULT_FILENAME, file_content=initial_content),
             cdn_skulpt="http://localhost:8000/skulpt.js",
             cdn_skulpt_std="http://localhost:8000/skulpt-stdlib.js",
             cdn_skulpt_drafter="http://localhost:8081/skulpt-drafter.js",)