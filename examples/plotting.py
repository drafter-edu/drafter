from drafter import *
import random
import matplotlib.pyplot as plt
from dataclasses import dataclass

random.seed(0)

MOCK_DATA = [
    random.randint(0, 100) for _ in range(100)
]

@dataclass
class State:
    data: list[int]

@route
def index(state: State):
    plt.hist(MOCK_DATA)
    plt.title('Random data')
    return Page(state, [
        "Plotting!",
        MatPlotLibPlot(),
        Button("Add data", add_data)
    ])

@route
def add_data(state: State):
    state.data.append(random.randint(0, 100))
    return index(state)


start_server(State(MOCK_DATA))