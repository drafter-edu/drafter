from drafter import *


@dataclass
class State:
    time: int = 0


@route
def index(state: State):
    return Page(
        state,
        [
            "Basic Timer (no frills):",
            Timer(1000 * 4, "/beep"),
            "\nTimer with controls:",
            Timer(1000 * 4, "/beep", controls=True),
            "\nStyled Timer:",
            Timer(
                1000 * 4, "/beep", style_background_color="blue", style_color="white"
            ),
            "\nCustom Ticker:",
            Timer(1000 * 4, "/beep", on_tick="/tick", rate=100),
            "\nCustom Ticker with TextBox:",
            Timer(1000 * 4, "/beep_with_box", on_tick="/tick_with_box"),
            "\nReturn to this page.",
            Button("Reload", index),
            "\nTextbox for form example:",
            TextBox("example_textbox", "Banana"),
        ],
    )


@route
def beep(state: State):
    return Fragment(state, ["BEEP!"])


@route
def tick(state: State, remaining: int):
    return Fragment(state, [f"Time remaining: {remaining} ms"])


@route
def tick_with_box(state: State, remaining: int, example_textbox: str):
    return Fragment(
        state, [f"Time remaining: {remaining} ms", f"Textbox value: {example_textbox}"]
    )


@route
def beep_with_box(state: State, remaining: int, example_textbox: str):
    return Fragment(state, [f"BEEPED: {example_textbox}"])


start_server(State(0))
