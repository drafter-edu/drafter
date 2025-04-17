from drafter import *
from bakery import assert_equal


@route
def index(state) -> Page:
    """
    In this version, the textboxes are on the front page, a there's a button to
    go to the page that actually adds the values together. Then, the bottom shows the latest
    result.
    """
    return Page(state, [
        "What is the first number?",
        TextBox("first", state["first_number"]),
        "What is the second number?",
        TextBox("second", state["second_number"]),
        Button("Add", add_page),
        "The result is",
        state["result"]
    ])


@route
def add_page(state, first: str, second: str) -> Page:
    """
    This is the page with the actual logic. The first and second textboxes values are sent here and
    stored in the state.
    If they are both composed of digits, then their sum is calculated. Otherwise, an error is stored in the result.
    Finally, we reuse the logic for showing the index page.
    """
    state["first_number"] = first
    state["second_number"] = second

    if first.isdigit() and second.isdigit():
        state["result"] = str(int(first) + int(second))
    else:
        state["result"] = "Invalid numbers!"

    return index(state)


# Test that the front page loads normally
# assert_equal(index(State("0", "0", "")),
#              Page(State("0", "0", ''),
#                   ['What is the first number?',
#                    TextBox('first', "0"),
#                    'What is the second number?',
#                    TextBox('second', "0"),
#                    Button('Add', add_page),
#                    'The result is',
#                    '']))
#
# # Test that the add page works with zeroes
# assert_equal(add_page(State("0", "0", ""), "0", "0"),
#              Page(State("0", "0", '0'),
#                   ['What is the first number?',
#                    TextBox('first', "0"),
#                    'What is the second number?',
#                    TextBox('second', '0'),
#                    Button('Add', add_page),
#                    'The result is',
#                    '0']))
#
# # Test that the add page can take more interesting numbers
# # Keyword parameters can be used to make the values more explicit.
# # Copying the body generated from the page may introduce them!
# assert_equal(add_page(State("0", "0", ""), "5", "3"),
#              Page(state=State(first_number="5", second_number="3", result='8'),
#                   content=['What is the first number?',
#                            TextBox(name='first', default_value="5"),
#                            'What is the second number?',
#                            TextBox(name='second', default_value="3"),
#                            Button(text='Add', url=add_page),
#                            'The result is',
#                            '8']))
#
# # Test that the add page can take more interesting numbers
# # Keyword parameters can be used to make the values more explicit.
# # Copying the body generated from the page may introduce them!
# assert_equal(add_page(State("0", "0", ""), "five", "three"),
#              Page(state=State(first_number="five", second_number="three", result='Invalid numbers!'),
#                   content=['What is the first number?',
#                            TextBox(name='first', default_value="five"),
#                            'What is the second number?',
#                            TextBox(name='second', default_value="three"),
#                            Button(text='Add', url=add_page),
#                            'The result is',
#                            'Invalid numbers!']))

# Default state for this application is two zeroes and no result.
start_server({"first_number": "0", "second_number": "0", "result": ""})
