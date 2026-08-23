"""Showcase of the student-friendly errors for bad values in page content.

Each link on the index page goes to a route whose page content contains a
different kind of unsupported value, nested inside a component so the
problem is only found while rendering. Visit them one at a time to see the
"Page Content Problem" error message, the student-level location phrase
(e.g. "the Table at index 1, row index 0, column index 1"), and the advice
tailored to the offending value's type.
"""

from dataclasses import dataclass

from drafter import *


@dataclass
class Pet:
    name: str
    species: str


@route
def index(state: int) -> Page:
    return Page(
        state,
        [
            Header("Content Error Showcase"),
            "Each of these pages contains a different kind of bad content. "
            "Visit one to see the error message it produces, then use the "
            "'Return to Index Page' link to come back and try another.",
            BulletedList(
                [
                    Link("Dictionary in a Table cell", dict_in_table),
                    Link("Tuple in a BulletedList", tuple_in_list),
                    Link("None inside a Div (missing return)", none_in_div),
                    Link(
                        "A function used as content (missing Link)", function_as_content
                    ),
                    Link("A class instead of an instance", class_not_instance),
                    Link("A set as content", set_in_content),
                    Link("A custom object as content", custom_object),
                    Link("Deeply nested inside layout components", deeply_nested),
                    Link("Component that fails while rendering", component_plan_error),
                ]
            ),
        ],
    )


@route
def dict_in_table(state: int) -> Page:
    # The motivating case: a dictionary hiding in a table cell. The error
    # names the Table, the row, and the column instead of tbody/tr/td.
    return Page(
        state,
        [
            "Here are the pets:",
            Table(
                [
                    ["Ada", "corgi"],
                    ["Captain", {"species": "cat", "color": "grey"}],
                ],
                header=["Name", "Species"],
            ),
        ],
    )


@route
def tuple_in_list(state: int) -> Page:
    # A tuple where a list item was meant; the advice suggests using a list.
    return Page(
        state,
        [
            "Shopping list:",
            BulletedList(["apples", "bananas", ("cherries", 3)]),
        ],
    )


@route
def none_in_div(state: int) -> Page:
    # A helper that forgets to return: the classic accidental None.
    def describe_score(score: int):
        if score > 100:
            return "Amazing!"
        # ... no return for other scores

    return Page(state, [Div("Your rating: ", describe_score(50))])


@route
def function_as_content(state: int) -> Page:
    # The function itself was put on the page, instead of Link("...", index).
    return Page(state, [Div("Go back to the ", index)])


@route
def class_not_instance(state: int) -> Page:
    # Forgot the parentheses: Pet instead of Pet("Ada", "corgi").
    return Page(state, [Div("My pet: ", Pet)])


@route
def set_in_content(state: int) -> Page:
    return Page(state, [Div("Lucky numbers: ", {4, 8, 15})])


@route
def custom_object(state: int) -> Page:
    # A dataclass instance is not content by itself; the generic advice
    # suggests wrapping it in str(...).
    return Page(state, [Div("My pet: ", Pet("Babbage", "mutt"))])


@route
def deeply_nested(state: int) -> Page:
    # The bad value is buried several components deep; the location phrase
    # walks the whole way down.
    return Page(
        state,
        [
            Div(
                Header("Report", level=2),
                Row(
                    "Details:",
                    Table([["fine", "fine"], ["fine", {"oops": True}]]),
                ),
            ),
        ],
    )


@route
def component_plan_error(state: int) -> Page:
    # Components check their arguments when created, but fields can be
    # modified afterward — so DefinitionList only discovers this problem
    # while rendering. Its own friendly explanation still comes through,
    # with the location on the page appended.
    glossary = DefinitionList([("HTML", "A markup language")])
    glossary.items = [("HTML", "A markup language"), ("CSS",)]
    return Page(state, ["Glossary:", glossary])


start_server(0)
