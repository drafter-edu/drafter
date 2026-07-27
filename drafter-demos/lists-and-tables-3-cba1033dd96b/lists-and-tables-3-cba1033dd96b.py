from drafter import *
from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    age: int


@route
def index() -> Page:
    return Page([
        Header("Residents"),
        Table([
            Pet("Ada", "corgi", 4),
            Pet("Babbage", "mutt", 6),
            Pet("Captain", "cat", 7),
            Pet("Domino", "cat", 2)
        ])
    ])


start_server()
