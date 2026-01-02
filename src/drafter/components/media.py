"""
Media components for audio, video, canvas, and SVG elements.
"""
from dataclasses import dataclass
from typing import Optional, List
from drafter.components.page_content import Component


@dataclass
class Audio(Component):
    """
    HTML5 Audio element for playing audio files.
    
    Args:
        src: URL or path to the audio file
        controls: Whether to show playback controls (default: True)
        autoplay: Whether to autoplay the audio (default: False)
        loop: Whether to loop the audio (default: False)
        muted: Whether to mute the audio (default: False)
        **kwargs: Additional HTML attributes and styles
    
    Example:
        Audio("audio/song.mp3")
        Audio("audio/podcast.mp3", autoplay=True, loop=True)
    """
    src: str
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool
    
    def __init__(self, src: str, controls: bool = True, autoplay: bool = False, 
                 loop: bool = False, muted: bool = False, **kwargs):
        self.src = src
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        # Build attribute string for boolean attributes
        attrs = []
        if self.controls:
            attrs.append('controls')
        if self.autoplay:
            attrs.append('autoplay')
        if self.loop:
            attrs.append('loop')
        if self.muted:
            attrs.append('muted')
        
        attrs_str = ' '.join(attrs)
        parsed_settings = self.parse_extra_settings()
        
        # Combine all attributes
        all_attrs = ' '.join(filter(None, [attrs_str, parsed_settings]))
        if all_attrs:
            all_attrs = ' ' + all_attrs
        
        return f"<audio src='{self.src}'{all_attrs}></audio>"


@dataclass
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
    src: str
    width: Optional[int]
    height: Optional[int]
    controls: bool
    autoplay: bool
    loop: bool
    muted: bool
    
    def __init__(self, src: str, width: Optional[int] = None, height: Optional[int] = None,
                 controls: bool = True, autoplay: bool = False, 
                 loop: bool = False, muted: bool = False, **kwargs):
        self.src = src
        self.width = width
        self.height = height
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop
        self.muted = muted
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        # Build attribute string for size attributes
        size_attrs = []
        if self.width is not None:
            size_attrs.append(f'width="{self.width}"')
        if self.height is not None:
            size_attrs.append(f'height="{self.height}"')
        
        # Build attribute string for boolean attributes
        bool_attrs = []
        if self.controls:
            bool_attrs.append('controls')
        if self.autoplay:
            bool_attrs.append('autoplay')
        if self.loop:
            bool_attrs.append('loop')
        if self.muted:
            bool_attrs.append('muted')
        
        size_attrs_str = ' '.join(size_attrs)
        bool_attrs_str = ' '.join(bool_attrs)
        parsed_settings = self.parse_extra_settings()
        
        # Combine all attributes
        all_attrs = ' '.join(filter(None, [size_attrs_str, bool_attrs_str, parsed_settings]))
        if all_attrs:
            all_attrs = ' ' + all_attrs
        
        return f"<video src='{self.src}'{all_attrs}></video>"


@dataclass
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
    
    def __init__(self, canvas_id: str, width: int = 300, height: int = 150, **kwargs):
        self.canvas_id = canvas_id
        self.width = width
        self.height = height
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings()
        
        # Combine all attributes
        all_attrs = f'id="{self.canvas_id}" width="{self.width}" height="{self.height}"'
        if parsed_settings:
            all_attrs += ' ' + parsed_settings
        
        return f"<canvas {all_attrs}></canvas>"


@dataclass
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
    
    def __init__(self, content: str, width: Optional[int] = None, height: Optional[int] = None, 
                 viewBox: Optional[str] = None, **kwargs):
        self.content = content
        self.width = width
        self.height = height
        self.viewBox = viewBox
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        # Build attribute string
        attrs = []
        if self.width is not None:
            attrs.append(f'width="{self.width}"')
        if self.height is not None:
            attrs.append(f'height="{self.height}"')
        if self.viewBox is not None:
            attrs.append(f'viewBox="{self.viewBox}"')
        
        attrs_str = ' '.join(attrs)
        parsed_settings = self.parse_extra_settings()
        
        # Combine all attributes
        all_attrs = ' '.join(filter(None, [attrs_str, parsed_settings]))
        if all_attrs:
            all_attrs = ' ' + all_attrs
        
        return f"<svg{all_attrs}>{self.content}</svg>"
