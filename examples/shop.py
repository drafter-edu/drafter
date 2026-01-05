from drafter import *
from typing import Optional


@dataclass
class Item:
    name: str
    price: int
    stock: int


@dataclass
class State:
    items2: list[Item]
    bought: list[str]
    money: int
    tiles: list[list[str]]


@route
def index(state: State) -> Page:
    for_sale = []
    for item in state.items2:
        if item.stock > 0:
            content = Span(
                "Buy",
                Button(item.name, purchase, arguments=Argument("name", item.name)),
                "for "
                + str(item.price)
                + " coins ("
                + str(item.stock)
                + " left in stock)",
            )
            for_sale.append(content)
    return Page(
        state,
        [
            "Welcome to the store!",
            "You have: " + str(state.money) + " coins",
            "You own: " + ", ".join(state.bought),
            "Select an item to purchase:",
            BulletedList(for_sale),
        ],
    )


def find_item(items2: list[Item], name: str) -> Optional[Item]:
    for item in items2:
        if item.name == name:
            return item
    return None


@route
def purchase(state: State, name: str) -> Page:
    # Is the item in the store?
    item = find_item(state.items2, name)
    if item is None:
        return Page(
            state,
            [
                "Sorry, we do not have a " + name + " in stock",
                Button("Return to store", index),
            ],
        )
    # Is the item in stock?
    elif item.stock <= 0:
        return Page(
            state,
            [
                "Sorry, we are out of stock of " + item.name,
                Button("Return to store", index),
            ],
        )
    # Do they have enough money?
    elif state.money < item.price:
        return Page(
            state,
            ["You cannot afford a " + item.name, Button("Return to store", index)],
        )
    else:
        # Item is in stock, and player has enough money
        item.stock -= 1
        state.money -= item.price
        state.bought.append(item.name)
        return Page(
            state,
            [
                "You have purchased a "
                + item.name
                + " for "
                + str(item.price)
                + " coins",
                Button("Return to store", index),
            ],
        )


assert_equal(
    index(State([], [], 0, [])),
    Page(
        State([], [], 0, []),
        [
            "Welcome to the store!",
            "You have: 0 coins",
            "You own: ",
            "Select an item to purchase:",
            BulletedList([]),
        ],
    ),
)


start_server(
    State(
        [
            Item("Sword of Hope", 100, 3),
            Item("John's Shield", 50, 5),
            Item("Potion", 25, 10),
            Item("!@#$%^&*\"')()<>", 100, 47),
        ],
        ["Potion", "Vulnery"],
        200,
        [
            ["Grass", "Grass", "Tree"],
            ["Water", "Water", "Grass"],
            ["Mountain", "Grass", "Grass"],
        ],
    )
)
