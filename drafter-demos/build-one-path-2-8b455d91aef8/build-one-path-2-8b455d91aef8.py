from drafter import *
from dataclasses import dataclass


@dataclass
class Entry:
    date: str
    distance_km: float
    note: str


@dataclass
class State:
    entries: list[Entry]
    goal_km: float


@route
def index(state: State) -> Page:
    lines = []
    for entry in state.entries:
        lines.append(entry.date + ": " + str(entry.distance_km) + " km")
    return Page(state, [
        Header("Trail Tracker"),
        BulletedList(lines),
        Button("Add a hike", "add_entry")
    ])


@route
def add_entry(state: State) -> Page:
    return Page(state, [
        Header("New hike"),
        "Date:",
        DateInput("date"),
        "\nDistance in km:",
        TextBox("distance", 5),
        "\nNote:",
        TextBox("note"),
        "\n",
        Button("Save", "save_entry"),
        Button("Cancel", "index")
    ])


@route
def save_entry(state: State, date: str, distance: float, note: str) -> Page:
    state.entries.append(Entry(date, distance, note))
    return index(state)


assert_state(
    save_entry(State([], 100.0), "2026-07-27", 8.5, "with Babbage"),
    State([Entry("2026-07-27", 8.5, "with Babbage")], 100.0))

start_server(State([], 100.0))
