from dataclasses import dataclass
import io
import base64
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan

try:
    import matplotlib.pyplot as plt

    _has_matplotlib = True
except ImportError:
    _has_matplotlib = False


@dataclass(repr=False)
class MatPlotLibPlot(Component):
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

    def plan(self, context) -> RenderPlan:
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
