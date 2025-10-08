from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Header Examples:",
        Header("Level 1 Header (h1)"),
        Header("Level 2 Header (h2)", 2),
        Header("Level 3 Header (h3)", 3),
        Header("Level 4 Header (h4)", 4),
        Header("Level 5 Header (h5)", 5),
        Header("Level 6 Header (h6)", 6),
    ])

start_server("")