from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Tip Calculator"),
        "Bill amount:",
        TextBox("bill", "20", on_input="recalculate"),
        "\n",
        Output("tip", ["A 20% tip would be $4.00"])
    ])


@route
def recalculate(bill: str) -> Fragment:
    if not bill.isdigit():
        return Fragment(["Enter a whole number of dollars."],
                        target="#tip")
    amount = int(bill) * 0.2
    return Fragment(["A 20% tip would be $" + str(round(amount, 2))],
                    target="#tip")


start_server()
