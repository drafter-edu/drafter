from drafter import *
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price: int
    stock: int


@dataclass
class State:
    items: list[Item]
    coins: int
    owned: list[str]


def find_item(items: list[Item], name: str) -> Item:
    for item in items:
        if item.name == name:
            return item
    return Item("nothing", 0, 0)


@route
def index(state: State) -> Page:
    content = [
        Header("The Adventurer's Shop"),
        "You have " + str(state.coins) + " coins.\n",
        "You own:",
        BulletedList(state.owned),
        HorizontalRule()
    ]
    for item in state.items:
        if item.stock > 0:
            content.append(Button("Buy " + item.name, "purchase",
                                  [Argument("item_name", item.name)]))
            content.append(" " + str(item.price) + " coins, "
                           + str(item.stock) + " left\n")
        else:
            content.append(item.name + ": sold out\n")
    return Page(state, content)


@route
def purchase(state: State, item_name: str) -> Page:
    item = find_item(state.items, item_name)
    if state.coins < item.price:
        return Page(state, [
            "You cannot afford the " + item.name + ".\n",
            Button("Back to the shop", "index")
        ])
    state.coins = state.coins - item.price
    item.stock = item.stock - 1
    state.owned.append(item.name)
    return index(state)


assert_state(
    purchase(State([Item("rope", 5, 2)], 12, []), "rope"),
    State([Item("rope", 5, 1)], 7, ["rope"]))
assert_has(
    purchase(State([Item("crown", 100, 1)], 3, []), "crown"),
    "You cannot afford the crown.")

start_server(State([
    Item("rope", 5, 2),
    Item("lantern", 12, 1),
    Item("crown", 100, 1)
], 30, []))
