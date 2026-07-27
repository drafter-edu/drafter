from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    tasks: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("To-Do"),
        NumberedList(state.tasks),
        Button("Add a task", "ask_new_task"),
        Button("Remove a task", "ask_remove_task")
    ])


@route
def ask_new_task(state: State) -> Page:
    return Page(state, [
        Header("Add a task"),
        "What needs doing?",
        TextBox("description"),
        "\n",
        Button("Save", "save_task"),
        Button("Cancel", "index")
    ])


@route
def save_task(state: State, description: str) -> Page:
    state.tasks.append(description)
    return index(state)


@route
def ask_remove_task(state: State) -> Page:
    return Page(state, [
        Header("Remove a task"),
        NumberedList(state.tasks),
        "Which number is done?",
        TextBox("number"),
        "\n",
        Button("Remove", "remove_task"),
        Button("Cancel", "index")
    ])


@route
def remove_task(state: State, number: str) -> Page:
    if number.isdigit():
        position = int(number)
        if 1 <= position <= len(state.tasks):
            state.tasks.pop(position - 1)
            return index(state)
    return Page(state, [
        "There is no task number " + number + ".\n",
        Button("Try again", "ask_remove_task"),
        Button("Back to the list", "index")
    ])


assert_state(save_task(State([]), "walk Babbage"),
             State(["walk Babbage"]))
assert_state(remove_task(State(["a", "b", "c"]), "2"),
             State(["a", "c"]))
assert_has(remove_task(State(["a"]), "99"), "There is no task number 99.")

start_server(State(["walk Babbage", "feed Captain"]))
