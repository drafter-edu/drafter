from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    walks: list[int]


@route
def index(state: State) -> Page:
    plt.bar(range(len(state.walks)), state.walks)
    plt.title("Blocks walked with Babbage")
    return Page(state, [
        Header("Walk Tracker"),
        MatPlotLibPlot(),
        Button("Log a long walk", "long_walk")
    ])


@route
def long_walk(state: State) -> Page:
    state.walks.append(8)
    return index(state)


start_server(State([3, 5, 2]))
