from drafter import *
from drafter.payloads.target import Target


@dataclass
class State:
    page_count: int
    id_count: int
    class_count: int
    secret_count: int


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Payload Type Examples"),
            Paragraph("This page demonstrates different payload types."),
            Row(
                Button("Update Page Count", update_page_count),
            ),
            Row(
                Button("Update Fragment by ID", update_fragment_by_id),
                Span("Specific Output:", Output("output_by_id", str(state.id_count))),
            ),
            Row(
                Button("Update Fragment by Class", update_fragment_by_class),
                Span(
                    "Class 1: ",
                    Output(
                        "output_by_class_1",
                        str(state.class_count),
                        classes="output_by_class",
                    ),
                    Output(
                        "output_by_class_2",
                        str(state.class_count),
                        classes="output_by_class",
                    ),
                ),
            ),
            Row(
                Button("Update Secretly (No Visual Change)", update_secretly),
                Span("Secret Count (Only in State):", Output("secret_count_output", str(state.secret_count))),
            )
        ],
    )


@route
def update_page_count(state: State) -> Page:
    state.page_count += 1
    return Page(
        state,
        [
            Header("Regular Page Update"),
            Paragraph(f"The page_count is now: {state.page_count}"),
            Button("Back to Index", index),
        ],
    )


@route
def update_fragment_by_id(state: State) -> Fragment:
    state.id_count += 1
    return Fragment(
        state,
        str(state.id_count),
        target=Target(id="output_by_id", replace=False),
    )


@route
def update_fragment_by_class(state: State) -> Fragment:
    state.class_count += 1
    return Fragment(
        state,
        str(state.class_count),
        target=".output_by_class",
    )


@route
def update_secretly(state: State) -> Update:
    state.secret_count += 1
    return Update(state)


start_server(State(0, 0, 0, 0))