from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "CheckBox Examples:",
        Header("Basic Checkbox"),
        CheckBox("newsletter"),
        "Subscribe to newsletter",
        LineBreak(),
        Header("Checkbox with Default Value"),
        CheckBox("terms", True),
        "I agree to the terms (checked by default)",
        LineBreak(),
        Button("Submit", show_choices)
    ])

@route 
def show_choices(state: str, newsletter: bool, terms: bool) -> Page:
    newsletter_text = "Yes" if newsletter else "No"
    terms_text = "Yes" if terms else "No"
    
    return Page(state, [
        f"Newsletter subscription: {newsletter_text}",
        LineBreak(),
        f"Terms agreement: {terms_text}",
        LineBreak(),
        Link("Go back", index)
    ])

start_server("")