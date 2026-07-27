"""
TODO: Currently, it doesn't seem like the seaborn dependency is getting picked up
by the automatic system?
"""

import random
from dataclasses import dataclass

import matplotlib.pyplot as plt

# import seaborn as sns
import pandas as pd

from drafter import *

random.seed(0)

MOCK_DATA = [random.randint(0, 100) for _ in range(100)]


@dataclass
class State:
    data: list[int]


@route
def index(state: State):
    df = pd.DataFrame({"data": state.data})
    # sns.histplot(df["data"], kde=True)
    df.plot.hist(y="data", bins=20)
    plt.title("Random data with Seaborn")

    return Page(
        state,
        ["Plotting!\n", MatPlotLibPlot(), LineBreak(), Button("Add data", add_data)],
    )


@route
def add_data(state: State):
    state.data.append(random.randint(0, 100))
    return index(state)


start_server(State(MOCK_DATA))
