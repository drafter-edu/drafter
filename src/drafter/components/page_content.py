from typing import List, Optional, Union

from drafter.components.utilities.attributes import BASELINE_ATTRS
from drafter.urls import remap_attr_styles


class Component:
    """
    Base class for all content that can be added to a page.
    This class is not meant to be used directly, but rather to be subclassed by other classes.
    Critically, each subclass must implement a ``__str__`` method that returns the HTML representation.

    Under most circumstances, a string value can be used in place of a ``PageContent`` object
    (in which case we say it is a ``Content`` type). However, the ``PageContent`` object
    allows for more customization and control over the content.

    Ultimately, the ``PageContent`` object is converted to a string when it is rendered.

    This class also has some helpful methods for verifying URLs and handling attributes/styles.
    """

    EXTRA_ATTRS: List[str] = []
    extra_settings: dict

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
        for key, value in raw_attrs.items():
            if key not in self.EXTRA_ATTRS and key not in BASELINE_ATTRS:
                styles.append(f"{key}: {value}")
            else:
                # TODO: Is this safe enough?
                attrs.append(f"{key}={str(value)!r}")
        for key, value in raw_styles.items():
            styles.append(f"{key}: {value}")
        result = " ".join(attrs)
        if styles:
            result += f" style='{'; '.join(styles)}'"
        return result

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

    def render(self, current_state, configuration):
        """
        This method is called when the component is being rendered to a string. It should return
        the HTML representation of the component, using the current State and configuration to
        determine the final output.

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        :return: The HTML representation of the component
        """
        return str(self)


Content = Union[Component, str]
PageContent = Union[Content, List[Content]]
