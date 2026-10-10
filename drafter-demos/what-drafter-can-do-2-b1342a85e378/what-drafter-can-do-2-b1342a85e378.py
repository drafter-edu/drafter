from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Password Strength"),
        TextBox("password", "", on_input="judge"),
        "\n",
        Output("verdict", ["Type a password."])
    ])


@route
def judge(password: str) -> Fragment:
    if len(password) < 6:
        verdict = "Too short."
    elif password.lower() == password:
        verdict = "Add a capital letter."
    else:
        verdict = "Strong enough for a cat."
    return Fragment([verdict], target="#verdict")


start_server()
