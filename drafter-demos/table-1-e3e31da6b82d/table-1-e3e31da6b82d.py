from drafter import *
from dataclasses import dataclass


@dataclass
class Expedition:
    destination: str
    days: int
    survived: bool


@route
def index() -> Page:
    return Page([
        Header("Expedition Log"),
        Table([
            Expedition("the volcano", 3, True),
            Expedition("the couch", 1, True),
            Expedition("the DMV", 1, False)
        ]),
        Header("Same data, lists and a custom header", 2),
        Table([
            ["the volcano", 3],
            ["the couch", 1]
        ], ["Place", "Days"])
    ])


start_server()
