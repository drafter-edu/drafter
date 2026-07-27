from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Nav(Link("Home", "index"), " | ", Link("Gallery", "gallery")),
        Main(
            Header("The Daily Babbage"),
            Article(
                Header("Mutt wins hearts at park", 2),
                Paragraph("Witnesses describe the small black dog "
                          "as 'a very good boy'.")
            ),
            Figure(
                "[photo of Babbage looking dignified]",
                FigureCaption("Babbage, moments after the incident.")
            )
        ),
        FooterContent(SmallText("The Daily Babbage is written by pets."))
    ])


@route
def gallery(state: State) -> Page:
    return Page(state, [
        Header("Gallery"),
        Nav(Link("Back home", "index"))
    ])


start_server(State())
