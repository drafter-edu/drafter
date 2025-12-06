from drafter import *

hide_debug_information()
set_website_framed(False)

set_website_style("sakura")


@route
def index(state: str) -> Page:

    return Page(
        state,
        [
            Header("Virtual Pet Cacus"),
            Image("soon-128.png"),
            Div(
                "Welcome to your virtual pet cactus! Take care of it and watch it grow.",
                Image("soon-128.png"),
                Text(
                    """
This is your very own virtual pet cactus. You can water it, give it sunlight, 
and even talk to it! Make sure to check on it regularly to keep it happy and healthy.
"""
                ),
                Button("Adopt a Cactus", "adopt_cactus"),
                style_display="flex",
                style_flex_direction="column",
                style_align_items="center",
            ),
        ],
    )


start_server("Nothing",
             cdn_skulpt_drafter="http://localhost:8081/skulpt-drafter.js")
