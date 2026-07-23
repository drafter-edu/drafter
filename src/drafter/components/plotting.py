"""Plotting components for embedding charts in pages.

Defines `MatPlotLibPlot`, which captures the current Matplotlib figure
and embeds it in the page as an image or inline SVG.
"""

import base64
import io
from dataclasses import dataclass

from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan
from drafter.helpers.utils import is_pyodide

try:
    import matplotlib.pyplot as plt

    _has_matplotlib = True
except ImportError as e:
    _has_matplotlib = False
    print(e)


@dataclass(repr=False)
class MatPlotLibPlot(Component):
    """Renders a Matplotlib figure as an image or SVG element.

    Captures the current Matplotlib figure and embeds it as a base64-encoded
    PNG or inline SVG. Can be used to display plots directly in Drafter pages.

    Attributes:
        extra_matplotlib_settings: Dict of Matplotlib savefig keyword arguments.
        close_automatically: Whether to close the figure after rendering.
        tag: The HTML tag name, always 'img'.
    """

    extra_matplotlib_settings: dict
    close_automatically: bool

    tag = "img"
    SELF_CLOSING_TAG = True

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
            close_automatically: Whether to close figure after rendering.
                Defaults to True.
            **kwargs: Additional HTML attributes and styles.

        Raises:
            ImportError: If Matplotlib is not installed.
        """
        if not _has_matplotlib:
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
        plt.savefig(image_data, **settings)  # type: ignore
        decoded_image_data = base64.b64encode(image_data.getvalue()).decode("utf-8")
        return RenderPlan(
            kind="raw",
            raw_html=f'<img src="data:image/png;base64,{decoded_image_data}" />',
        )

    def plan(self, context) -> RenderPlan:
        """Generate render plan for the Matplotlib figure.

        Args:
            context: Rendering context.

        Returns:
            RenderPlan for img element (PNG) or raw SVG content.

        Raises:
            ValueError: If format is not 'png' or 'svg'.
        """
        if is_pyodide():
            return self._plan_pyodide(context)
        else:
            # Handle image processing
            image_data = io.BytesIO()
            plt.savefig(image_data, **self.extra_matplotlib_settings)  # type: ignore
            if self.close_automatically:
                plt.close()  # type: ignore
            image_data.seek(0)

            attrs = {}
            if self.extra_matplotlib_settings["format"] == "png":
                figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
                figure = f"data:image/png;base64,{figure}"
                attrs["src"] = figure
            elif self.extra_matplotlib_settings["format"] == "svg":
                figure = image_data.read().decode()
                # For SVG, we return the raw HTML
                return RenderPlan(
                    kind="raw",
                    raw_html=figure,
                )
            else:
                raise ValueError(
                    f"Unsupported format {self.extra_matplotlib_settings['format']}"
                )

            attrs.update(self.extra_settings)

            return self._plan_tag(context, attributes=attrs)
