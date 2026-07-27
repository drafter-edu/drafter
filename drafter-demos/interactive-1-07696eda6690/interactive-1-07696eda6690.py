from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Pet Name Consultant"),
        "Propose a name:",
        TextBox("name", "", on_input="judge"),
        "\n",
        Output("verdict", ["The consultant awaits."])
    ])


@route
def judge(name: str) -> Fragment:
    if name == "":
        report = "The consultant awaits."
    elif len(name) > 12:
        report = "Distinguished, but hard to shout at the park."
    elif name.lower() == "captain":
        report = "Taken. The cat had it first."
    else:
        report = "'" + name + "' has promise."
    return Fragment([report], target="#verdict")


start_server()
