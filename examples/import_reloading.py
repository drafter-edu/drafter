from drafter import *
import import_reloading_friend


@route
def index():
    return Page(
        None,
        [
            "This should crash if you change the flag in the other file.",
            "No Error Found" if not import_reloading_friend.show_error else 1 / 0,
        ],
    )


start_server()
