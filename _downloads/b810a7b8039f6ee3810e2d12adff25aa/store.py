from drafter import *
from bakery import assert_equal
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price: int
    stock: int


@dataclass
class State:
    items: list[Item]
    bought: list[str]
    money: int


@route
def index(state: State) -> Page:
    for_sale = []
    for item in state.items:
        if item.stock > 0:
            content = Span("Buy",
                           Button(item.name, purchase, arguments=Argument("name", item.name)),
                           "for " + str(item.price) + " coins (" + str(item.stock) + " left in stock)")
            for_sale.append(content)
    return Page(state, [
        "Welcome to the store!",
        "You have: " + str(state.money) + " coins",
        "You own: " + ", ".join(state.bought),
        "Select an item to purchase:",
        BulletedList(for_sale)
    ])


def find_item(items: list[Item], name: str) -> Item:
    for item in items:
        if item.name == name:
            return item
    return None


@route
def purchase(state: State, name: str) -> Page:
    # Is the item in the store?
    item = find_item(state.items, name)
    if item is None:
        return Page(state, [
            "Sorry, we do not have a " + name + " in stock",
            Button("Return to store", index)
        ])
    # Is the item in stock?
    elif item.stock <= 0:
        return Page(state, [
            "Sorry, we are out of stock of " + item.name,
            Button("Return to store", index)
        ])
    # Do they have enough money?
    elif state.money < item.price:
        return Page(state, [
            "You cannot afford a " + item.name,
            Button("Return to store", index)
        ])
    else:
        # Item is in stock, and player has enough money
        item.stock -= 1
        state.money -= item.price
        state.bought.append(item.name)
        return Page(state, [
            "You have purchased a " + item.name + " for " + str(item.price) + " coins",
            Button("Return to store", index)
        ])



start_server(State([
    Item("Sword", 100, 3),
    Item("Shield", 50, 5),
    Item("Potion", 25, 10)
], [], 200))