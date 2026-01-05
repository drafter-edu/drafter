"""

There are three main types defined here:
- `Component`: The base class for all content that can be added to a page. It provides methods for verifying the component's state, parsing extra settings into HTML attributes and styles, updating styles and attributes, and rendering the component to HTML.
- `Content`: A type alias that represents either a `Component` or a string. This allows for flexibility in content representation.
- `PageContent`: A type alias that represents either a single `Content` item or a list of `Content` items. This allows for multiple pieces of content to be grouped together for a page.

Note that `str` is also considered a valid `Content` type, allowing for simple text content to be used directly without needing to create a `Component` instance.


Some HTML elements are actually composed of child elements (e.g., a `<div>` containing multiple `<p>` tags). They might also have dedicated JavaScript and CSS associated with them, that should have their own lifecycle.

To create custom components, you can subclass the `Component` class.

Attribute order should always be consistent, with styles at the end. Generally, this means that they should be alphabetized.

A Component should always:
- Have a **kwargs** parameter in its constructor to accept extra settings.
- Store those extra settings in the `extra_settings` property.
- Use the `parse_extra_settings` method to convert those settings into valid HTML attributes and styles.
- Implement a `render` method that returns the HTML representation of the component.
- Avoid mutating any fields in the `pre_render`, `render`, or `post_render` methods.


Technically, we need the component to return not just its HTML, but also its CSS and JS additions. It might also want to add other messages to the page, such as an instruction to start a timer or something. So our render should really return a more complex structure.

"""

from typing import List, Union, Any, Optional
import html

from drafter.components.planning.render_plan import RenderPlan
from drafter.components.utilities.attributes import (
    BASELINE_ATTRS,
    BOOLEAN_ATTRS,
    remap_attr_styles,
)


