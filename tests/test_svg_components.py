"""
Tests for SVG components
"""
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


def test_svg_container_basic():
    """Test basic SVG container rendering."""
    svg = Svg(200, 100)
    result = str(svg)
    assert 'width="200"' in result
    assert 'height="100"' in result
    assert 'xmlns="http://www.w3.org/2000/svg"' in result
    assert result.startswith('<svg')
    assert result.endswith('</svg>')


def test_svg_container_with_content():
    """Test SVG container with child elements."""
    circle = SvgCircle(50, 50, 25, fill="red")
    svg = Svg(100, 100, circle)
    result = str(svg)
    assert '<circle' in result
    assert 'cx="50"' in result
    assert 'fill="red"' in result


def test_svg_rectangle():
    """Test SVG rectangle rendering."""
    rect = SvgRectangle(10, 20, 100, 50, fill="blue", stroke="black", stroke_width=2)
    result = str(rect)
    assert '<rect' in result
    assert 'x="10"' in result
    assert 'y="20"' in result
    assert 'width="100"' in result
    assert 'height="50"' in result
    assert 'fill="blue"' in result
    assert 'stroke="black"' in result
    assert 'stroke-width="2"' in result


def test_svg_rectangle_no_fill():
    """Test SVG rectangle without fill."""
    rect = SvgRectangle(0, 0, 50, 50)
    result = str(rect)
    assert '<rect' in result
    assert 'fill=' not in result


def test_svg_circle():
    """Test SVG circle rendering."""
    circle = SvgCircle(100, 100, 50, fill="green", stroke="black", stroke_width=2)
    result = str(circle)
    assert '<circle' in result
    assert 'cx="100"' in result
    assert 'cy="100"' in result
    assert 'r="50"' in result
    assert 'fill="green"' in result
    assert 'stroke="black"' in result
    assert 'stroke-width="2"' in result


def test_svg_circle_no_fill():
    """Test SVG circle without fill."""
    circle = SvgCircle(50, 50, 25)
    result = str(circle)
    assert '<circle' in result
    assert 'fill=' not in result


def test_svg_ellipse():
    """Test SVG ellipse rendering."""
    ellipse = SvgEllipse(100, 100, 80, 40, fill="yellow", stroke="black")
    result = str(ellipse)
    assert '<ellipse' in result
    assert 'cx="100"' in result
    assert 'cy="100"' in result
    assert 'rx="80"' in result
    assert 'ry="40"' in result
    assert 'fill="yellow"' in result
    assert 'stroke="black"' in result


def test_svg_line():
    """Test SVG line rendering."""
    line = SvgLine(10, 10, 100, 100, stroke="red", stroke_width=3)
    result = str(line)
    assert '<line' in result
    assert 'x1="10"' in result
    assert 'y1="10"' in result
    assert 'x2="100"' in result
    assert 'y2="100"' in result
    assert 'stroke="red"' in result
    assert 'stroke-width="3"' in result


def test_svg_line_defaults():
    """Test SVG line with default stroke values."""
    line = SvgLine(0, 0, 50, 50)
    result = str(line)
    assert '<line' in result
    assert 'stroke="black"' in result
    assert 'stroke-width="1"' in result


def test_svg_polygon():
    """Test SVG polygon rendering."""
    points = [(50, 10), (90, 90), (10, 90)]
    polygon = SvgPolygon(points, fill="lime", stroke="purple", stroke_width=2)
    result = str(polygon)
    assert '<polygon' in result
    assert 'points="50,10 90,90 10,90"' in result
    assert 'fill="lime"' in result
    assert 'stroke="purple"' in result
    assert 'stroke-width="2"' in result


def test_svg_polygon_string_points():
    """Test SVG polygon with string points."""
    polygon = SvgPolygon("50,10 90,90 10,90", fill="lime")
    result = str(polygon)
    assert '<polygon' in result
    assert 'points="50,10 90,90 10,90"' in result


def test_svg_polyline():
    """Test SVG polyline rendering."""
    points = [(10, 10), (50, 50), (90, 10)]
    polyline = SvgPolyline(points, stroke="blue", stroke_width=2)
    result = str(polyline)
    assert '<polyline' in result
    assert 'points="10,10 50,50 90,10"' in result
    assert 'fill="none"' in result
    assert 'stroke="blue"' in result
    assert 'stroke-width="2"' in result


def test_svg_polyline_defaults():
    """Test SVG polyline with defaults."""
    points = [(0, 0), (50, 50)]
    polyline = SvgPolyline(points)
    result = str(polyline)
    assert '<polyline' in result
    assert 'fill="none"' in result
    assert 'stroke="black"' in result
    assert 'stroke-width="1"' in result


def test_svg_path():
    """Test SVG path rendering."""
    path = SvgPath("M 10 10 L 50 50 L 90 10", stroke="purple", stroke_width=2, fill="none")
    result = str(path)
    assert '<path' in result
    assert 'd="M 10 10 L 50 50 L 90 10"' in result
    assert 'stroke="purple"' in result
    assert 'stroke-width="2"' in result
    assert 'fill="none"' in result


def test_svg_path_defaults():
    """Test SVG path with defaults."""
    path = SvgPath("M 0 0 L 10 10")
    result = str(path)
    assert '<path' in result
    assert 'fill="none"' in result
    assert 'stroke="black"' in result
    assert 'stroke-width="1"' in result


def test_svg_text():
    """Test SVG text rendering."""
    text = SvgText(50, 50, "Hello, SVG!", fill="blue", font_size=24, font_family="Arial")
    result = str(text)
    assert '<text' in result
    assert 'x="50"' in result
    assert 'y="50"' in result
    assert 'fill="blue"' in result
    assert 'font-size="24"' in result
    assert 'font-family="Arial"' in result
    assert '>Hello, SVG!</text>' in result


def test_svg_text_defaults():
    """Test SVG text with defaults."""
    text = SvgText(10, 10, "Test")
    result = str(text)
    assert '<text' in result
    assert 'fill="black"' in result
    assert 'font-size="16"' in result
    assert 'font-family="Arial, sans-serif"' in result
    assert 'text-anchor="start"' in result


def test_svg_text_alignment():
    """Test SVG text with different alignments."""
    text = SvgText(100, 50, "Centered", text_anchor="middle")
    result = str(text)
    assert 'text-anchor="middle"' in result


def test_complex_svg():
    """Test complex SVG with multiple elements."""
    svg = Svg(
        200, 200,
        SvgRectangle(0, 0, 200, 200, fill="lightblue"),
        SvgCircle(100, 100, 50, fill="yellow"),
        SvgText(100, 180, "Sun", text_anchor="middle", font_size=20)
    )
    result = str(svg)
    assert '<svg' in result
    assert '<rect' in result
    assert '<circle' in result
    assert '<text' in result
    assert 'lightblue' in result
    assert 'yellow' in result
    assert 'Sun' in result


def test_svg_extra_settings():
    """Test SVG components with extra settings."""
    rect = SvgRectangle(0, 0, 100, 100, fill="red", opacity=0.5)
    result = str(rect)
    assert '<rect' in result
    # Extra settings should be parsed
    assert 'opacity' in result.lower()


def test_svg_repr():
    """Test SVG repr for debugging."""
    svg = Svg(100, 100, SvgCircle(50, 50, 25))
    repr_str = repr(svg)
    assert 'Svg' in repr_str
    assert '100' in repr_str
