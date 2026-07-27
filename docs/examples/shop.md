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

A little shop: items with prices and stock, a purse of coins, and a
Buy button per item. Buying spends coins, lowers stock, and adds the
item to what you own; sold-out items lose their button, and spending
beyond your purse gets refused. One `purchase` route handles every
item, told apart by an `Argument`.

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

Three layers, each with one job:

- `Item` and `State` are the data: the shop's inventory, your purse,
  your haul.
- `find_item` is a helper answering "which item is this name?"; it
  returns a harmless placeholder rather than crashing on unknown
  names.
- `index` builds the storefront from the data, and `purchase`
  enforces the two rules of commerce: you pay, and stock drops.

## How it works

The storefront loop makes a decision per item: in stock gets a
button plus its price line, sold out gets plain text with no button.
The page's controls and the state can never disagree, because the
controls are *derived from* the state each time the page is built.

Each Buy button carries `Argument("item_name", item.name)`, so every
one targets the same `purchase` route. The refusal branch comes
*before* any mutation: check first, then spend, so a failed purchase
changes nothing. That ordering habit (validate, then mutate) is
worth stealing for every app that changes state.

Mutating `item.stock` works because `find_item` returns the actual
`Item` object from the list, not a copy; changing it changes the
inventory.

## Make it yours

1. **Modify**: give the shop a restock button that adds 1 to every
   item's stock.
2. **Modify**: sell an owned item back for half price (rounding down
   with `//` is fine).
3. **Complete**: refuse to sell a second crown to someone who owns
   one; some things should be one per customer.
4. **Combine**: show the haul with a `Table` of `Item`s instead of a
   `BulletedList` of names, which means owning changes from
   remembering names to remembering items.
5. **Create**: reskin it as a plant nursery, a potion stall, or a
   school bake sale; only the data changes.

## Tests

The success test checks all three effects of one purchase at once,
coins down, stock down, item owned, by comparing whole states. The
refusal test checks that being short of coins produces the polite
page. Missing from the tests, deliberately, is the sold-out case;
adding `assert_has(index(State([Item("rope", 5, 0)], 10, [])),
"rope: sold out")` is the first Make-it-yours of the Tests section.

## Likely errors

- **`missing parameter` on `purchase`**: a Buy button lost its
  `[Argument("item_name", ...)]`; every button targeting `purchase`
  must carry one.
- **Stock goes negative**: the button disappears at zero stock, but
  if you add other paths to `purchase` (a "buy two" button), the
  route itself needs a stock check too, for the same reason the
  login example guards its private page: routes are reachable
  without buttons.
- **Buying changes the display but not the purse**: the mutation
  must land on `state` and the found `item`; a helper that returns
  a *new* `Item` instead of the one in the list breaks the link.

## Related

- [Show different content](../add/show-different-content.md): the
  button-per-item pattern, explained as a recipe.
- [Dynamic pages](../concepts/dynamic-pages.md): the concept.
- [Argument](../reference/components/actions/argument.md): exact
  behavior.
- [Pet registry](pet-registry.md): the same nested-data shape
  without the commerce.
