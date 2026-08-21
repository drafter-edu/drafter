from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Video"),
            Camera("camera", width=300, height=120),
            Label("As Image:", "as_image"),
            CheckBox("as_image"),
            Clock(1000, "take_photo"),
            Output("details", "Wait for it..."),
        ],
    )


@route
def take_photo(state: State, camera: Photo, as_image: bool) -> Fragment:
    if camera.status == "live":
        if as_image:
            if camera.picture is not None:
                return Fragment(state, Image(camera.picture), target="#details")
        return Fragment(state, repr(camera), target="#details")
    else:
        return Fragment(state, "Camera is not live.", target="#details")


start_server(State())
