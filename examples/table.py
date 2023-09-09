from bakery import assert_equal
from dataclasses import dataclass
from drafter import route, start_server, Page, Textbox, SubmitButton, Dropdown, Table


@dataclass
class Dog:
    name: str
    age: int
    breed: str

@route
def index_page(state: list[Dog]) -> Page:
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
        Textbox("name", "text"),
        "What is the dog's age?",
        Textbox("age", "number"),
        "What is the dog's breed?",
        Dropdown("breed", ["corgi", "schnauzer", "mutt"]),
        SubmitButton("Add this dog", finish_adding_dog_page),
        SubmitButton("Go back", index_page)
    ])
    
@route
def finish_adding_dog_page(state: list[Dog], name: str, age: str, breed: str) -> Page:
    state.append(Dog(name, int(age), breed))
    return index_page(state)

@route
def view_dogs_page(state: list[Dog]) -> Page:
    return Page(state, [
        "Here are the dogs:",
        Table(state),
        SubmitButton("Go back", index_page)
    ])

start_server([], reloader=True)