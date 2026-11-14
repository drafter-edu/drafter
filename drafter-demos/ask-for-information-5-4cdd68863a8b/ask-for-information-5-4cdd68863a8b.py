from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    tickets: str
    problem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Ticket booth"),
        state.problem,
        "How many tickets would you like (1 to 10)?",
        TextBox("tickets", state.tickets),
        "\n",
        Button("Buy", "buy")
    ])


@route
def buy(state: State, tickets: str) -> Page:
    state.tickets = tickets
    if not tickets.isdigit():
        state.problem = "Please type a whole number.\n"
        return index(state)
    if int(tickets) < 1 or int(tickets) > 10:
        state.problem = "You can buy between 1 and 10 tickets.\n"
        return index(state)
    state.problem = ""
    cost = int(tickets) * 5
    return Page(state, [
        "You bought " + tickets + " tickets for " + str(cost) + " gold.\n",
        Button("Buy more", "index")
    ])


assert_has(buy(State("", ""), "lots"), "Please type a whole number.")
assert_has(buy(State("", ""), "40"), "between 1 and 10")
assert_has(buy(State("", ""), "3"), "You bought 3 tickets for 15 gold.")

start_server(State("2", ""))
