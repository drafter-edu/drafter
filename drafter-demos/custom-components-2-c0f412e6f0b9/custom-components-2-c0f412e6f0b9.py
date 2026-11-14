from drafter import *
from drafter.components.page_content import ComponentArgument, RenderPlan
from dataclasses import dataclass


@dataclass
class State:
    applicant: str


@dataclass(repr=False)
class FieldGroup(Component):
    tag = "fieldset"
    caption: str
    content: list
    locked: bool

    ARGUMENTS = [
        ComponentArgument("caption"),
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("locked", kind="keyword", default_value=False),
    ]
    KNOWN_ATTRS = ["disabled"]
    RENAME_ATTRS = {"caption": "", "locked": "disabled"}

    def __init__(self, caption: str, *content, locked: bool = False,
                 **extra_settings):
        self.caption = caption
        self.content = list(content)
        self.locked = locked
        self.extra_settings = extra_settings

    def get_children(self, context) -> list:
        legend = RenderPlan(kind="tag", tag_name="legend",
                            children=[self.caption])
        return [legend] + self.content


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adopt Babbage"),
        "Latest applicant: " + state.applicant + "\n",
        FieldGroup(
            "Your application",
            "Your name: ",
            TextBox("visitor"),
            Button("Apply", "apply")
        ),
        FieldGroup(
            "Applications for Captain",
            "Captain the grey cat already has a home. ",
            Button("Apply", "apply"),
            locked=True
        )
    ])


@route
def apply(state: State, visitor: str) -> Page:
    state.applicant = visitor
    return index(state)


assert_has(index(State("nobody yet")),
           FieldGroup("Your application",
                      "Your name: ",
                      TextBox("visitor"),
                      Button("Apply", "apply")))
assert_state(apply(State("nobody yet"), "Grace"), State("Grace"))

start_server(State("nobody yet"))
