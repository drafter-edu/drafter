from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            # These checkboxes are separate, and each maps to a boolean parameter
            "What foods do you like? (Boolean Checkboxes)\n",
            Label("Chicken:", "like_chicken"),
            CheckBox("like_chicken"),
            Label("Beef:", "like_beef"),
            CheckBox("like_beef"),
            Label("None of the above:", "like_none"),
            CheckBox("like_none"),
            HorizontalRule(),
            # These checkboxes are related, and map to a single list
            "What places have you been to?\n",
            Label("Places:", "places"),
            RelatedCheckBox("places", "New York"),
            Label("New York", "New York"),
            RelatedCheckBox("places", "Los Angeles"),
            Label("Los Angeles", "Los Angeles"),
            RelatedCheckBox("places", "Chicago"),
            Label("Chicago", "Chicago"),
            HorizontalRule(),
            # This select box allows the user to choose a single interest
            Label("Interests:", "interests"),
            SelectBox("interests", ["Music", "Games", "Sports", "Movies"]),
            HorizontalRule(),
            # This select box allows the user to choose multiple colors
            Label("Colors:", "colors"),
            SelectBox("colors", ["Red", "Green", "Blue"], multiple=True),
            LineBreak(),
            Button("Submit", "next/"),
        ],
    )


@route
def next(
    state: State,
    interests: str,
    colors: list[str],
    like_chicken: bool,
    like_beef: bool,
    like_none: bool,
    places: list[str],
) -> Page:
    return Page(
        state,
        [
            "Thank you for your submission!\n",
            f"You selected interests: {interests}\n",
            f"Colors: {colors}\n",
            f"Like Chicken: {like_chicken}\n",
            f"Like Beef: {like_beef}\n",
            f"Like None: {like_none}\n",
            f"Places: {places}\n",
        ],
    )


start_server(State())
