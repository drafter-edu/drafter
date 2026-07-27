from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Background Music Example"),
            Paragraph(
                "This page demonstrates how to play background music using the drafter framework."
            ),
            Audio(
                src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                controls=True,
                autoplay=True,
                loop=True,
                muted=False,
                persistent=True,
            ),
            Paragraph(
                "The audio above will continue playing even if you navigate to another page."
            ),
            Button("Go to Another Page", another_page),
        ],
    )


@route
def another_page(state: State) -> Page:
    return Page(
        state,
        [
            Header("Another Page"),
            Paragraph(
                "You can navigate back to the main page and the background music will still be playing."
            ),
            Button("Back to Main Page", index),
        ],
    )


start_server(State())
