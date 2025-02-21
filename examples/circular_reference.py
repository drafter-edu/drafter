from drafter import *

@dataclass
class Item:
    name: str
    previously_seen: list

@dataclass
class State:
    items: list[Item]

# ...

first_item = Item("First Item", [])
second_item = Item("Second Item", [first_item])
first_item.previously_seen.append(second_item)
start_server(State([first_item, second_item]))