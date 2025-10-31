"""
Main SVG Container Component

The Svg class is the container for all SVG elements. All SVG shapes and text
must be placed inside an Svg container.
"""

from dataclasses import dataclass
from typing import Any, List
from drafter.components.page_content import Component


@dataclass(repr=False)
class Svg(Component):
    """
    Container component for SVG graphics.
    
    An SVG container holds all the shapes, lines, text, and other elements that
    make up your graphic. You must specify a width and height for the SVG.
    
    Args:
        width: Width of the SVG canvas in pixels
        height: Height of the SVG canvas in pixels
        *content: SVG elements to include (shapes, text, etc.)
        **kwargs: Additional SVG attributes (viewBox, preserveAspectRatio, etc.)
    
    Example:
        svg = Svg(
            200, 200,
            SvgCircle(100, 100, 50, fill="blue"),
            SvgRectangle(10, 10, 80, 40, fill="red")
        )
    """
    
    width: int
    height: int
    content: List[Any]
    extra_settings: dict
    
    def __init__(self, width: int, height: int, *content, **kwargs):
        self.width = width
        self.height = height
        self.content = list(content)
        self.extra_settings = kwargs
    
    def __repr__(self):
        content_repr = ', '.join(repr(item) for item in self.content)
        if self.extra_settings:
            return f"Svg({self.width}, {self.height}, {content_repr}, {self.extra_settings})"
        return f"Svg({self.width}, {self.height}, {content_repr})"
    
    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        content_str = ''.join(str(item) for item in self.content)
        
        return (
            f'<svg width="{self.width}" height="{self.height}" '
            f'xmlns="http://www.w3.org/2000/svg" {parsed_settings}>'
            f'{content_str}'
            f'</svg>'
        )
