"""Rendering of component hierarchies into HTML strings.

Provides the `Renderer` class and the `render` convenience function, which
recursively convert strings, lists, `Component` instances, and
`RenderPlan` objects into indented HTML while collecting CSS/JS assets and
recording rendering errors.
"""

import html
from dataclasses import dataclass

from drafter.components import Component
from drafter.components.planning.render_plan import NewlineMode, RenderPlan
from drafter.components.utilities.attributes import parse_extra_settings
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState


class RenderError(Exception):
    """Exception raised during component rendering."""

    pass


@dataclass
class Renderer:
    """Convert component hierarchies to HTML strings with asset tracking.

    Recursively processes components, strings, and lists into HTML.
    Handles attribute escaping, whitespace control, and collects CSS/JS assets.

    Attributes:
        state: Current application state for component context.
        configuration: Server configuration for rendering context.
        errors: Accumulated rendering errors.
        component_stack: Path to current component for error reporting.
        depth: Current indentation level.
        parts: Accumulated HTML string fragments.
        assets: Collected CSS and JS asset URLs.
        indentation: Spaces per indentation level.
        newline_mode_stack: Stack of `NewlineMode` values controlling whether
            newlines in text are converted to `<br>`; components push and pop
            modes as they are rendered.
    """

    def __init__(
        self,
        state: SiteState | None = None,
        configuration: ClientServerConfiguration | None = None,
    ):
        self.state = state
        self.configuration = configuration
        self.errors = []
        self.component_stack = []
        self.depth = 0
        self.parts = []
        self.assets = {"css": set(), "js": set()}
        self.indentation = 2
        self.newline_mode_stack = [NewlineMode.CONVERT_TO_BR]

    def flatten(self) -> str:
        """Combine all accumulated HTML parts into a single string.

        Returns:
            str: Complete rendered HTML output.
        """
        return "".join(self.parts)

    def write(self, part: str):
        """Write an HTML string with current indentation.

        Args:
            part: HTML fragment to write.
        """
        self.parts.append((self.depth) * (" " * self.indentation) + part)

    def new_line(self):
        """Append a newline to the output."""
        self.parts.append("\n")

    def in_convert_newlines_mode(self) -> bool | None:
        """Check if the current rendering mode converts newlines to `<br>`.

        Returns:
            True when the current newline mode is not RETAIN and the
            configuration enables `newlines_to_br`; otherwise a falsy value
            (False, or None when no configuration is set).
        """
        return self.newline_mode_stack[-1] != NewlineMode.RETAIN and (
            self.configuration and self.configuration.newlines_to_br
        )

    def render(self, component):
        """Recursively render a component to HTML.

        Handles strings (escaped), lists (iterated), Components (planned),
        and RenderPlans (direct output). Manages indentation and asset tracking.

        Args:
            component: String, list, Component, or RenderPlan to render.

        Raises:
            RenderError: If component rendering encounters an error.
            TypeError: If component type is unsupported.

        TODO:
            Handle errors more gracefully with logging.
        """
        # TODO: Handle errors gracefully and log them
        # print(self.component_stack, component)
        # print(self.depth, component, self.in_convert_newlines_mode())
        if isinstance(component, str):
            if self.in_convert_newlines_mode():
                escaped = html.escape(component).replace("\n", "<br>")
                self.write(escaped)
            else:
                self.write(html.escape(component))
        elif isinstance(component, list):
            for child_index, child in enumerate(component):
                self.component_stack.append(f"[{child_index}]")
                self.render(child)
                self.new_line()
                self.component_stack.pop()
        elif isinstance(component, (Component, RenderPlan)):
            if isinstance(component, Component):
                # Get the rendering plan for the component
                try:
                    plan = component.plan(self)
                except Exception as e:
                    error = RenderError(
                        f"Error rendering component {component} at {self.component_stack}: {e}"
                    )
                    self.errors.append(error)
                    raise error from e
            else:
                plan = component

            # Handle assets
            if plan.assets:
                self.assets["css"].update(plan.assets.css)
                self.assets["js"].update(plan.assets.js)

            # Render based on the kind of plan
            if plan.kind == "tag":
                self.component_stack.append(plan.tag_name)
                attrs = ""
                if plan.attributes:
                    parsed_attrs = parse_extra_settings(
                        plan.attributes, plan.known_attributes, plan.id
                    )
                    if parsed_attrs:
                        attrs = f" {parsed_attrs}"
                closed = "/" if plan.self_closing else ""
                self.write(f"<{plan.tag_name}{attrs}{closed}>")
                if not plan.collapse_whitespace and not plan.self_closing:
                    self.new_line()
                # TODO: Handle COLLAPSE_WHITESPACE if needed
                self.depth += 1
                old_depth = 0
                if plan.children:
                    for child_index, child in enumerate(plan.children):
                        self.component_stack.append(f"[{child_index}]")
                        if plan.collapse_whitespace:
                            old_depth = self.depth
                            self.depth = 0
                        self.newline_mode_stack.append(plan.newline_mode)
                        self.render(child)
                        self.newline_mode_stack.pop()
                        if not plan.collapse_whitespace:
                            self.new_line()
                        else:
                            self.depth = old_depth
                        self.component_stack.pop()
                self.depth -= 1
                if not plan.self_closing:
                    self.write(f"</{plan.tag_name}>")
                self.component_stack.pop()
            elif plan.kind == "fragment":
                if plan.items:
                    for item_index, item in enumerate(plan.items):
                        self.component_stack.append(f"[{item_index}]")
                        self.render(item)
                        self.component_stack.pop()
            elif plan.kind == "emit":
                if plan.emitter:
                    plan.emitter(self.state, self.configuration)
            elif plan.kind == "raw":
                if plan.raw_html:
                    self.write(plan.raw_html)
        else:
            raise TypeError(
                f"Unsupported page content type: {type(component)}\nAt {self.component_stack}"
            )


def render(
    component,
    state: SiteState | None = None,
    configuration: ClientServerConfiguration | None = None,
) -> Renderer:
    """Create a Renderer and render a component hierarchy to HTML.

    Args:
        component: Component/string/list to render.
        state: Application state for component context.
        configuration: Server configuration for rendering context.

    Returns:
        Renderer: Instance with completed rendering and accumulated assets.
    """
    renderer = Renderer(state, configuration)
    renderer.render(component)
    return renderer
