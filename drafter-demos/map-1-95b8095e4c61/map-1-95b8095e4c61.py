from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Ada's Favorite Parks"),
        Map("spot",
            center=(39.68, -75.75),
            zoom=14,
            markers=[
                MapMarker(39.681, -75.756, "The big field"),
                MapMarker(39.677, -75.749, "Squirrel tree"),
                MapMarker(39.686, -75.744, "Best puddle")
            ])
    ])


start_server(State())
