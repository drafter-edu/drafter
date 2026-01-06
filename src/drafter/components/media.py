from dataclasses import dataclass
from typing import Optional
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan


@dataclass(repr=False)
class Audio(Component):
    """
    HTML5 audio element for embedding sound content.

    Note that this renders an element in the page. For audio control
    that plays outside of the page context (e.g., background music),
    consider using the play_audio function from drafter.media.audio.

    Args:
        src: Source URL of the audio file.
        controls: Whether to display audio controls (default: True).
        autoplay: Whether to autoplay the audio (default: False).
        loop: Whether to loop the audio (default: False).
        muted: Whether to mute the audio (default: False).
        **kwargs: Additional HTML attributes.

    Examples:
        Audio("path/to/audio.mp3")
        Audio("path/to/audio.ogg", controls=False, autoplay=True)
    """

    src: str
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool

    tag = "audio"
    KNOWN_ATTRS = ["src", "controls", "autoplay", "loop", "muted"]
    ARGUMENTS = [
        ComponentArgument("src"),
        ComponentArgument("controls", kind="keyword", default_value=True),
        ComponentArgument("autoplay", kind="keyword", default_value=False),
        ComponentArgument("loop", kind="keyword", default_value=False),
        ComponentArgument("muted", kind="keyword", default_value=False),
    ]

    DEFAULT_ATTRS = {"controls": True}

    def __init__(
        self,
        src: str,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        muted: bool = False,
        **kwargs,
    ):
        self.src = src
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.extra_settings = kwargs


@dataclass(repr=False)
class Video(Component):
    """
    HTML5 Video element for playing video files.

    Args:
        src: URL or path to the video file
        width: Optional width in pixels
        height: Optional height in pixels
        controls: Whether to show playback controls (default: True)
        autoplay: Whether to autoplay the video (default: False)
        loop: Whether to loop the video (default: False)
        muted: Whether to mute the video (default: False)
        **kwargs: Additional HTML attributes and styles

    Example:
        Video("video/tutorial.mp4")
        Video("video/demo.mp4", width=640, height=480, autoplay=True)
    """

    tag = "video"
    src: str
    width: Optional[int]
    height: Optional[int]
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool
    KNOWN_ATTRS = ["src", "width", "height", "controls", "autoplay", "loop", "muted"]
    ARGUMENTS = [
        ComponentArgument("src"),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
        ComponentArgument("controls", kind="keyword", default_value=True),
        ComponentArgument("autoplay", kind="keyword", default_value=False),
        ComponentArgument("loop", kind="keyword", default_value=False),
        ComponentArgument("muted", kind="keyword", default_value=False),
    ]

    DEFAULT_ATTRS = {"controls": True}

    def __init__(
        self,
        src: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        muted: bool = False,
        **kwargs,
    ):
        self.src = src
        self.width = width
        self.height = height
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.extra_settings = kwargs


@dataclass(repr=False)
class Canvas(Component):
    """
    HTML5 Canvas element for drawing graphics via JavaScript.

    Args:
        canvas_id: ID attribute for the canvas element
        width: Width in pixels (default: 300)
        height: Height in pixels (default: 150)
        **kwargs: Additional HTML attributes and styles

    Example:
        Canvas("myCanvas", width=640, height=480)
        Canvas("drawArea", width=800, height=600, style_border="1px solid black")
    """

    canvas_id: str
    width: int
    height: int
    tag = "canvas"
    KNOWN_ATTRS = ["id", "width", "height"]
    RENAME_ATTRS = {"canvas_id": "id"}
    DEFAULT_ATTRS = {"width": 300, "height": 150}

    ARGUMENTS = [
        ComponentArgument("canvas_id"),
        ComponentArgument("width", kind="keyword", default_value=300),
        ComponentArgument("height", kind="keyword", default_value=150),
    ]

    def __init__(self, canvas_id: str, width: int = 300, height: int = 150, **kwargs):
        self.canvas_id = canvas_id
        self.width = width
        self.height = height
        self.extra_settings = kwargs


@dataclass(repr=False)
class SVG(Component):
    """
    SVG element wrapper for embedding SVG graphics.

    Args:
        content: List of SVG child elements/components or raw SVG string
        width: Optional width attribute
        height: Optional height attribute
        viewBox: Optional viewBox attribute (e.g., "0 0 100 100")
        **kwargs: Additional HTML attributes and styles

    Example:
        SVG('<circle cx="50" cy="50" r="40" fill="red"/>', width=100, height=100)
        SVG('<rect width="100" height="100" fill="blue"/>', viewBox="0 0 100 100")
    """

    content: str
    width: Optional[int]
    height: Optional[int]
    viewBox: Optional[str]
    tag = "svg"
    KNOWN_ATTRS = ["width", "height", "viewBox"]

    ARGUMENTS = [
        ComponentArgument("content", is_content=True),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
        ComponentArgument("viewBox", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        content: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        viewBox: Optional[str] = None,
        **kwargs,
    ):
        self.content = content
        self.width = width
        self.height = height
        self.viewBox = viewBox
        self.extra_settings = kwargs

    def get_children(self, context) -> list:
        if isinstance(self.content, str):
            return [RenderPlan(kind="raw", raw_html=self.content)]
        return self.content
