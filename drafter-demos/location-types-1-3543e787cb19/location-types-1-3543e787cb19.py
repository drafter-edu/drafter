from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Where the pets sleep"),
        Map("spot",
            center=(39.68, -75.75),
            zoom=16,
            markers=[
                MapMarker(39.6805, -75.7515, "Ada's bed"),
                MapMarker(39.6801, -75.7508, "Captain's tower"),
                MapMarker(39.6798, -75.7512)
            ])
    ])


start_server(State())
