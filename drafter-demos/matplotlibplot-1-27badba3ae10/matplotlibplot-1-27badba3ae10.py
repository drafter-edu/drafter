from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    plt.plot([12, 15, 11, 18, 16, 20])
    plt.title("Treats eaten by Ada this week")
    return Page(state, [
        Header("Treat Tracker"),
        MatPlotLibPlot()
    ])


start_server(State())
