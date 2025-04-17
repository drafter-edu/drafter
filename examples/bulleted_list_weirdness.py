from bakery import assert_equal
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
        Pre("Alpha", "Beta"),
        "You have: " + str(state.money) + " coins",
        "You own: " + ", ".join(state.bought),
        "Select an item to purchase:",
        BulletedList(for_sale)
    ])

@route
def purchase(state: State) -> Page:
    return Page(state, [])



assert_equal(
 index(State(items=[Item(name='Sword', price=100, stock=3), Item(name='Shield', price=50, stock=5), Item(name='Potion', price=25, stock=10)], bought=[], money=200)),
 Page(state=State(items=[Item(name='Sword', price=100, stock=3),
                        Item(name='Shield', price=50, stock=5),
                        Item(name='Potion', price=25, stock=10)],
                 bought=[],
                 money=200),
     content=['Welcome to the store!',
                Pre('Alpha', 'Beta'),
              'You have: 200 coins',
              'You own: ',
              'Select an item to purchase:',
              BulletedList(items=[Span(content=['Buy',
                                                Button(text='Sword', url='/purchase', arguments=Argument(name='name', value='Sword')),
                                                'for 100 coins (3 left in stock)'],
                                       extra_settings={},
                                       kind='span'),
                                  Span(content=['Buy',
                                                Button(text='Shield', url='/purchase', arguments=Argument(name='name', value='Shield')),
                                                'for 50 coins (5 left in stock)'],
                                       extra_settings={},
                                       kind='span'),
                                  Span(content=['Buy',
                                                Button(text='Potion', url='/purchase', arguments=Argument(name='name', value='Potion')),
                                                'for 25 coins (10 left in stock)'],
                                       extra_settings={},
                                       kind='span')],
                           kind='ul')]))


start_server(State([
    Item("Sword", 100, 3),
    Item("Shield", 50, 5),
    Item("Potion", 25, 10)
], [], 200))