from drafter import *


def pet_card(name: str, species: str) -> PageContent:
    return Div(
        Header(name, 3),
        species + "\n",
        Button("Adopt " + name, "index"),
        style_border="2px solid darkseagreen",
        style_border_radius="8px",
        style_padding="12px",
        style_margin="8px"
    )


@route
def index() -> Page:
    return Page([
        Header("Adoption Corner"),
        pet_card("Babbage", "A small black mutt of great enthusiasm."),
        pet_card("Domino", "A black cat of great dignity.")
    ])


start_server()
