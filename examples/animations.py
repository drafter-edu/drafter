from drafter import *


add_website_css("""
.fade-in-element {
  animation: fadeIn 2s ease-in forwards;
}

@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}
""")


@dataclass
class State:
    text: str


@route
def index(state: State):
    return Page(state, [
        Div("Hello, world!", classes="fade-in-element"),
        TextBox("text", state.text),
        Button("Click me!", "index")
    ])


start_server(State("Type something here"))