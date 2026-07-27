"""Media components for embedding audio, video, and graphics.

Defines `Audio` and `Video` (HTML5 media elements with deferred autoplay
and optional persistence across page transitions), plus `Canvas` and
`SVG` for drawing graphics.
"""

from dataclasses import dataclass

from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan

AUTOPLAY_WRAPPER_TAG = "drafter-media"
"""Custom element (js/src/components/media.tsx) that defers autoplay until the drafter-page-loaded event fires."""


def _plan_with_deferred_autoplay(component: Component, context) -> RenderPlan:
    """Plan a media tag, deferring autoplay to the page-loaded event.

    A native ``autoplay`` attribute starts playback as soon as the element
    is inserted into the DOM, which happens while the new page's HTML is
    still loading. Instead, the ``autoplay`` attribute is moved onto a
    ``<drafter-media>`` wrapper element, whose client-side implementation
    starts playback when the drafter page-loaded event fires.
    """
    attributes = component.get_attributes(context)
    autoplay = attributes.pop("autoplay", False)
    inner = component._plan_tag(context, attributes=attributes)
    if not autoplay:
        return inner
    return RenderPlan(
        kind="tag",
        tag_name=AUTOPLAY_WRAPPER_TAG,
        attributes={"autoplay": True},
        children=[inner],
        known_attributes=["autoplay"],
    )


@dataclass(repr=False)
class Audio(Component):
    """Renders an HTML5 audio element for embedding sound content.

    Note that this renders an element in the page. For audio control
    that plays outside of the page context (e.g., background music),
    consider using the play_audio function from drafter.media.audio.

    Attributes:
        src: Source URL of the audio file.
        controls: Whether to display audio controls.
        autoplay: Whether to autoplay the audio.
        loop: Whether to loop the audio.
        muted: Whether to mute the audio.
        persistent: Whether the audio keeps playing across page transitions.
        tag: The HTML tag name, always 'audio'.
    """

    src: str
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool
    persistent: bool

    tag = "audio"
    PERSISTABLE = True
    KNOWN_ATTRS = ["src", "controls", "autoplay", "loop", "muted"]
    ARGUMENTS = [
        ComponentArgument("src"),
        ComponentArgument("controls", kind="keyword", default_value=True),
        ComponentArgument("autoplay", kind="keyword", default_value=False),
        ComponentArgument("loop", kind="keyword", default_value=False),
        ComponentArgument("muted", kind="keyword", default_value=False),
        ComponentArgument("persistent", kind="keyword", default_value=False),
    ]

    DEFAULT_ATTRS = {"controls": True}

    def __init__(
        self,
        src: str,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        muted: bool = False,
        persistent: bool = False,
        **kwargs,
    ):
        """Initialize audio component.

        Args:
            src: Source URL of the audio file.
            controls: Whether to display audio controls. Defaults to True.
            autoplay: Whether to autoplay the audio. Playback starts once
                the page has finished loading (the drafter page-loaded
                event), not while the page is still being inserted.
                Defaults to False.
            loop: Whether to loop the audio. Defaults to False.
            muted: Whether to mute the audio. Defaults to False.
            persistent: Whether the audio keeps playing across page
                transitions (e.g., background music). Note that browsers
                require a user interaction before audio can start playing.
                Defaults to False.
            **kwargs: Additional HTML attributes and styles.
        """
        self.src = src
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.persistent = persistent
        self.extra_settings = kwargs

    def plan(self, context) -> RenderPlan:
        """Plan the audio element, deferring any autoplay.

        Args:
            context: Rendering context.

        Returns:
            The audio tag RenderPlan, wrapped in a `drafter-media` element
            when autoplay is requested.
        """
        return _plan_with_deferred_autoplay(self, context)


