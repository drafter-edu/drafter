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
- Have a **extra_settings** kwargs parameter in its constructor to accept extra settings that are stored in `extra_settings` dict


Technically, we need the component to return not just its HTML, but also its CSS and JS additions. It might also want to add other messages to the page, such as an instruction to start a timer or something. So our render should really return a more complex structure.

"""

from dataclasses import dataclass
from typing import List, Union, Any, Optional, ClassVar, Callable
import json
import html

from drafter.components.planning.render_plan import AssetBundle, RenderPlan
from drafter.components.utilities.attributes import (
    BASELINE_ATTRS,
    BOOLEAN_ATTRS,
    remap_attr_styles,
)
from drafter.components.utilities.validation import (
    validate_json_value,
    validate_parameter_name,
)

RouteSafeValue = Union[str, int, float, bool]
JsonSafeValue = Union[str, int, float, bool, None, list, dict]
UrlOrFunction = Union[str, Callable]


@dataclass
class ComponentArgument:
    name: str
    kind: str = "positional"  # "positional", "var", "keyword"
    default_value: Any = None
    is_content: bool = False


@dataclass
class Arguable:
    name: str
    value: JsonSafeValue


def convert_arguments_to_json(arguments, only_validate=False) -> Optional[str]:
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            validate_parameter_name(key, "Argument")
            validate_json_value(value, "Argument")
        return json.dumps(arguments) if not only_validate else None

    elif isinstance(arguments, Arguable):
        validate_parameter_name(arguments.name, "Argument")
        validate_json_value(arguments.value, "Argument")
        return (
            json.dumps({arguments.name: arguments.value}) if not only_validate else None
        )

    elif isinstance(arguments, (list, set, tuple)):
        argument_dict = {}
        for index, item in enumerate(arguments):
            if isinstance(item, Arguable):
                validate_parameter_name(item.name, "Argument")
                validate_json_value(item.value, "Argument")
                argument_dict[item.name] = item.value
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                key, value = item
                validate_parameter_name(key, "Argument")
                validate_json_value(value, "Argument")
                argument_dict[key] = value
            elif isinstance(item, dict) and len(item) == 1:
                key, value = next(iter(item.items()))
                validate_parameter_name(key, "Argument")
                validate_json_value(value, "Argument")
                argument_dict[key] = value
            else:
                raise ValueError(
                    f"Invalid argument format at index {index}: {item}.\nMust be an Arguable, a (name, value) pair, or a dict with a single key-value pair."
                )
        return json.dumps(argument_dict) if not only_validate else None
    elif isinstance(arguments, dict):
        for key, value in arguments.items():
            validate_parameter_name(key, "Argument")
            validate_json_value(value, "Argument")
        return json.dumps(arguments) if not only_validate else None
    else:
        raise ValueError(
            "The arguments must be an Argument, a list of Argument objects, a list of (name, value) pairs, or a dict of name to value."
        )


class Component:
    """
    Base class for all content that can be added to a page.
    This class is not meant to be used directly, but rather to be subclassed by other classes.

    Components can be turned into HTML by first calling the `plan` method, which
    returns a `RenderPlan` object. The `RenderPlan` object contains all the information
    needed to render the component, including its tag name, attributes, children,
    and any associated assets.

    Components can be converted to a string using __repr__, which should
    be able to roundtrip back to the same component using eval.

    Conceptually, there are three "versions" of the data for the Component:
    - The "arguments" which are essentially defined by the __init__ method and include both
        the positional and keyword arguments. These are stored as fields on the Component instance
        as "internals".
        The arguments can be either positional, variable, keyword, or extra (kwargs).
        Every component must have extra_settings, and that ends up as a field as well.
        When the __repr__ is called, it should generate these arguments to create a string that can be
        eval'd back into the same component.
    - The "fields" which are the actual fields contained inside of the Component as an instance.
        These vary completely by the type of component, but can be used to derive both the arguments
        and the externals. They should roughly align to the arguments, so that the users can
        modify them after the fact and have the changes be reflected in the arguments and the externals.
    - The "externals" which are the HTML attributes, children, assets, and other information
        needed to render the component. These are derived from the internals, but are not stored that
        way. Instead, they are generated on the fly when the `plan` method is called, using the
        `get_attributes`, `get_children`, and `get_assets` methods.

    Args that are marked as "Content" get turned into Children (child content), other args get turned into attributes.

    So basically the canonical data is the fields, and then some of those fields are identified
    to create the HTML attributes, children, and assets.

    The default for an argument is to be turned into an attribute of the same name, unless
    it is in the RENAME_ATTRS dict. The KNOWN_ATTRS list is used to force certain arguments
    to be turned into attributes, even though the default is to turn them into style properties.
    The DEFAULT_ATTRS dict is used to provide default values for attributes, which can be overridden
    by the extra_settings.

    Types of args:
    - Positional regular arg: POSITIONAL_ARGS
    - Variable regular arg: VAR_ARGS
    - Keyword regular arg (default value): DEFAULT_ARGS
    - Positional content arg: CONTENT_ARGS
    - Variable content arg: VAR_CONTENT_ARGS
    - Keyword content arg (default value): DEFAULT_CONTENT_ARGS
    - Extra settings (kwargs that get turned into attributes)

    A special extra case is the `arguments` parameter, primarily for Link and Button components, but actually
    usable by any component. This will be a list of Argument objects that will represent be turned into a special
    `data--drafter-arguments` attribute that will have arguments embedded directly on the element, which will
    then be passed to any events emanating from that element. The obvious use case is for links and buttons, where
    you want arguments to be passed when the link or button is clicked, but it could also be used for other events.
    - The `arguments` parameter can be either an Argument, a sequence of Argument, a sequence of (name, value) pairs, or a dict of name to value.
    - The names MUST be valid Python identifiers, and the values can be any JSON-serializable value (but not dataclasses).
    - The `arguments` parameter will be turned into a `data--drafter-arguments` attribute.
    - The value of the `data--drafter-arguments` attribute will be a JSON string.
    - The `arguments` parameter will usually be stored in the `extra_settings` dict, but it can also be stored as a field on the component if desired.

    Under any student-facing circumstances, a string value can be used in place of a `Component` object
    (in which case we say it is a `Content` type). However, the `Component` object
    allows for more customization and control over the content. Most situations also
    allow for a list of `Content` objects (which we call `PageContent`), which can be
    used to group multiple pieces of content together.
    """

    tag: str
    extra_settings: dict

    ARGUMENTS: ClassVar[list[ComponentArgument]] = []

    DEFAULT_ATTRS: ClassVar[dict] = {}
    KNOWN_ATTRS: ClassVar[list[str]] = []
    RENAME_ATTRS: ClassVar[dict[str, str]] = {}

    # Formatting settings
    COLLAPSE_WHITESPACE: ClassVar[bool] = False
    SELF_CLOSING_TAG: ClassVar[bool] = False

    # Constants
    DRAFTER_DATA_ARGUMENT_NAME: ClassVar[str] = "data--drafter-arguments"

    def plan(self, context) -> RenderPlan:
        return self._plan_tag(context)

    def _plan_tag(
        self,
        context,
        tag_name=None,
        attributes=None,
        children=None,
        assets=None,
        known_attributes=None,
        id=None,
        self_closing=None,
    ) -> RenderPlan:
        return RenderPlan(
            kind="tag",
            tag_name=tag_name or self.get_tag(context),
            attributes=attributes or self.get_attributes(context),
            children=children or self.get_children(context),
            assets=assets or self.get_assets(context),
            known_attributes=known_attributes or self.KNOWN_ATTRS,
            id=id or self.get_id(),
            self_closing=self_closing
            if self_closing is not None
            else self.SELF_CLOSING_TAG,
        )

    def _handle_extra_settings(self, attributes, context) -> dict:
        for key, value in self.extra_settings.items():
            if key == "arguments":
                attributes[self.DRAFTER_DATA_ARGUMENT_NAME] = convert_arguments_to_json(
                    value
                )
            else:
                attributes[key] = value
        return attributes

    def get_attributes(self, context) -> dict:
        attributes = {}
        # Default attributes that should always be included, unless overridden by extra_settings
        if self.DEFAULT_ATTRS:
            attributes.update(self.DEFAULT_ATTRS)
        for argument in self.ARGUMENTS:
            if argument.is_content:
                continue
            key = argument.name
            value = getattr(self, key, argument.default_value)
            if argument.kind == "keyword" and value == argument.default_value:
                continue
            key = self.RENAME_ATTRS.get(key, key)
            if not key:
                continue
            attributes[key] = value
        # Handle extra settings
        attributes = self._handle_extra_settings(attributes, context)
        return attributes

    def get_tag(self, context) -> str:
        return self.tag

    def get_children(self, context) -> List[Any]:
        children = []
        for argument in self.ARGUMENTS:
            if not argument.is_content:
                continue
            if argument.kind == "var":
                value = getattr(self, argument.name)
                if value is not None:
                    for child in value:
                        children.append(child)
                continue
            else:
                key = argument.name
                value = getattr(self, key, argument.default_value)
                if value is not None:
                    children.append(value)
        return children

    def get_arguments(self) -> List[str]:
        """
        Create the list of arguments to be used in the __repr__ method, which
        should be able to roundtrip back to the same component using eval.

        Returns:
            List[str]: The list of values to be used in the __repr__ method.
        """
        arguments = []
        handled_arguments = set()
        still_positional = True
        for argument in self.ARGUMENTS:
            parameter_name = argument.name
            # Don't double-render any keyword arguments that will also be in extra_settings
            if argument.kind == "keyword" and parameter_name in self.extra_settings:
                continue
            handled_arguments.add(parameter_name)
            value = getattr(self, parameter_name, argument.default_value)
            if argument.is_content:
                if argument.kind == "positional":
                    arguments.append(repr(value))
                elif argument.kind == "var":
                    for item in value:
                        arguments.append(repr(item))
                    still_positional = False
                elif argument.kind == "keyword":
                    if value != argument.default_value:
                        if still_positional:
                            arguments.append(repr(value))
                        else:
                            arguments.append(f"{parameter_name}={repr(value)}")
                    else:
                        still_positional = False
            else:
                if argument.kind == "positional":
                    arguments.append(repr(value))
                elif argument.kind == "var":
                    for item in value:
                        arguments.append(repr(item))
                    still_positional = False
                elif argument.kind == "keyword":
                    if value != argument.default_value:
                        if still_positional:
                            arguments.append(repr(value))
                        else:
                            arguments.append(f"{parameter_name}={repr(value)}")
                    else:
                        still_positional = False

        if self.extra_settings:
            for key, value in sorted(self.extra_settings.items()):
                if key in handled_arguments:
                    continue
                arguments.append(f"{key}={repr(value)}")
        return arguments

    def get_assets(self, context) -> Optional[AssetBundle]:
        return None

    def __repr__(self):
        class_name = self.__class__.__name__
        arguments = self.get_arguments()
        return f"{class_name}({', '.join(arguments)})"

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

        TODO: Should this update the fields of the component as well, if the attr corresponds to a field?

        :param attr: The key of the attribute to be updated in the dictionary.
        :type attr: str
        :param value: The value to set for the specified key in the dictionary.
        :type value: Any
        :return: The instance of the object after the update.
        :rtype: Self
        """
        self.extra_settings[attr] = value
        return self


Content = Union[Component, str]
PageContent = Union[Content, List[Content]]
