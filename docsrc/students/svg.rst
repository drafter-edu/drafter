.. _svg_docs:

SVG Graphics Documentation
==========================

SVG (Scalable Vector Graphics) support in Drafter allows you to create resolution-independent graphics
that scale perfectly at any size. This page documents all the SVG components available in Drafter.

Overview
--------

All SVG elements must be placed inside an ``Svg`` container. The container defines the size of your
drawing canvas. Inside the container, you can add shapes, lines, text, and other elements.

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from drafter import Page, Svg, SvgCircle, SvgRectangle
    
    @route
    def svg_demo(state: State) -> Page:
        svg = Svg(
            200, 200,
            SvgCircle(100, 100, 50, fill="blue"),
            SvgRectangle(10, 10, 80, 40, fill="red")
        )
        return Page(state, [svg])

SVG Container
-------------

.. function:: Svg(width, height, *content, **kwargs)

    Container component for SVG graphics. All SVG shapes and text must be placed inside an Svg container.
    
    :param width: Width of the SVG canvas in pixels
    :type width: int
    :param height: Height of the SVG canvas in pixels
    :type height: int
    :param content: SVG elements to include (shapes, text, etc.). You do not pass them in as a list, 
                    but as separate arguments (like the ``print`` function).
    :type content: SvgComponent
    :param kwargs: Additional SVG attributes (e.g., viewBox, preserveAspectRatio)
    
    Example:
    
    .. code-block:: python
    
        Svg(
            300, 200,
            SvgCircle(150, 100, 60, fill="green"),
            SvgText(150, 180, "Hello!", text_anchor="middle")
        )

Shape Components
----------------

SvgRectangle
~~~~~~~~~~~~

.. function:: SvgRectangle(x, y, width, height, fill=None, stroke=None, stroke_width=None, **kwargs)

    Create a rectangle in an SVG.
    
    :param x: X-coordinate of the top-left corner
    :type x: float
    :param y: Y-coordinate of the top-left corner
    :type y: float
    :param width: Width of the rectangle
    :type width: float
    :param height: Height of the rectangle
    :type height: float
    :param fill: Fill color (e.g., "red", "#FF0000", "rgb(255,0,0)"). Defaults to ``None`` (transparent).
    :type fill: str
    :param stroke: Outline color. Defaults to ``None`` (no outline).
    :type stroke: str
    :param stroke_width: Width of the outline. Defaults to ``None``.
    :type stroke_width: float
    
    Example:
    
    .. code-block:: python
    
        SvgRectangle(10, 20, 100, 50, fill="blue", stroke="black", stroke_width=2)

SvgCircle
~~~~~~~~~

.. function:: SvgCircle(cx, cy, r, fill=None, stroke=None, stroke_width=None, **kwargs)

    Create a circle in an SVG.
    
    :param cx: X-coordinate of the center
    :type cx: float
    :param cy: Y-coordinate of the center
    :type cy: float
    :param r: Radius of the circle
    :type r: float
    :param fill: Fill color (e.g., "red", "#FF0000", "rgb(255,0,0)"). Defaults to ``None`` (transparent).
    :type fill: str
    :param stroke: Outline color. Defaults to ``None`` (no outline).
    :type stroke: str
    :param stroke_width: Width of the outline. Defaults to ``None``.
    :type stroke_width: float
    
    Example:
    
    .. code-block:: python
    
        SvgCircle(100, 100, 50, fill="green", stroke="black", stroke_width=2)

SvgEllipse
~~~~~~~~~~

.. function:: SvgEllipse(cx, cy, rx, ry, fill=None, stroke=None, stroke_width=None, **kwargs)

    Create an ellipse in an SVG.
    
    :param cx: X-coordinate of the center
    :type cx: float
    :param cy: Y-coordinate of the center
    :type cy: float
    :param rx: Horizontal radius
    :type rx: float
    :param ry: Vertical radius
    :type ry: float
    :param fill: Fill color. Defaults to ``None`` (transparent).
    :type fill: str
    :param stroke: Outline color. Defaults to ``None`` (no outline).
    :type stroke: str
    :param stroke_width: Width of the outline. Defaults to ``None``.
    :type stroke_width: float
    
    Example:
    
    .. code-block:: python
    
        SvgEllipse(100, 100, 80, 40, fill="yellow", stroke="black")

SvgLine
~~~~~~~

.. function:: SvgLine(x1, y1, x2, y2, stroke="black", stroke_width=1, **kwargs)

    Create a line in an SVG.
    
    :param x1: X-coordinate of the start point
    :type x1: float
    :param y1: Y-coordinate of the start point
    :type y1: float
    :param x2: X-coordinate of the end point
    :type x2: float
    :param y2: Y-coordinate of the end point
    :type y2: float
    :param stroke: Line color. Defaults to ``"black"``.
    :type stroke: str
    :param stroke_width: Width of the line. Defaults to ``1``.
    :type stroke_width: float
    
    Example:
    
    .. code-block:: python
    
        SvgLine(10, 10, 100, 100, stroke="red", stroke_width=3)

SvgPolygon
~~~~~~~~~~

.. function:: SvgPolygon(points, fill="black", stroke=None, stroke_width=None, **kwargs)

    Create a polygon (closed shape with straight sides) in an SVG.
    
    :param points: List of (x, y) coordinate tuples that define the polygon's vertices
    :type points: list[tuple] or str
    :param fill: Fill color. Defaults to ``"black"``.
    :type fill: str
    :param stroke: Outline color. Defaults to ``None`` (no outline).
    :type stroke: str
    :param stroke_width: Width of the outline. Defaults to ``None``.
    :type stroke_width: float
    
    Example (create a triangle):
    
    .. code-block:: python
    
        SvgPolygon([(50, 10), (90, 90), (10, 90)], fill="lime", stroke="purple", stroke_width=2)

