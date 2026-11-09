"""
A seaborn chart. Seaborn is not one of the libraries bundled with the
browser's Python, so Drafter installs it from PyPI when it sees the import.

To run this on your own computer, install the libraries there first:

    pip install seaborn pandas
"""

import random
from dataclasses import dataclass

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from drafter import *

random.seed(0)

MOCK_DATA = [random.randint(0, 100) for _ in range(100)]


@dataclass
class State:
    data: list[int]


@route
def index(state: State):
    df = pd.DataFrame({"data": state.data})
    sns.histplot(df["data"], kde=True)
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
