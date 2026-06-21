add_website_css("""
body {
    margin: 0;
    font-family: sans-serif;
}
.card {
    padding: 1rem;
    color: red;
}
""")


def index(state: State) -> Page:
    return Page(
        state,
        [
            Div(
                "Hello",
                bold("world"),
                "!",
                Button("Click Me", style_padding="0.5rem", style_color="blue"),
                classes="card",
            )
        ],
    )
