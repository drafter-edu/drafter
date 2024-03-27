from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    balance: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Your current balance is:",
        state.balance,
        Button("Withdraw", start_withdraw),
        # Button("Deposit", start_deposit)
    ])


@route
def start_withdraw(state: State) -> Page:
    return Page(state, [
        "How much do you want to withdraw?",
        TextBox("amount", 10),
        Button("Make withdraw", update_balance),
        Button("Cancel", index)
    ])


@route
def update_balance(state: State, amount: int) -> Page:
    state.balance -= amount
    return index(state)


start_server(State(1000))
