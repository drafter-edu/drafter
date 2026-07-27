from drafter import *
from dataclasses import dataclass


@dataclass
class Recipe:
    name: str
    minutes: int
    difficulty: str


@route
def index() -> Page:
    return Page([
        Header("Tonight"),
        DefinitionList(Recipe("impossible pie", 45, "brave"))
    ])


start_server()
