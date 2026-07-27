from drafter import *

@route
def index() -> Page:
    return Page([
        Text("This page works fine."),
        Button("Next", "another_page")
    ],
    js="""
        let counter = 0;
        alert("Counter is " + counter);
    """)

@route
def another_page() -> Page:
    return Page([
        Text("This page will have an error in the JS console.")
    ],
    js="""
        let counter = 2;
        alert("Counter is " + counter);
    """)

start_server()