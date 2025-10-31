"""
SVG Text Component

This module provides a component for adding text to SVG graphics.
"""

from dataclasses import dataclass
from typing import Optional
from drafter.components.page_content import Component


@dataclass
class SvgText(Component):
    """
    Create text in an SVG.
    
    Args:
        x: X-coordinate where the text starts
        y: Y-coordinate where the text baseline sits
        text: The text content to display
        fill: Text color (default: "black")
        font_size: Size of the font in pixels (default: 16)
        font_family: Font family to use (default: "Arial")
        text_anchor: Text alignment - "start", "middle", or "end" (default: "start")
        **kwargs: Additional SVG attributes
    
    Example:
        SvgText(50, 50, "Hello, SVG!", fill="blue", font_size=24, font_family="Arial")
    """
    
    x: float
    y: float
    text: str
    fill: str = "black"
    font_size: int = 16
    font_family: str = "Arial"
    text_anchor: str = "start"
    
    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        fill: str = "black",
        font_size: int = 16,
        font_family: str = "Arial",
        text_anchor: str = "start",
        **kwargs
    ):
        self.x = x
        self.y = y
        self.text = text
        self.fill = fill
        self.font_size = font_size
        self.font_family = font_family
        self.text_anchor = text_anchor
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [
            f'x="{self.x}"',
            f'y="{self.y}"',
            f'fill="{self.fill}"',
            f'font-size="{self.font_size}"',
            f'font-family="{self.font_family}"',
            f'text-anchor="{self.text_anchor}"',
        ]
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<text {" ".join(attrs)}>{self.text}</text>'
