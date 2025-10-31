"""
SVG Shape Components

This module provides simple shape components for creating SVG graphics.
All coordinates and sizes are in pixels by default.
"""

from dataclasses import dataclass
from typing import Optional, List, Union
from drafter.components.page_content import Component


@dataclass
class SvgRectangle(Component):
    """
    Create a rectangle in an SVG.
    
    Args:
        x: X-coordinate of the top-left corner
        y: Y-coordinate of the top-left corner
        width: Width of the rectangle
        height: Height of the rectangle
        fill: Fill color (e.g., "red", "#FF0000", "rgb(255,0,0)")
        stroke: Outline color
        stroke_width: Width of the outline
        **kwargs: Additional SVG attributes
    
    Example:
        SvgRectangle(10, 20, 100, 50, fill="blue", stroke="black", stroke_width=2)
    """
    
    x: float
    y: float
    width: float
    height: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        **kwargs
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [f'x="{self.x}"', f'y="{self.y}"', f'width="{self.width}"', f'height="{self.height}"']
        
        if self.fill is not None:
            attrs.append(f'fill="{self.fill}"')
        if self.stroke is not None:
            attrs.append(f'stroke="{self.stroke}"')
        if self.stroke_width is not None:
            attrs.append(f'stroke-width="{self.stroke_width}"')
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<rect {" ".join(attrs)} />'


@dataclass
class SvgCircle(Component):
    """
    Create a circle in an SVG.
    
    Args:
        cx: X-coordinate of the center
        cy: Y-coordinate of the center
        r: Radius of the circle
        fill: Fill color (e.g., "red", "#FF0000", "rgb(255,0,0)")
        stroke: Outline color
        stroke_width: Width of the outline
        **kwargs: Additional SVG attributes
    
    Example:
        SvgCircle(100, 100, 50, fill="green", stroke="black", stroke_width=2)
    """
    
    cx: float
    cy: float
    r: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    
    def __init__(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        **kwargs
    ):
        self.cx = cx
        self.cy = cy
        self.r = r
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [f'cx="{self.cx}"', f'cy="{self.cy}"', f'r="{self.r}"']
        
        if self.fill is not None:
            attrs.append(f'fill="{self.fill}"')
        if self.stroke is not None:
            attrs.append(f'stroke="{self.stroke}"')
        if self.stroke_width is not None:
            attrs.append(f'stroke-width="{self.stroke_width}"')
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<circle {" ".join(attrs)} />'


@dataclass
class SvgEllipse(Component):
    """
    Create an ellipse in an SVG.
    
    Args:
        cx: X-coordinate of the center
        cy: Y-coordinate of the center
        rx: Horizontal radius
        ry: Vertical radius
        fill: Fill color (e.g., "red", "#FF0000", "rgb(255,0,0)")
        stroke: Outline color
        stroke_width: Width of the outline
        **kwargs: Additional SVG attributes
    
    Example:
        SvgEllipse(100, 100, 80, 40, fill="yellow", stroke="black")
    """
    
    cx: float
    cy: float
    rx: float
    ry: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    
    def __init__(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        **kwargs
    ):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [f'cx="{self.cx}"', f'cy="{self.cy}"', f'rx="{self.rx}"', f'ry="{self.ry}"']
        
        if self.fill is not None:
            attrs.append(f'fill="{self.fill}"')
        if self.stroke is not None:
            attrs.append(f'stroke="{self.stroke}"')
        if self.stroke_width is not None:
            attrs.append(f'stroke-width="{self.stroke_width}"')
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<ellipse {" ".join(attrs)} />'


@dataclass
class SvgLine(Component):
    """
    Create a line in an SVG.
    
    Args:
        x1: X-coordinate of the start point
        y1: Y-coordinate of the start point
        x2: X-coordinate of the end point
        y2: Y-coordinate of the end point
        stroke: Line color (default: "black")
        stroke_width: Width of the line (default: 1)
        **kwargs: Additional SVG attributes
    
    Example:
        SvgLine(10, 10, 100, 100, stroke="red", stroke_width=3)
    """
    
    x1: float
    y1: float
    x2: float
    y2: float
    stroke: str = "black"
    stroke_width: float = 1
    
    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = "black",
        stroke_width: float = 1,
        **kwargs
    ):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [
            f'x1="{self.x1}"',
            f'y1="{self.y1}"',
            f'x2="{self.x2}"',
            f'y2="{self.y2}"',
            f'stroke="{self.stroke}"',
            f'stroke-width="{self.stroke_width}"',
        ]
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<line {" ".join(attrs)} />'


