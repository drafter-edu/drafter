import random
from dataclasses import dataclass

import matplotlib.pyplot as plt

from drafter import *

random.seed(0)

MOCK_DATA = [random.randint(0, 100) for _ in range(100)]


@dataclass
class State:
    data: list[int]


@route
def index(state: State):
    plt.hist(MOCK_DATA)
    plt.title("Random data")
    return Page(
        state,
        ["Plotting!\n", MatPlotLibPlot(), LineBreak(), Button("Add data", add_data)],
    )


@route
def add_data(state: State):
    state.data.append(random.randint(0, 100))
    return index(state)


start_server(State(MOCK_DATA))
