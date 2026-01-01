"""
Media components for audio and video elements.
"""
from dataclasses import dataclass
from typing import Optional
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
