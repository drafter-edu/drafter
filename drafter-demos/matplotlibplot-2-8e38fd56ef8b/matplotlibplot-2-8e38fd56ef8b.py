from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    naps: list[int]


@route
def index(state: State) -> Page:
    plt.bar(range(len(state.naps)), state.naps)
    plt.title("Captain's naps per day")
    return Page(state, [
        Header("Nap Chart"),
        MatPlotLibPlot(),
        Button("Record a lazy day", "lazy_day")
    ])


@route
def lazy_day(state: State) -> Page:
    state.naps.append(state.naps[-1] + 1)
    return index(state)


start_server(State([3, 4, 2]))