SvgPolyline
~~~~~~~~~~~

.. function:: SvgPolyline(points, fill="none", stroke="black", stroke_width=1, **kwargs)

    Create a polyline (open shape with connected straight lines) in an SVG.
    
    :param points: List of (x, y) coordinate tuples that define the line's path
    :type points: list[tuple] or str
    :param fill: Fill color. Defaults to ``"none"`` for an open shape.
    :type fill: str
    :param stroke: Line color. Defaults to ``"black"``.
    :type stroke: str
    :param stroke_width: Width of the line. Defaults to ``1``.
    :type stroke_width: float
    
    Example (create a zigzag line):
    
    .. code-block:: python
    
        SvgPolyline([(10, 10), (50, 50), (90, 10)], stroke="blue", stroke_width=2)

SvgPath
~~~~~~~

.. function:: SvgPath(d, fill="none", stroke="black", stroke_width=1, **kwargs)

    Create a path (complex shape) in an SVG using path commands. This is an advanced feature
    for creating complex shapes like curves and arcs.
    
    The path is defined using a series of commands:
    
    * ``M`` = moveto (move to a point without drawing)
    * ``L`` = lineto (draw a straight line to a point)
    * ``H`` = horizontal lineto
    * ``V`` = vertical lineto
    * ``C`` = curveto (cubic Bézier curve)
    * ``S`` = smooth curveto
    * ``Q`` = quadratic Bézier curve
    * ``T`` = smooth quadratic Bézier curve
    * ``A`` = elliptical arc
    * ``Z`` = closepath (close the current shape)
    
    :param d: Path data string using SVG path commands
    :type d: str
    :param fill: Fill color. Defaults to ``"none"``.
    :type fill: str
    :param stroke: Line color. Defaults to ``"black"``.
    :type stroke: str
    :param stroke_width: Width of the line. Defaults to ``1``.
    :type stroke_width: float
    
    Example (draw a simple curve):
    
    .. code-block:: python
    
        SvgPath("M 10 10 L 50 50 L 90 10", stroke="purple", stroke_width=2, fill="none")

Text Component
--------------

SvgText
~~~~~~~

.. function:: SvgText(x, y, text, fill="black", font_size=16, font_family="Arial, sans-serif", text_anchor="start", **kwargs)

    Create text in an SVG.
    
    :param x: X-coordinate where the text starts
    :type x: float
    :param y: Y-coordinate where the text baseline sits
    :type y: float
    :param text: The text content to display
    :type text: str
    :param fill: Text color. Defaults to ``"black"``.
    :type fill: str
    :param font_size: Size of the font in pixels. Defaults to ``16``.
    :type font_size: int
    :param font_family: Font family to use. Defaults to ``"Arial, sans-serif"`` for cross-platform compatibility.
    :type font_family: str
    :param text_anchor: Text alignment - ``"start"``, ``"middle"``, or ``"end"``. Defaults to ``"start"``.
    :type text_anchor: str
    
    Example:
    
    .. code-block:: python
    
        SvgText(50, 50, "Hello, SVG!", fill="blue", font_size=24, text_anchor="middle")

Colors in SVG
-------------

SVG supports several color formats:

* **Named colors**: ``"red"``, ``"blue"``, ``"green"``, ``"orange"``, etc.
* **Hex colors**: ``"#FF0000"`` (red), ``"#00FF00"`` (green), ``"#0000FF"`` (blue)
* **RGB colors**: ``"rgb(255, 0, 0)"`` (red), ``"rgb(0, 255, 0)"`` (green)
* **RGBA colors**: ``"rgba(255, 0, 0, 0.5)"`` (semi-transparent red)

Complete Example
----------------

Here's a complete example creating a simple scene with multiple SVG elements:

.. code-block:: python

    from drafter import route, Page, State, Svg, SvgRectangle, SvgCircle, SvgText, SvgLine
    
    @route
    def svg_scene(state: State) -> Page:
        # Create a simple house scene
        svg = Svg(
            400, 300,
            # Sky
            SvgRectangle(0, 0, 400, 200, fill="lightblue"),
            # Ground
            SvgRectangle(0, 200, 400, 100, fill="green"),
            # House body
            SvgRectangle(100, 120, 120, 80, fill="beige", stroke="brown", stroke_width=2),
            # Roof
            SvgPolygon([(90, 120), (160, 70), (230, 120)], fill="darkred", stroke="brown", stroke_width=2),
            # Door
            SvgRectangle(140, 150, 40, 50, fill="brown"),
            # Window
            SvgRectangle(180, 140, 30, 30, fill="lightblue", stroke="black", stroke_width=1),
            # Sun
            SvgCircle(350, 50, 30, fill="yellow"),
            # Label
            SvgText(200, 280, "My House", fill="black", font_size=20, text_anchor="middle")
        )
        
        return Page(state, [svg])

Tips for Beginners
------------------

1. **Start with the container**: Always begin by creating an ``Svg`` container with a width and height.

2. **Coordinate system**: The top-left corner is (0, 0). X increases to the right, Y increases downward.

3. **Layering**: Elements are drawn in the order they appear. Later elements appear on top of earlier ones.

4. **Colors**: Start with simple named colors like ``"red"``, ``"blue"``, ``"green"`` before moving to hex codes.

5. **Testing**: Start with one shape at a time, then gradually add more to build up your graphic.

6. **Sizes**: All measurements are in pixels. A good starting size for an SVG is 200x200 or 300x300.