@dataclass
class SvgPolygon(Component):
    """
    Create a polygon (closed shape with straight sides) in an SVG.
    
    Note: Polygons are closed shapes, so they have a default fill of "black". 
    If you want an unfilled polygon, set fill="none".
    
    Args:
        points: List of (x, y) coordinate tuples or a string of points
        fill: Fill color (default: "black" for closed shapes)
        stroke: Outline color
        stroke_width: Width of the outline
        **kwargs: Additional SVG attributes
    
    Example:
        # Create a triangle
        SvgPolygon([(50, 10), (90, 90), (10, 90)], fill="lime", stroke="purple", stroke_width=2)
    """
    
    points: Union[List[tuple], str]
    fill: str = "black"
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    
    def __init__(
        self,
        points: Union[List[tuple], str],
        fill: str = "black",
        stroke: Optional[str] = None,
        stroke_width: Optional[float] = None,
        **kwargs
    ):
        self.points = points
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def _format_points(self) -> str:
        """Convert points list to SVG points string format."""
        if isinstance(self.points, str):
            return self.points
        return ' '.join(f'{x},{y}' for x, y in self.points)
    
    def __str__(self) -> str:
        points_str = self._format_points()
        attrs = [f'points="{points_str}"', f'fill="{self.fill}"']
        
        if self.stroke is not None:
            attrs.append(f'stroke="{self.stroke}"')
        if self.stroke_width is not None:
            attrs.append(f'stroke-width="{self.stroke_width}"')
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<polygon {" ".join(attrs)} />'


@dataclass
class SvgPolyline(Component):
    """
    Create a polyline (open shape with connected straight lines) in an SVG.
    
    Args:
        points: List of (x, y) coordinate tuples or a string of points
        fill: Fill color (default: "none" for open shape)
        stroke: Line color (default: "black")
        stroke_width: Width of the line (default: 1)
        **kwargs: Additional SVG attributes
    
    Example:
        # Create a zigzag line
        SvgPolyline([(10, 10), (50, 50), (90, 10)], stroke="blue", stroke_width=2)
    """
    
    points: Union[List[tuple], str]
    fill: str = "none"
    stroke: str = "black"
    stroke_width: float = 1
    
    def __init__(
        self,
        points: Union[List[tuple], str],
        fill: str = "none",
        stroke: str = "black",
        stroke_width: float = 1,
        **kwargs
    ):
        self.points = points
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def _format_points(self) -> str:
        """Convert points list to SVG points string format."""
        if isinstance(self.points, str):
            return self.points
        return ' '.join(f'{x},{y}' for x, y in self.points)
    
    def __str__(self) -> str:
        points_str = self._format_points()
        attrs = [
            f'points="{points_str}"',
            f'fill="{self.fill}"',
            f'stroke="{self.stroke}"',
            f'stroke-width="{self.stroke_width}"',
        ]
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<polyline {" ".join(attrs)} />'


@dataclass
class SvgPath(Component):
    """
    Create a path (complex shape) in an SVG using path commands.
    
    The path is defined using a series of commands. This is an advanced feature
    for creating complex shapes like curves and arcs.
    
    Args:
        d: Path data string using SVG path commands
            M = moveto, L = lineto, C = curveto, Z = closepath, etc.
        fill: Fill color (default: "none")
        stroke: Line color (default: "black")
        stroke_width: Width of the line (default: 1)
        **kwargs: Additional SVG attributes
    
    Example:
        # Draw a simple curve
        SvgPath("M 10 10 L 50 50 L 90 10", stroke="purple", stroke_width=2, fill="none")
    """
    
    d: str
    fill: str = "none"
    stroke: str = "black"
    stroke_width: float = 1
    
    def __init__(
        self,
        d: str,
        fill: str = "none",
        stroke: str = "black",
        stroke_width: float = 1,
        **kwargs
    ):
        self.d = d
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        attrs = [
            f'd="{self.d}"',
            f'fill="{self.fill}"',
            f'stroke="{self.stroke}"',
            f'stroke-width="{self.stroke_width}"',
        ]
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if parsed_settings:
            attrs.append(parsed_settings)
        
        return f'<path {" ".join(attrs)} />'
