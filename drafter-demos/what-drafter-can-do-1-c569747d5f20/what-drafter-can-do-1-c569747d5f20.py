from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Victory Fanfare"),
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160),
        "\nWith echo: ",
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160, effects=[Echo()]),
        "\nDoorbell: ",
        Tone("E5", duration=300)
    ])


start_server()
