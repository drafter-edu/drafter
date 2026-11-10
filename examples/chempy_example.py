# chempy

"""A small Drafter web app that balances chemical equations using ChemPy."""

from dataclasses import dataclass

from chempy import balance_stoichiometry
from drafter import Button, Header, Page, TextBox, route, start_server


@dataclass
class State:
    reactants: str = "H2, O2"
    products: str = "H2O"
    result: str = ""
    error: str = ""


def parse_species(text: str) -> list[str]:
    """Read comma-separated chemical formulas, preserving their order."""
    species = [part.strip() for part in text.split(",")]
    if not all(species):
        raise ValueError("Enter one or more formulas, separated by commas.")
    if len(species) != len(set(species)):
        raise ValueError("Each formula may appear only once on a side.")
    return species


def format_side(species: list[str], coefficients: dict) -> str:
    """Display terms in the same order the user entered them."""
    terms = []
    for formula in species:
        coefficient = coefficients[formula]
        terms.append(formula if coefficient == 1 else f"{coefficient} {formula}")
    return " + ".join(terms)


@route
def index(state: State) -> Page:
    content = [
        Header("ChemPy Equation Balancer"),
        "Enter chemical formulas separated by commas (without coefficients).",
        "Reactants:",
        TextBox("reactants", state.reactants),
        "Products:",
        TextBox("products", state.products),
        Button("Balance equation", "balance"),
    ]
    if state.result:
        content.extend([Header("Balanced equation"), state.result])
    if state.error:
        content.append("Error: " + state.error)
    return Page(state, content)


@route
def balance(state: State, reactants: str, products: str) -> Page:
    state.reactants = reactants
    state.products = products
    state.result = ""
    state.error = ""

    try:
        left = parse_species(reactants)
        right = parse_species(products)
        if set(left) & set(right):
            raise ValueError("A formula cannot appear on both sides of the equation.")
        # A determined or minimal positive integer solution, where possible.
        lhs, rhs = balance_stoichiometry(set(left), set(right))
        state.result = f"{format_side(left, lhs)} -> {format_side(right, rhs)}"
    except Exception as exc:
        state.error = str(exc) or "The equation could not be balanced."

    return index(state)


start_server(State())
