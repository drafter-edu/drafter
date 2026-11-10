"""Plotting components for embedding charts in pages.

Defines `MatPlotLibPlot`, which captures the current Matplotlib figure
and embeds it in the page as an image or inline SVG.
"""

import io
from dataclasses import dataclass
from typing import Any

from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan
from drafter.data.errors import StudentFacingError
from drafter.data.images import Picture, bytes_to_data_url
from drafter.helpers.utils import is_pyodide, is_skulpt

_plt = None


def _get_pyplot():
    """Import matplotlib.pyplot on first use, caching the module.

    In the browser, matplotlib is not preloaded: it is installed if the student
    explicitly requires it or imports it in their top-level code.
    Importing at use time rather than at module load time means such
    late installs are still picked up.

    Returns:
        The matplotlib.pyplot module, or None if matplotlib is unavailable.
    """
    global _plt
    if _plt is None:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return None
        _plt = plt
    return _plt


def has_matplotlib() -> bool:
    """Whether matplotlib is importable, attempting the import if needed."""
    return _get_pyplot() is not None


@dataclass(repr=False)
class MatPlotLibPlot(Component):
    """Renders a Matplotlib figure as an image or SVG element.

    Captures the current Matplotlib figure at the moment the component is
    created and embeds it as a base64-encoded PNG or inline SVG. Draw the
    chart first, then create the component.

    Because the figure is captured (and, by default, closed) on creation,
    the next chart always starts from a blank figure. That holds even when
    the page is never shown, such as when a unit test calls the route.

    Attributes:
        extra_matplotlib_settings: Dict of Matplotlib savefig keyword arguments.
        close_automatically: Whether creating the component closes the
            figure, so that later plotting starts a new one.
        tag: The HTML tag name, always 'img'.

    Example:
        plt.plot([12, 15, 11, 18])
        plt.title("Treats eaten this week")
        Page(state, [MatPlotLibPlot()])
    """

    extra_matplotlib_settings: dict
    close_automatically: bool

    tag = "img"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["src", "alt"]

    ARGUMENTS = [
        ComponentArgument(
            "extra_matplotlib_settings", kind="keyword", default_value=None
        ),
        ComponentArgument("close_automatically", kind="keyword", default_value=True),
    ]

    def __init__(
        self, extra_matplotlib_settings=None, close_automatically=True, **kwargs
    ):
        """Initialize Matplotlib plot component.

        Args:
            extra_matplotlib_settings: Optional dict of Matplotlib savefig kwargs.
                Defaults to PNG format with tight bounding box.
            close_automatically: Whether to close the captured figure so
                the next chart starts fresh. Pass False to keep drawing on
                the same figure, or to show it in a second MatPlotLibPlot.
                Defaults to True.
            **kwargs: Additional HTML attributes and styles.

        Raises:
            ImportError: If Matplotlib is not installed.
        """
        if not has_matplotlib():
            raise ImportError(
                "Matplotlib is not installed. Please install it to use this feature."
            )
        if extra_matplotlib_settings is None:
            extra_matplotlib_settings = {}
        self.extra_matplotlib_settings = extra_matplotlib_settings
        self.extra_settings = kwargs
        if "format" not in extra_matplotlib_settings:
            extra_matplotlib_settings["format"] = "png"
        if "bbox_inches" not in extra_matplotlib_settings:
            extra_matplotlib_settings["bbox_inches"] = "tight"
        self.close_automatically = close_automatically
        self._figure = self._capture_figure()

    def _capture_figure(self) -> Any:
        """Take hold of pyplot's current figure for this component.

        Capturing at creation time, instead of when the page renders, ties
        the chart to the plotting commands that came just before it. With
        `close_automatically`, the figure is also released from pyplot, so
        nothing drawn for this chart can appear in a later one. A released
        figure can still be saved.

        Returns:
            The captured figure, or None under Skulpt, whose matplotlib
            only supports saving the current figure.
        """
        if is_skulpt():
            return None
        plt = _get_pyplot()
        figure = plt.gcf()
        if self.close_automatically:
            plt.close(figure)
        return figure

    def _save_figure(self, target: io.BytesIO, settings: dict) -> None:
        """Write the captured figure into `target` using savefig settings.

        Args:
            target: Buffer that receives the image data.
            settings: Keyword arguments for Matplotlib's `savefig`.
        """
        if self._figure is None:
            # Skulpt: no figure objects, so save whatever is current.
            _get_pyplot().savefig(target, **settings)
        else:
            self._figure.savefig(target, **settings)

    def to_picture(self) -> Picture:
        """Render this component's Matplotlib figure as a `Picture`.

        Renders the figure captured when the component was created to PNG
        with this component's settings, so the chart can be stored in
        state, manipulated, or offered as a download.

        Returns:
            The rendered chart as a Picture.
        """
        image_data = io.BytesIO()
        settings = self.extra_matplotlib_settings.copy()
        settings["format"] = "png"
        self._save_figure(image_data, settings)
        return Picture.from_bytes(image_data.getvalue(), mime_type="image/png")

    def _plan_pyodide(self, context) -> RenderPlan:
        """Generate render plan for Pyodide environment.

        Saves the figure to an in-memory PNG buffer and embeds it as a
        base64-encoded `<img>` data URL.

        Args:
            context: Rendering context.

        Returns:
            RenderPlan with raw HTML for the figure.
        """
        # In Pyodide, save the figure to a PNG buffer and embed it as a base64 data URL
        image_data = io.BytesIO()
        settings = self.extra_matplotlib_settings.copy()
        if "format" not in settings:
            settings["format"] = "png"
        self._save_figure(image_data, settings)
        data_url = bytes_to_data_url(image_data.getvalue(), "image/png")
        return RenderPlan(
            kind="raw",
            raw_html=f'<img src="{data_url}" />',
        )

    def plan(self, context) -> RenderPlan:
        """Generate render plan for the Matplotlib figure.

        Args:
            context: Rendering context.

        Returns:
            RenderPlan for img element (PNG) or raw SVG content.

        Raises:
            StudentFacingError: If format is not 'png' or 'svg'.
        """
        if is_pyodide():
            return self._plan_pyodide(context)
        else:
            # Handle image processing
            image_data = io.BytesIO()
            self._save_figure(image_data, self.extra_matplotlib_settings)
            image_data.seek(0)

            attrs = {}
            if self.extra_matplotlib_settings["format"] == "png":
                attrs["src"] = bytes_to_data_url(image_data.getvalue(), "image/png")
            elif self.extra_matplotlib_settings["format"] == "svg":
                figure = image_data.read().decode()
                # For SVG, we return the raw HTML
                return RenderPlan(
                    kind="raw",
                    raw_html=figure,
                )
            else:
                raise StudentFacingError(
                    f"Unsupported format {self.extra_matplotlib_settings['format']}",
                    friendly=(
                        "The format you gave MatPlotLibPlot in "
                        "extra_matplotlib_settings is "
                        f"{self.extra_matplotlib_settings['format']!r}, but "
                        "plots can only be shown as 'png' or 'svg'."
                    ),
                    steps=(
                        "Change the format to 'png' or 'svg', like "
                        "MatPlotLibPlot({'format': 'png'}).",
                        "Or leave out the format setting to use the default ('png').",
                    ),
                )

            attrs.update(self.extra_settings)

            return self._plan_tag(context, attributes=attrs)
