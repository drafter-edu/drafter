from bakery import assert_equal
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    todos: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Todo List App"),
        "Here are your todo items:",
        NumberedList(state.todos),
        "What would you like to do?",
        Button("Add new task", ask_new_item),
        Button("Delete task", request_delete_number)
    ])

@route
def ask_new_item(state: State) -> Page:
    return Page(state, [
        Header("Add New Task"),
        "What is the new task?",
        TextBox("new_task"),
        Button("Save new task", save_new_item),
        Button("Cancel", index)
    ])

@route
def save_new_item(state: State, new_task) -> Page:
    state.todos.append(new_task)
    return index(state)

@route
def request_delete_number(state: State) -> Page:
    return Page(state, [
        Header("Delete Task"),
        "What task do you want to delete?",
        TextBox("task_number"),
        Button("Delete task", delete_item),
        Button("Cancel", index)
    ])

@route
def delete_item(state: State, task_number: str) -> Page:
    if task_number.isdigit():
        task_number = int(task_number)
        if 0 < task_number <= len(state.todos):
            state.todos.pop(task_number - 1)
            return index(state)
        else:
            return error_page(state, "That task number is not valid.")
    else:
        return error_page(state, "That task number is not a number.")

@route
def error_page(state: State, error_message) -> Page:
    return Page(state, [
        Header("Error!"),
        "Error occurred:",
        error_message,
        Button("Okay", index)
    ])


start_server(State(["Wash the cat", "Pet the dog"]))