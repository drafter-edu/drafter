from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Two escape hatches"),
        Paragraph(
            "HtmlTag wraps safe content: ",
            HtmlTag("cite", "The Care and Feeding of Corgis"),
            "."
        ),
        RawHTML("<p>RawHTML renders <em>anything</em>, "
                "as written.</p>")
    ])


start_server(State())
