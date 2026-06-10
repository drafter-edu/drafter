"""
A simple application for managing a bank account.
"""
from drafter import *
from bakery import assert_equal
from dataclasses import dataclass


@dataclass
class State:
    """ The state of the bank account app. """


@route
def index(state: State) -> Page:
    """ The main page of the bank account app, showing the balance and options to withdraw or deposit. """

@route
def start_withdraw(state: State) -> Page:
    """ The page for starting a withdrawal. """


@route
def finish_withdraw(state: State, amount: int) -> Page:
    """ The page for finishing a withdrawal. """


@route
def start_deposit(state: State) -> Page:
    """ The page for starting a deposit. """


@route
def finish_deposit(state: State, amount: int) -> Page:
    """ The page for finishing a deposit. """

# Check that the index page renders correctly
assert_equal(
    index(State(balance=100)),
    Page(
        state=State(balance=100),
        content=[
            "Your current balance is:",
            "100",
            Button(text="Withdraw", url="/start_withdraw"),
            Button(text="Deposit", url="/start_deposit"),
        ],
    ),
)

# Check that the start_withdraw page renders correctly
assert_equal(
    start_withdraw(State(balance=100)),
    Page(
        state=State(balance=100),
        content=[
            "How much would you like to withdraw?",
            TextBox(name="amount", default_value=10),
            Button(text="Withdraw", url="/finish_withdraw"),
            Button(text="Cancel", url="/"),
        ],
    ),
)

# Check that the finish_withdraw updates the state correctly
assert_equal(
    finish_withdraw(State(balance=100), 10),
    Page(
        state=State(balance=90),
        content=[
            "Your current balance is:",
            "90",
            Button(text="Withdraw", url="/start_withdraw"),
            Button(text="Deposit", url="/start_deposit"),
        ],
    ),
)

# Check that the start_deposit page renders correctly
assert_equal(
    start_deposit(State(balance=90)),
    Page(
        state=State(balance=90),
        content=[
            "How much would you like to deposit?",
            TextBox(name="amount", default_value=10),
            Button(text="Deposit", url="/finish_deposit"),
            Button(text="Cancel", url="/"),
        ],
    ),
)

# Check that the finish_deposit updates the state correctly
assert_equal(
    finish_deposit(State(balance=90), 20),
    Page(
        state=State(balance=110),
        content=[
            "Your current balance is:",
            "110",
            Button(text="Withdraw", url="/start_withdraw"),
            Button(text="Deposit", url="/start_deposit"),
        ],
    ),
)

# Another check for finishing the deposit
assert_equal(
    finish_deposit(State(balance=100), 20),
    Page(
        state=State(balance=120),
        content=[
            "Your current balance is:",
            "120",
            Button(text="Withdraw", url="/start_withdraw"),
            Button(text="Deposit", url="/start_deposit"),
        ],
    ),
)


start_server(State(100))
