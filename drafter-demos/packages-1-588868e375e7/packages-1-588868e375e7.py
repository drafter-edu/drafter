from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    plt.plot([1, 4, 2, 8, 5])
    plt.title("A chart from a third-party library")
    return Page(state, [
        Header("It works"),
        MatPlotLibPlot()
    ])


start_server(State())
