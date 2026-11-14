from drafter import *
from dataclasses import dataclass

add_website_js("""
if (!window.cardKeysReady) {
    window.cardKeysReady = true;
    document.addEventListener("keydown", function (event) {
        if (event.key === "ArrowRight") {
            var button = document.querySelector('[data-nav="next_card"]');
            if (button) {
                button.click();
            }
        }
    });
}
""")


@dataclass
class State:
    cards: list[str]
    position: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Flash Cards"),
        state.cards[state.position] + "\n",
        Button("Next", "next_card"),
        "\nThe right arrow key also shows the next card."
    ])


@route
def next_card(state: State) -> Page:
    state.position = (state.position + 1) % len(state.cards)
    return index(state)


assert_state(next_card(State(["one", "two"], 1)), State(["one", "two"], 0))

start_server(State([
    "Ada is a corgi.",
    "Babbage is a small black mutt.",
    "Captain is a grey cat.",
    "Domino is a black cat."
], 0))
