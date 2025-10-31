"""
SVG Components for Drafter

This module provides a simple, novice-friendly interface for creating SVG graphics
in Drafter applications. SVG (Scalable Vector Graphics) allows you to create
resolution-independent graphics that scale perfectly at any size.

Basic usage:
    from drafter import Svg, SvgCircle, SvgRectangle
    
    # Create an SVG with a circle and rectangle
    svg = Svg(
        width=200, 
        height=200,
        SvgCircle(cx=100, cy=100, r=50, fill="blue"),
        SvgRectangle(x=10, y=10, width=50, height=30, fill="red")
    )
"""

from drafter.components.svg.svg_component import Svg
from drafter.components.svg.shapes import (
    SvgRectangle,
    SvgCircle,
    SvgEllipse,
    SvgLine,
    SvgPolygon,
    SvgPolyline,
    SvgPath,
)
from drafter.components.svg.text import SvgText

__all__ = [
    "Svg",
    "SvgRectangle",
    "SvgCircle",
    "SvgEllipse",
    "SvgLine",
    "SvgPolygon",
    "SvgPolyline",
    "SvgPath",
    "SvgText",
]
