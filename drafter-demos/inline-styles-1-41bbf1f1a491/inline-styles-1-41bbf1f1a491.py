from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("House Rules"),
        Paragraph(
            Strong("Never"), " leave the treat jar open. ",
            Emphasis("Captain is always watching.")
        ),
        Paragraph(
            "Press ", KeyboardInput("Ctrl"), " + ",
            KeyboardInput("S"), " to save your progress."
        ),
        Paragraph(
            "Dinner is at ", DeletedText("5:00"), " ",
            InsertedText("4:45"),
            SmallText(" (the cats renegotiated).")
        ),
        Paragraph(
            "The ", Abbreviation("ASPCA",
                title="American Society for the Prevention of "
                      "Cruelty to Animals"),
            " approves of this household."
        )
    ])


start_server(State())
