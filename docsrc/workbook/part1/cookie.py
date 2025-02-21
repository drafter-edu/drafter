"""
# Cookie Clicker

Click the cookie to get more cookies!
"""
from drafter import *
from bakery import assert_equal
from dataclasses import dataclass


@dataclass
class State:
    """
    The state of the cookie clicker app.
    TODO: You will need to add a field to this dataclass to store the number of cookies.
    """


@route
def index(state: State) -> Page:
    """
    The main page of the cookie clicker app, showing how many cookies you have and a button to get more.
    TODO: You will need to implement this function.
    """


@route
def cookie(state: State) -> Page:
    """
    The route that updates the number of cookies in the state, and then redirects to the index page.
    TODO: You will need to implement this function.
    """


# These tests will help you know when your implementation is correct, and what the output looks like.

# If you open the app for the first time, you should see that you have 0 cookies.
assert_equal(
    index(State(cookies=0)),
    Page(
        state=State(cookies=0),
        # The system will accept either the string "/cookie" or the function name cookie for the url parameter!
        content=["You have 0 cookies", Button(text="🍪", url="/cookie")],
    ),
)

# If you click the cookie button, it routes to the cookie page and increases the number of cookies by one.
assert_equal(
    cookie(State(cookies=0)),
    Page(
        state=State(cookies=1),
        content=["You have 1 cookies", Button(text="🍪", url="/cookie")],
    ),
)

# This works whether you have 0 cookies or 100 cookies (which is this case).
assert_equal(
    cookie(State(cookies=100)),
    Page(
        state=State(cookies=101),
        content=["You have 101 cookies", Button(text="🍪", url="/cookie")],
    ),
)

# Actually start up the server. Notice that the initial state has 0 cookies.
start_server(State(0))
