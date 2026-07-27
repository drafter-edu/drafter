from drafter import *


@route
def index() -> Page:
    return Page([
        Header("The Plan"),
        "Ingredients (order does not matter):",
        BulletedList(["flour", "butter", "improbable optimism"]),
        "Steps (order very much matters):",
        NumberedList(["preheat", "mix", "regret nothing", "bake"])
    ])


start_server()
