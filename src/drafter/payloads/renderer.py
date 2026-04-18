from dataclasses import dataclass
from typing import Optional
import html
from drafter.components import Component
from drafter.components.planning.render_plan import RenderPlan
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
    """

    def __init__(
        self,
        state: Optional[SiteState] = None,
        configuration: Optional[ClientServerConfiguration] = None,
    ):
        self.state = state
        self.configuration = configuration
        self.errors = []
        self.component_stack = []
        self.depth = 0
        self.parts = []
        self.assets = {"css": set(), "js": set()}
        self.indentation = 2
        self.in_preformatted = 0

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
        if isinstance(component, str):
            escaped = html.escape(component)
            if self.in_preformatted:
                self.write(escaped)
            elif '\n' in escaped:
                lines = escaped.split('\n')
                for i, line in enumerate(lines):
                    self.write(line)
                    if i < len(lines) - 1:
                        self.new_line()
                        self.write('<br>')
                        self.new_line()
            else:
                self.write(escaped)
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
                if plan.collapse_whitespace:
                    self.in_preformatted += 1
                if plan.children:
                    for child_index, child in enumerate(plan.children):
                        self.component_stack.append(f"[{child_index}]")
                        if plan.collapse_whitespace:
                            old_depth = self.depth
                            self.depth = 0
                        self.render(child)
                        if not plan.collapse_whitespace:
                            self.new_line()
                        else:
                            self.depth = old_depth
                        self.component_stack.pop()
                if plan.collapse_whitespace:
                    self.in_preformatted -= 1
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
    state: Optional[SiteState] = None,
    configuration: Optional[ClientServerConfiguration] = None,
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
