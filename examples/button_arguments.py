from bakery import assert_equal
from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        "Welcome to my site!",
        TextBox("pears", 7),
        TextBox("plums", "3"),
        Argument("apples", 5),
        Button("Buy", "buy_page", Argument("oranges", 7))
    ])


@route
def buy_page(state: State, apples: int, oranges: int, pears: int, plums: str) -> Page:
    return Page(state, [
        f"You bought {apples} apples, {oranges} oranges, {plums} plums, and {pears} pears",
    ])


assert_equal(
    index(State()),
    Page(state=State(),
         content=['Welcome to my site!',
                  TextBox(name='pears', kind='text', default_value=7),
                  TextBox(name='plums', kind='text', default_value='3'),
                  Argument(name='apples', value=5),
                  Button(text='Buy', url='/buy_page', arguments=Argument(name='oranges', value=7))]))

assert_equal(
    buy_page(State(), 5, 7, 7, '3'),
    Page(state=State(), content=['You bought 5 apples, 7 oranges, 3 plums, and 7 pears']))

assert_equal(
    buy_page(State(), 5, 7, 100, '200'),
    Page(state=State(), content=['You bought 5 apples, 7 oranges, 200 plums, and 100 pears']))

start_server(State())
