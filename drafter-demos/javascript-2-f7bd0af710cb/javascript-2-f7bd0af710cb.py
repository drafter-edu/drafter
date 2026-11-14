from drafter import *
from dataclasses import dataclass
import sys

IN_BROWSER = sys.platform == "emscripten"


@dataclass
class State:
    pass


def window_width() -> int:
    if not IN_BROWSER:
        return 1024
    import js
    return int(js.window.innerWidth)


def describe_width(width: int) -> str:
    if width < 600:
        return "a narrow window, probably on a phone"
    return "a wide window"


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Window Check"),
        "You are using " + describe_width(window_width()) + "."
    ])


assert_equal(describe_width(400), "a narrow window, probably on a phone")
assert_equal(describe_width(1280), "a wide window")
assert_has(index(State()), Header("Window Check"))

start_server(State())
