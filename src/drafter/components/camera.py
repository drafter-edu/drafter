"""Camera component for capturing photos from the user's webcam.

Provides the :class:`Camera` component and :class:`Photo` dataclass for
handling browser camera (getUserMedia) integration with form-based
workflows.

The Python side only describes the component: it renders as a
``<drafter-camera>`` custom element whose behavior (permission workflow,
live preview, photo capture) is implemented in js/src/components/camera.tsx.
Like :class:`~drafter.components.geolocation.CurrentLocation` and
:class:`~drafter.components.audio.AudioRecorder`, the element keeps a
hidden form field named after the component updated with a JSON-encoded
:class:`Photo`; the converter registered below turns that payload into a
:class:`Photo` when the matching route parameter is annotated with it.
Failures become ``status`` values rather than exceptions, so routes can
inspect problems without try/except.
"""

from dataclasses import dataclass

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
)
from drafter.components.utilities.registry import (
    COMPONENT_CONTRACT_REGISTRY,
)
from drafter.components.utilities.validation import validate_parameter_name
from drafter.data.errors import StudentFacingError

FACING_MODES = ("user", "environment")
"""Which camera a `Camera` prefers: "user" (front/selfie) or
"environment" (rear/world-facing)."""


@dataclass(repr=False)
class Camera(Component):
    """Captures photos from the user's webcam and submits them with the form.

    This component follows the same permission workflow as
    :class:`~drafter.components.geolocation.CurrentLocation`: it shows an
    "Enable camera" prompt, and once permission is granted it displays a
    live preview with a "Take photo" button. The captured photo is kept in
    a hidden form field (named ``name``), so a route parameter with the
    same name receives the converted value: annotate it as
    :class:`~drafter.data.images.Picture` (or ``bytes``) to get just the
    image, or as :class:`Photo` to get the full envelope including the
    permission ``status``. Display a photo by passing the `Picture` (or
    the Photo's ``data_url``) to :class:`~drafter.components.images.Image`.

    Visual states:
    - prompt: Shows "Enable camera" button when permission not yet requested
    - pending: Shows spinner while waiting for permission
    - live: Shows the live preview with "Take photo" and "Stop" buttons
    - granted: Shows the captured photo with a "Retake" button
    - denied: Shows "Camera access denied" message
    - error: Shows error message if the camera fails
    - unavailable: Shows message if the camera API is not supported

    After a photo is taken the camera stream is stopped (turning off the
    camera light); "Retake" starts it again.

    Attributes:
        name: The form field name that will contain the Photo data.
        width: Requested video width in pixels. Defaults to 640.
        height: Requested video height in pixels. Defaults to 480.
        facing: Which camera to prefer: "user" (front/selfie) or
            "environment" (rear). Defaults to "user".
        mirror: Whether to mirror the live preview horizontally, like a
            selfie mirror; the captured photo is never mirrored.
            Defaults to True.
        show: Whether to display the camera UI. Defaults to True.
        on_capture: Function or URL to call when a photo is captured.
        on_denied: Function or URL to call when camera permission is denied.
        on_error: Function or URL to call when the camera fails.
    """

    name: str
    width: int = 640
    height: int = 480
    facing: str = "user"
    mirror: bool = True
    show: bool = True
    on_capture: UrlOrFunction | None = None
    on_denied: UrlOrFunction | None = None
    on_error: UrlOrFunction | None = None

    tag = "drafter-camera"

    KNOWN_ATTRS = [
        "name",
        "width",
        "height",
        "facing",
        "mirror",
        "show",
    ]
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("width", "keyword", 640),
        ComponentArgument("height", "keyword", 480),
        ComponentArgument("facing", "keyword", "user"),
        ComponentArgument("mirror", "keyword", True),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("on_capture", "keyword", None, is_event=True),
        ComponentArgument("on_denied", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["capture", "denied", "error"]

    #: What this component emits: the JS implementation (js/src/components/
    #: camera.tsx) must match this contract, and the router uses it to
    #: reason about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Camera",
        html_tag="drafter-camera",
        emitted_events=[
            EventPayloadSpec(
                event_name="capture",
                fields=[
                    EventPayloadFieldSpec(
                        "width", int, "Width of the captured photo in pixels."
                    ),
                    EventPayloadFieldSpec(
                        "height", int, "Height of the captured photo in pixels."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="denied",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Always denied when permission is rejected."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the denial."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Failure state: denied, unavailable, or error."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        name: str,
        width: int = 640,
        height: int = 480,
        facing: str = "user",
        mirror: bool = True,
        show: bool = True,
        on_capture: UrlOrFunction | None = None,
        on_denied: UrlOrFunction | None = None,
        on_error: UrlOrFunction | None = None,
        **extra_settings,
    ):
        """Initialize the Camera component.

        Args:
            name: The form field name for the Photo data.
            width: Requested video width in pixels.
            height: Requested video height in pixels.
            facing: "user" (front/selfie) or "environment" (rear).
            mirror: Whether to mirror the live preview horizontally.
            show: Whether to display the camera UI.
            on_capture: Function or URL to call when a photo is captured.
            on_denied: Function or URL to call when permission is denied.
            on_error: Function or URL to call when the camera fails.
            **extra_settings: Additional HTML attributes.

        Raises:
            StudentFacingError: If facing is not a supported mode, or if
                width or height is not a positive whole number.
        """
        validate_parameter_name(name, "Camera")
        if facing not in FACING_MODES:
            raise StudentFacingError(
                f"Camera facing must be one of"
                f" {', '.join(repr(mode) for mode in FACING_MODES)},"
                f" not {facing!r}.",
                friendly=(
                    f"The facing argument you gave Camera was {facing!r}, "
                    "but a camera can only face 'user' (the front, selfie "
                    "camera) or 'environment' (the rear camera)."
                ),
                steps=(
                    "Use facing='user' for the front/selfie camera.",
                    "Use facing='environment' for the rear camera.",
                    "Check the spelling of the facing argument.",
                ),
            )
        for dimension_name, dimension in (("width", width), ("height", height)):
            if (
                not isinstance(dimension, int)
                or isinstance(dimension, bool)
                or dimension <= 0
            ):
                raise StudentFacingError(
                    f"Camera {dimension_name} must be a positive number of"
                    f" pixels, not {dimension!r}.",
                    friendly=(
                        f"The {dimension_name} argument you gave Camera was "
                        f"{dimension!r}, but it needs to be a whole number "
                        "of pixels bigger than zero."
                    ),
                    steps=(
                        f"Give {dimension_name} a whole number, like "
                        f"{dimension_name}=480.",
                        f"Or leave out {dimension_name} to use the default size.",
                    ),
                )
        self.name = name
        self.width = width
        self.height = height
        self.facing = facing
        self.mirror = mirror
        self.show = show
        self.on_capture = on_capture
        self.on_denied = on_denied
        self.on_error = on_error
        self.extra_settings = extra_settings


COMPONENT_CONTRACT_REGISTRY.register(Camera.CONTRACT)