@dataclass(repr=False)
class Video(Component):
    """Renders an HTML5 video element for playing video files.

    Attributes:
        src: URL or path to the video file.
        width: Optional width in pixels.
        height: Optional height in pixels.
        controls: Whether to show playback controls.
        autoplay: Whether to autoplay the video.
        loop: Whether to loop the video.
        muted: Whether to mute the video.
        persistent: Whether the video keeps playing across page transitions.
        tag: The HTML tag name, always 'video'.
    """

    tag = "video"
    src: str
    width: int | None
    height: int | None
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool
    persistent: bool
    PERSISTABLE = True
    KNOWN_ATTRS = ["src", "width", "height", "controls", "autoplay", "loop", "muted"]
    ARGUMENTS = [
        ComponentArgument("src"),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
        ComponentArgument("controls", kind="keyword", default_value=True),
        ComponentArgument("autoplay", kind="keyword", default_value=False),
        ComponentArgument("loop", kind="keyword", default_value=False),
        ComponentArgument("muted", kind="keyword", default_value=False),
        ComponentArgument("persistent", kind="keyword", default_value=False),
    ]

    DEFAULT_ATTRS = {"controls": True}

    def __init__(
        self,
        src: str,
        width: int | None = None,
        height: int | None = None,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        muted: bool = False,
        persistent: bool = False,
        **kwargs,
    ):
        """Initialize video component.

        Args:
            src: URL or path to the video file.
            width: Optional width in pixels.
            height: Optional height in pixels.
            controls: Whether to show playback controls. Defaults to True.
            autoplay: Whether to autoplay the video. Playback starts once
                the page has finished loading (the drafter page-loaded
                event), not while the page is still being inserted.
                Defaults to False.
            loop: Whether to loop the video. Defaults to False.
            muted: Whether to mute the video. Defaults to False.
            persistent: Whether the video keeps playing across page
                transitions. Note that browsers require a user interaction
                before unmuted media can start playing. Defaults to False.
            **kwargs: Additional HTML attributes and styles.
        """
        self.src = src
        self.width = width
        self.height = height
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.persistent = persistent
        self.extra_settings = kwargs

    def plan(self, context) -> RenderPlan:
        """Plan the video element, deferring any autoplay.

        Args:
            context: Rendering context.

        Returns:
            The video tag RenderPlan, wrapped in a `drafter-media` element
            when autoplay is requested.
        """
        return _plan_with_deferred_autoplay(self, context)


@dataclass(repr=False)
class Canvas(Component):
    """Renders an HTML5 canvas element for drawing graphics via JavaScript.

    Attributes:
        canvas_id: ID attribute for the canvas element.
        width: Width in pixels.
        height: Height in pixels.
        tag: The HTML tag name, always 'canvas'.
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
        """Initialize canvas component.

        Args:
            canvas_id: ID attribute for the canvas element.
            width: Width in pixels. Defaults to 300.
            height: Height in pixels. Defaults to 150.
            **kwargs: Additional HTML attributes and styles.
        """
        self.canvas_id = canvas_id
        self.width = width
        self.height = height
        self.extra_settings = kwargs


@dataclass(repr=False)
class SVG(Component):
    """
    SVG element wrapper for embedding SVG graphics.

    Attributes:
        content: SVG child elements or raw SVG string.
        width: Optional width attribute.
        height: Optional height attribute.
        viewBox: Optional viewBox attribute (e.g., '0 0 100 100').
        tag: The HTML tag name, always 'svg'.
    """

    content: str
    width: int | None
    height: int | None
    viewBox: str | None
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
        width: int | None = None,
        height: int | None = None,
        viewBox: str | None = None,
        **kwargs,
    ):
        """Initialize SVG component.

        Args:
            content (str): SVG child elements or raw SVG string.
            width (Optional[int]): Optional width attribute.
            height (Optional[int]): Optional height attribute.
            viewBox (Optional[str]): Optional viewBox attribute (e.g., '0 0 100 100').
            **kwargs: Additional HTML attributes and styles.
        """
        self.content = content
        self.width = width
        self.height = height
        self.viewBox = viewBox
        self.extra_settings = kwargs

    def get_children(self, context) -> list:
        """Get the SVG's child content.

        Args:
            context: Rendering context.

        Returns:
            A single raw RenderPlan when the content is a string;
            otherwise the content unchanged.
        """
        if isinstance(self.content, str):
            return [RenderPlan(kind="raw", raw_html=self.content)]
        return self.content
