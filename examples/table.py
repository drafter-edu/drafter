from bakery import assert_equal
from dataclasses import dataclass
from drafter import route, start_server, Page, TextBox, SubmitButton, SelectBox, Table, hide_debug_information



hide_debug_information()

@dataclass
class Dog:
    name: str
    age: int
    breed: str

@route
def index(state: list[Dog]) -> Page:
    return Page(state, [
        "There are " + str(len(state)) + " dogs",
        "What do you want to do?",
        SubmitButton("Add a dog", add_dog_page),
        "View the dogs.",
        SubmitButton("View the dogs", view_dogs_page)
    ])


@route
def add_dog_page(state: list[Dog]) -> Page:
    return Page(state, [
        "What is the dog's name?",
        TextBox("name"),
        "What is the dog's age?",
        TextBox("age"),
        "What is the dog's breed?",
        SelectBox("breed", ["corgi", "schnauzer", "mutt"]),
        SubmitButton("Add this dog", finish_adding_dog_page),
        SubmitButton("Go back", index)
    ])
    
@route
def finish_adding_dog_page(state: list[Dog], name: str, age: str, breed: str) -> Page:
    state.append(Dog(name, int(age), breed))
    return index(state)

@route
def view_dogs_page(state: list[Dog]) -> Page:
    return Page(state, [
        "Here are the dogs:",
        Table(state),
        SubmitButton("Go back", index)
    ])

start_server([], reloader=True)