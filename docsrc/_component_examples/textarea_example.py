from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "TextArea Examples:",
        Header("Basic TextArea"),
        TextArea("user_comment"),
        Header("TextArea with Default Value"),
        TextArea("prefilled_comment", "This is pre-filled text..."),
        Button("Submit", process_form)
    ])

@route 
def process_form(state: str, user_comment: str, prefilled_comment: str) -> Page:
    return Page(state, [
        "Your comments:",
        Header("Basic comment:", 3),
        user_comment,
        Header("Prefilled comment:", 3),
        prefilled_comment,
        Link("Go back", index)
    ])

start_server("")