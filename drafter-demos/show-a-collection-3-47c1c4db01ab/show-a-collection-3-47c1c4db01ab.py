from drafter import *
from dataclasses import dataclass


@dataclass
class Player:
    name: str
    score: int


@dataclass
class State:
    players: list[Player]


def scoreboard(players: list[Player]) -> list:
    lines = []
    for player in players:
        lines.append(player.name + ": " + str(player.score) + " points\n")
    return lines


@route
def index(state: State) -> Page:
    return Page(state, [
        "Scoreboard:\n"
    ] + scoreboard(state.players) + [
        Button("Everyone scores", "all_score")
    ])


@route
def all_score(state: State) -> Page:
    for player in state.players:
        player.score = player.score + 1
    return index(state)


start_server(State([Player("Red team", 3), Player("Blue team", 5)]))