class Component:
    """
    Base class for all content that can be added to a page.
    This class is not meant to be used directly, but rather to be subclassed by other classes.
    Critically, each subclass must implement a `__str__` method that returns the HTML representation.
    Note that generally, we prefer to try to `render` the component rather than directly converting it to a string.

    Under any student-facing circumstances, a string value can be used in place of a `Component` object
    (in which case we say it is a `Content` type). However, the `Component` object
    allows for more customization and control over the content.

    Ultimately, the `Component` object is converted to a string when it is rendered.

    This class also has some helpful methods for verifying URLs and handling attributes/styles.
    """

    tag: str
    extra_settings: dict
    children: "Optional[list[PageContent]]" = None
    DEFAULT_EXTRA_SETTINGS: Optional[dict] = None
    EXTRA_ATTRS: list[str] = []

    POSITIONAL_ARGS: list[str] = []
    DEFAULT_ARGS: dict[str, Any] = {}
    RENAME_ARGS: dict[str, str] = {}

    COLLAPSE_WHITESPACE = False
    SELF_CLOSING_TAG = False

    def plan(self, context) -> RenderPlan:
        return RenderPlan(
            kind="tag",
            tag_name=self.get_tag(),
            attributes=self.get_attributes(context),
            children=self.get_children(),
            assets=self.get_assets(),
            known_attributes=self.EXTRA_ATTRS,
            id=self.get_id(),
            self_closing=self.SELF_CLOSING_TAG,
        )

    def get_attributes(self, context) -> dict:
        attributes = {}
        for key in self.POSITIONAL_ARGS:
            value = getattr(self, key)
            if key in self.RENAME_ARGS:
                key = self.RENAME_ARGS[key]
            attributes[key] = value
        if self.DEFAULT_EXTRA_SETTINGS:
            attributes.update(self.DEFAULT_EXTRA_SETTINGS)
        attributes.update(self.extra_settings)
        return attributes

    def get_tag(self) -> str:
        return self.tag

    def get_children(self) -> List[Any]:
        return list(self.children) if self.children is not None else []

    def get_arguments(self) -> List[str]:
        return [repr(c) for c in self.get_children()] + [
            repr(getattr(self, key))
            for key in self.POSITIONAL_ARGS
            if (
                key not in self.DEFAULT_ARGS
                or getattr(self, key) != self.DEFAULT_ARGS.get(key)
            )
        ]

    def get_assets(self):
        return None

    def __repr__(self):
        class_name = self.__class__.__name__
        parts = self.get_arguments()
        if self.extra_settings:
            for key, value in sorted(self.extra_settings.items()):
                parts.append(f"{key}={repr(value)}")
        return f"{class_name}({', '.join(parts)})"

    def get_id(self) -> str:
        """
        Gets the ID of the component if it has one.

        :return: The ID of the component, or an auto-generated one if none is set.
        :rtype: str
        """
        return self.extra_settings.get("id", f"drafter-component-{id(self)}")

    def verify(self, router, state, configuration, request):
        """
        Verify the status of this component. This method is called before rendering the component
        to ensure that the component is in a valid state. If the component is not valid, this method
        should return False.

        Default implementation returns True.

        :param router: The router used to resolve URLs
        :param state: The current state of the server
        :param configuration: The configuration of the server
        :param request: The request being processed
        :return: True if the component is valid, False otherwise
        """
        return None

    def update_style(self, style, value):
        """
        Updates the style of a specific setting and stores it in the
        extra_settings dictionary with a key formatted as "style_{style}".

        :param style: The key representing the style to be updated
        :type style: str
        :param value: The value to associate with the given style key
        :type value: Any
        :return: Returns the instance of the object after updating the style
        :rtype: self
        """
        self.extra_settings[f"style_{style}"] = value
        return self

    def update_attr(self, attr, value):
        """
        Updates a specific attribute with the given value in the extra_settings dictionary.

        This method modifies the `extra_settings` dictionary by setting the specified
        attribute to the given value. It returns the instance of the object, allowing
        for method chaining. No validation is performed on the input values, so they
        should conform to the expected structure or constraints of the `extra_settings`.

        :param attr: The key of the attribute to be updated in the dictionary.
        :type attr: str
        :param value: The value to set for the specified key in the dictionary.
        :type value: Any
        :return: The instance of the object after the update.
        :rtype: Self
        """
        self.extra_settings[attr] = value
        return self

    # DEPRECATED OLD APPROACH BELOW

    def parse_extra_settings(self, **kwargs):
        """
        Parses and combines extra settings into valid attribute and style formats.

        This method processes additional configuration settings provided via arguments or stored
        in the `extra_settings` property, converts them into valid HTML attributes and styles,
        and then consolidates the processed values into the appropriate output format. Attributes
        not explicitly defined in the baseline or extra attribute lists are converted into inline
        style declarations.

        :param kwargs: Arbitrary keyword arguments containing extra configuration settings to be
            applied or overridden. The keys represent attribute or style names, and the values
            represent their corresponding values.
        :return: A string containing formatted HTML attributes along with an inline style block
            if any styles are provided.
        :rtype: str
        """
        extra_settings = self.extra_settings.copy()
        extra_settings.update(kwargs)
        raw_styles, raw_attrs = remap_attr_styles(extra_settings)
        styles, attrs = [], []
        seen_attrs = set()
        # Preprocess attributes and styles
        for key, value in raw_attrs.items():
            # Check for data-* attributes
            is_data_attr = key.startswith("data-")
            # Check if known attribute
            is_known_attr = key in self.EXTRA_ATTRS or key in BASELINE_ATTRS

            if not is_data_attr and not is_known_attr:
                # If not a data-* or known attribute, assume it is a style
                styles.append(f"{key}: {value}")
            else:
                # Handle boolean attributes
                if key in BOOLEAN_ATTRS:
                    if value:
                        attrs.append(f"{key}")
                else:
                    # Otherwise handle regular attribute
                    escaped_value = html.escape(str(value), quote=True)
                    attrs.append(f'{key}="{escaped_value}"')
                seen_attrs.add(key)
        # Now handle styles
        for key, value in raw_styles.items():
            styles.append(f"{key}: {value}")
        if "id" not in seen_attrs:
            attrs.append(f'id="{self.get_id()}"')
        result = " ".join(sorted(attrs))
        if styles:
            result += f" style='{'; '.join(sorted(styles))}'"
        return result

    def _render_tag(
        self, tag_name: str, content: str = "", self_closing: bool = False, **kwargs
    ) -> str:
        """
        Renders an HTML tag with the given name and attributes.

        :param tag_name: The name of the HTML tag to render
        :param self_closing: Whether the tag is self-closing (e.g., <br />)
        :param kwargs: Additional attributes to include in the tag
        :return: The rendered HTML tag as a string
        """
        parsed_settings = self.parse_extra_settings(**kwargs)
        if self_closing:
            return f"<{tag_name} {parsed_settings}/>"
        else:
            return f"<{tag_name} {parsed_settings}>{content}</{tag_name}>"

    def render(self, current_state, configuration):
        """
        This method is called when the component is being rendered to a string. It should return
        the HTML representation of the component, using the current State and configuration to
        determine the final output. The fall back for every component is to simply convert it to a string using str().

        Parents are responsible for calling the render method of their children as needed!

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        :return: The HTML representation of the component
        """
        self.pre_render(current_state, configuration)
        result = str(self)
        self.post_render(current_state, configuration)
        return result

    def pre_render(self, current_state, configuration):
        """
        This method is called before the component is rendered. It can be used to perform any
        necessary setup or initialization before the component is converted to a string.

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        """
        pass

    def post_render(self, current_state, configuration):
        """
        This method is called after the component is rendered. It can be used to perform any
        necessary cleanup or finalization after the component has been converted to a string.

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        """
        pass


Content = Union[Component, str]
PageContent = Union[Content, List[Content]]
