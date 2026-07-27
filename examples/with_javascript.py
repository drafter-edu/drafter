from drafter import *
from bakery import assert_equal

code = """
setTimeout(() => {
    alert("Hello world!");
}, 1000);
"""

@route
def index(state: str) -> Page:
    return Page(state, [
        Image("", width="0", onerror=code)
    ], js="<script>console.log('JavaScript is working!');</script>")

@route
def update_message(state: str, new_message: str) -> Page:
    state = new_message
    return index(state)

assert_equal(index("Hello"),
             Page("Hello", [
                 "Current message: Hello",
                 TextBox("new_message", "Enter new message"),
                 Button("Update Message", update_message),
             ])
             )

start_server("Initial",
             cdn_skulpt="http://localhost:8000/skulpt.js",
             cdn_skulpt_std="http://localhost:8000/skulpt-stdlib.js",
             cdn_skulpt_drafter="http://localhost:8081/skulpt-drafter.js",)