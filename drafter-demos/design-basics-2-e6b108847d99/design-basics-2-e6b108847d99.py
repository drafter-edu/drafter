from drafter import *


def crowded() -> list:
    return [
        Header("Bake Sale", 3),
        Header("Cookies", 3),
        "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
        Header("When", 3),
        "Saturday.\n"
    ]


def designed() -> list:
    return [
        Header("Bake Sale"),
        change_padding(Div(
            Header("Cookies", 2),
            change_width(
                "Chocolate chunk, oatmeal, mystery. All good. Probably.\n",
                "30em")
        ), "12px"),
        change_padding(Div(
            Header("When", 2),
            change_color(bold("Saturday.\n"), "darkslateblue")
        ), "12px")
    ]


@route
def index() -> Page:
    return Page(
        [Header("Crowded", 4), HorizontalRule()] + crowded() +
        [HorizontalRule(), Header("Designed", 4), HorizontalRule()] +
        designed()
    )


start_server()
