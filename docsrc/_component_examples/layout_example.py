from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Layout Examples:",
        Header("LineBreak Example"),
        "First line",
        LineBreak(),
        "Second line after line break",
        
        HorizontalRule(),
        
        Header("Horizontal Rule Example"),
        "Content above the rule",
        HorizontalRule(),
        "Content below the rule",
        
        HorizontalRule(),
        
        Header("Div and Span Examples"),
        Div(
            "This content is in a div container",
            LineBreak(),
            Span("This is in a span", style="color: blue;"),
            " and this continues after the span."
        )
    ])

start_server("")