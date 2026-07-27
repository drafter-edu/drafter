from drafter import Button, Page, add_route, start_server


def index():
    return Page(
        None,
        [
            "Hello, World!",
            Button("Second page with Slash", "/second"),
            Button("Second page", "second"),
            Button("Second page as Function", second),
        ],
    )


def second():
    return Page(None, ["Welcome to the second page.", Button("Third page", "/third")])


def third():
    return Page(None, ["Welcome to the third page.", Button("Return to start", "/")])


add_route("/", index)
add_route("/second", second)
add_route("/third", third)

start_server()
