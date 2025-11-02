from dataclasses import dataclass
from drafter import *
from bakery import assert_equal


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            "Welcome to my site!",
            TextBox("pears", 7),
            TextBox("plums", "3"),
            Argument("apples", 5),
            Argument("words", "ups' and \" and downs"),
            Argument("check", True),
            Button(
                "Buy",
                "buy_page",
                [
                    Argument("oranges", 7),
                    Argument("fruits", "oranges and pears and more"),
                    Argument("bonus", False),
                ],
            ),
        ],
    )


@route
def buy_page(
    state: State,
    apples: int,
    oranges: int,
    pears: int,
    plums: str,
    fruits: str,
    words: str,
    check: bool,
    bonus: bool,
) -> Page:
    return Page(
        state,
        [
            f"You bought {apples} apples, {oranges} oranges, {plums} plums, and {pears} pears. ({fruits}) ({words}) ({check}) ({bonus})"
        ],
    )


assert_equal(
    index(State()),
    Page(
        state=State(),
        content=[
            "Welcome to my site!",
            TextBox(name="pears", kind="text", default_value=7),
            TextBox(name="plums", kind="text", default_value="3"),
            Argument(name="apples", value=5),
            Argument(name="words", value="ups' and \" and downs"),
            Argument(name="check", value=True),
            Button(
                text="Buy",
                url="/buy_page",
                arguments=[
                    Argument(name="oranges", value=7),
                    Argument(name="fruits", value="oranges and pears and more"),
                    Argument(name="bonus", value=False),
                ],
            ),
        ],
    ),
)

assert_equal(
    buy_page(
        State(),
        5,
        7,
        7,
        "3",
        "oranges and pears and more",
        "test and test",
        True,
        False,
    ),
    Page(
        state=State(),
        content=[
            "You bought 5 apples, 7 oranges, 3 plums, and 7 pears. (oranges and pears and more) (test and test) (True) (False)"
        ],
    ),
)

assert_equal(
    buy_page(
        State(),
        5,
        7,
        100,
        "200",
        "oranges and pears and more",
        "test and test",
        False,
        True,
    ),
    Page(
        state=State(),
        content=[
            "You bought 5 apples, 7 oranges, 200 plums, and 100 pears. (oranges and pears and more) (test and test) (False) (True)"
        ],
    ),
)

start_server(State())
