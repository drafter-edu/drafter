"""Navigation components: Link and Button with data-nav attributes."""

from dataclasses import dataclass
from typing import List

from drafter.components.base import PageContent, LinkContent, make_safe_argument
from drafter.constants import SUBMIT_BUTTON_KEY


@dataclass
class Link(PageContent, LinkContent):
    text: str
    url: str

    def __init__(self, text: str, url: str, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments
        # Generate a unique ID for this link instance to avoid namespace collisions
        self._link_id = id(self)

    def __str__(self) -> str:
        # Create a unique namespace using both link text and instance ID
        link_namespace = f"{self.text}#{self._link_id}"
        precode = self.create_arguments(self.arguments, link_namespace)
        # Use data-nav for pure client-side navigation
        return f"{precode}<a data-nav='{self.url}' {self.parse_extra_settings()}>{self.text}</a>"


@dataclass
class Button(PageContent, LinkContent):
    text: str
    url: str
    arguments: List
    external: bool = False

    def __init__(self, text: str, url: str, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments
        # Generate a unique ID for this button instance to avoid namespace collisions
        self._button_id = id(self)

    def __repr__(self):
        if self.arguments:
            return f"Button(text={self.text!r}, url={self.url!r}, arguments={self.arguments!r})"
        return f"Button(text={self.text!r}, url={self.url!r})"

    def __str__(self) -> str:
        # Create a unique namespace using both button text and instance ID
        button_namespace = f"{self.text}#{self._button_id}"
        precode = self.create_arguments(self.arguments, button_namespace)
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        value = make_safe_argument(button_namespace)
        # Use data-nav for pure client-side navigation
        # Keep type='submit' so forms can be submitted properly
        return f"{precode}<button type='submit' data-nav='{self.url}' name='{SUBMIT_BUTTON_KEY}' value='{value}' {parsed_settings}>{self.text}</button>"


SubmitButton = Button
