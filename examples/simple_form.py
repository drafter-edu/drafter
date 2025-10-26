from drafter import *


@route
def index(state: str) -> Page:
    return Page(["Enter your name:", TextBox("name"), Button("Submit", process_form)])


@route
def process_form(state: str, name: str) -> Page:
    return Page(["Hello, " + name + "!"])


start_server("")
