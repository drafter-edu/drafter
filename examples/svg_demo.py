"""
SVG Example for Drafter

This example demonstrates the SVG components available in Drafter.
It creates several pages showcasing different SVG features.
"""

from dataclasses import dataclass
from drafter import route, Page, start_server, Button
from drafter.components.svg import (
    Svg,
    SvgRectangle,
    SvgCircle,
    SvgEllipse,
    SvgLine,
    SvgPolygon,
    SvgPolyline,
    SvgPath,
    SvgText,
)


@dataclass
class State:
    """Simple state for the example."""
    pass


@route
def index(state: State) -> Page:
    """Main page with navigation to different SVG examples."""
    return Page(state, [
        "<h1>SVG Examples in Drafter</h1>",
        "<p>Choose an example to explore:</p>",
        Button("Basic Shapes", basic_shapes),
        Button("Complex Scene", complex_scene),
        Button("Chart Example", chart_example),
        Button("Pattern Example", pattern_example),
    ])


@route
def basic_shapes(state: State) -> Page:
    """Demonstrate basic SVG shapes."""
    svg = Svg(
        600, 400,
        # Rectangle
        SvgRectangle(20, 20, 100, 80, fill="lightblue", stroke="navy", stroke_width=2),
        SvgText(70, 120, "Rectangle", text_anchor="middle", font_size=14),
        
        # Circle
        SvgCircle(200, 60, 40, fill="lightgreen", stroke="darkgreen", stroke_width=2),
        SvgText(200, 120, "Circle", text_anchor="middle", font_size=14),
        
        # Ellipse
        SvgEllipse(340, 60, 60, 40, fill="lightyellow", stroke="orange", stroke_width=2),
        SvgText(340, 120, "Ellipse", text_anchor="middle", font_size=14),
        
        # Line
        SvgLine(450, 20, 550, 100, stroke="red", stroke_width=3),
        SvgText(500, 120, "Line", text_anchor="middle", font_size=14),
        
        # Polygon (triangle)
        SvgPolygon([(70, 160), (120, 240), (20, 240)], fill="pink", stroke="purple", stroke_width=2),
        SvgText(70, 260, "Polygon", text_anchor="middle", font_size=14),
        
        # Polyline (zigzag)
        SvgPolyline([(160, 160), (180, 200), (200, 160), (220, 200), (240, 160)], 
                    fill="none", stroke="blue", stroke_width=2),
        SvgText(200, 260, "Polyline", text_anchor="middle", font_size=14),
        
        # Path (curved)
        SvgPath("M 300 160 Q 320 200, 340 160 T 380 160", 
                fill="none", stroke="teal", stroke_width=2),
        SvgText(340, 260, "Path", text_anchor="middle", font_size=14),
    )
    
    return Page(state, [
        "<h1>Basic SVG Shapes</h1>",
        svg,
        Button("Back to Menu", index),
    ])


@route
def complex_scene(state: State) -> Page:
    """Create a more complex scene with multiple elements."""
    svg = Svg(
        500, 400,
        # Sky
        SvgRectangle(0, 0, 500, 250, fill="skyblue"),
        
        # Sun
        SvgCircle(400, 80, 40, fill="yellow"),
        
        # Clouds (simple)
        SvgCircle(100, 60, 25, fill="white"),
        SvgCircle(120, 60, 30, fill="white"),
        SvgCircle(140, 60, 25, fill="white"),
        
        # Ground
        SvgRectangle(0, 250, 500, 150, fill="green"),
        
        # House body
        SvgRectangle(150, 180, 120, 100, fill="beige", stroke="brown", stroke_width=2),
        
        # Roof
        SvgPolygon([(140, 180), (210, 130), (280, 180)], fill="darkred", stroke="brown", stroke_width=2),
        
        # Door
        SvgRectangle(190, 220, 40, 60, fill="brown"),
        
        # Windows
        SvgRectangle(165, 195, 30, 30, fill="lightblue", stroke="black", stroke_width=1),
        SvgRectangle(225, 195, 30, 30, fill="lightblue", stroke="black", stroke_width=1),
        
        # Tree
        SvgRectangle(350, 220, 20, 60, fill="saddlebrown"),
        SvgCircle(360, 210, 35, fill="darkgreen"),
        
        # Path to house
        SvgPath("M 100 280 Q 150 270, 190 280", fill="none", stroke="gray", stroke_width=3),
        
        # Label
        SvgText(250, 380, "My Dream House", fill="black", font_size=24, text_anchor="middle"),
    )
    
    return Page(state, [
        "<h1>Complex SVG Scene</h1>",
        "<p>A house scene created with SVG components</p>",
        svg,
        Button("Back to Menu", index),
    ])


@route
def chart_example(state: State) -> Page:
    """Create a simple bar chart using SVG."""
    # Sample data
    data = [("Apples", 120), ("Oranges", 80), ("Bananas", 150), ("Grapes", 90)]
    max_value = max(value for _, value in data)
    
    # Chart dimensions
    chart_width = 500
    chart_height = 300
    bar_width = 80
    margin = 50
    
    # Create SVG elements
    elements = [
        # Title
        SvgText(chart_width // 2, 30, "Fruit Sales Chart", 
                text_anchor="middle", font_size=20, fill="black"),
        
        # Y-axis
        SvgLine(margin, margin, margin, chart_height - margin, stroke="black", stroke_width=2),
        # X-axis
        SvgLine(margin, chart_height - margin, chart_width - margin, chart_height - margin, 
                stroke="black", stroke_width=2),
    ]
    
    # Add bars and labels
    colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"]
    for i, ((label, value), color) in enumerate(zip(data, colors)):
        x = margin + 40 + i * (bar_width + 20)
        bar_height = (value / max_value) * (chart_height - 2 * margin - 40)
        y = chart_height - margin - bar_height
        
        # Bar
        elements.append(
            SvgRectangle(x, y, bar_width, bar_height, fill=color, stroke="black", stroke_width=1)
        )
        
        # Value label
        elements.append(
            SvgText(x + bar_width / 2, y - 5, str(value), 
                    text_anchor="middle", font_size=12, fill="black")
        )
        
        # X-axis label
        elements.append(
            SvgText(x + bar_width / 2, chart_height - margin + 20, label, 
                    text_anchor="middle", font_size=12, fill="black")
        )
    
    svg = Svg(chart_width, chart_height, *elements)
    
    return Page(state, [
        "<h1>SVG Bar Chart Example</h1>",
        "<p>A simple data visualization using SVG</p>",
        svg,
        Button("Back to Menu", index),
    ])


@route
def pattern_example(state: State) -> Page:
    """Create a pattern using SVG shapes."""
    svg = Svg(
        400, 400,
        # Background
        SvgRectangle(0, 0, 400, 400, fill="lightgray"),
        
        # Create a grid pattern of circles
        *[
            SvgCircle(x, y, 15, fill=color, stroke="white", stroke_width=2)
            for i, x in enumerate(range(40, 400, 80))
            for j, y in enumerate(range(40, 400, 80))
            for color in [["red", "blue", "green", "yellow", "purple"][(i + j) % 5]]
        ],
        
        # Title
        SvgText(200, 30, "Color Pattern", text_anchor="middle", font_size=24, fill="black"),
    )
    
    return Page(state, [
        "<h1>SVG Pattern Example</h1>",
        "<p>A repeating pattern created with SVG circles</p>",
        svg,
        Button("Back to Menu", index),
    ])


if __name__ == "__main__":
    start_server(State())
