from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "This page overrides the default error page to show that you can customize it.",
            "The error message below is intentionally caused by a division by zero.",
            "\n",
            Button("Cause an error", cause_error),
        ],
    )


@route
def cause_error(state: State) -> Page:
    # This will cause a ZeroDivisionError, which will be caught and displayed using the custom error page.
    result = 1 / 0
    return Page(state, [f"The result is: {result}"])


set_error_page(
    "Oh No It Went Badly",
    "Something went wrong on the server. Please try again later.",
    False,
)


start_server(State())
