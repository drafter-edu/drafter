---
page_type: example
title: Shop
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Use Arguments, inventory state, and multiple routes together.
---

# Shop

## What it does

The shop displays a list of items, including each item's price and
remaining stock. It also shows how many coins the player currently
has. Each available item has a **Buy** button.

When the player buys an item, the application subtracts its price
from the player's coins, reduces the item's stock by one, and adds
the item to the player's inventory. The **Buy** button is not shown
when an item is out of stock. The application also rejects a
purchase when the player does not have enough coins.

All purchases are processed by the same `purchase` route. An
`Argument` identifies the item the player selected.

## Try it

Buy until something sells out, then until you run out of coins.

```python drafter height=360
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
```

## The code

The code has three layers, each with one job:

- `Item` and `State` hold the data: the shop's inventory, the
  player's coins, and the list of items the player owns.
- `find_item` is a helper that looks up an item by name. It returns
  a harmless placeholder rather than crashing when the name is
  unknown.
- `index` builds the storefront from the data, and `purchase`
  applies the purchase rules: the player pays the price, and the
  stock goes down.

## How it works

The loop in `index` makes a decision for each item: an item that is
in stock gets a Buy button and a price line, while a sold-out item
gets plain text with no button. The page's controls and the state
can never disagree, because the controls are *derived from* the
state each time the page is built.

Every Buy button targets the same `purchase` route, and the
`Argument("item_name", item.name)` attached to each button tells the
route which item was chosen. Inside `purchase`, the check for
insufficient coins comes *before* any change to the state, so a
failed purchase changes nothing. That ordering, validate first and
then mutate, is a habit worth building in any app that changes
state.

Mutating `item.stock` works because `find_item` returns the actual
`Item` object from the list, not a copy; changing that object
changes the inventory.

## Make it yours

1. **Modify**: give the shop a restock button that adds 1 to every
   item's stock.
2. **Modify**: sell an owned item back for half price (rounding down
   with `//` is fine).
3. **Complete**: refuse to sell a second crown to a player who
   already owns one, so the crown is limited to one per customer.
4. **Combine**: show the owned items with a `Table` of `Item`s
   instead of a `BulletedList` of names. This changes what the state
   remembers, from a list of names to a list of items.
5. **Create**: reskin the shop as a plant nursery, a potion stall,
   or a school bake sale. Only the data needs to change.

## Tests

The first test compares whole states, which lets it check all three
effects of a successful purchase at once: the coins go down, the
stock goes down, and the item joins the owned list. The second test
checks that a player without enough coins sees the refusal page. The
sold-out case is deliberately left untested; writing that assertion
yourself, `assert_has(index(State([Item("rope", 5, 0)], 10, [])),
"rope: sold out")`, is a good first exercise.

## Likely errors

- **`missing parameter` on `purchase`**: a Buy button is missing its
  `[Argument("item_name", ...)]`; every button targeting `purchase`
  must include one.
- **Stock goes negative**: the Buy button disappears when stock
  reaches zero, but if you add other paths to `purchase` (such as a
  "buy two" button), the route itself needs its own stock check. The
  reason is the same one the login example gives for guarding its
  private page: routes are reachable even without buttons.
- **Buying changes the display but not the coin count**: the changes
  must be made to `state` and to the `item` found in the list. A
  helper that returns a *new* `Item`, instead of the one in the
  list, breaks that connection.

## Related

- [Show different content](../add/show-different-content.md)
  explains the button-per-item pattern step by step.
- [Dynamic pages](../concepts/dynamic-pages.md) explains the
  underlying concept.
- [Argument](../reference/components/actions/argument.md) documents
  the component's exact behavior.
- [Pet registry](pet-registry.md) uses the same nested-data
  structure without the buying and selling.
