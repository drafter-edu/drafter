"""Default "about" route, rendering the configured site information page."""

from drafter.client_server.client_server import ClientServer
from drafter.components import (
    BulletedList,
    Button,
    Header,
    InlineCode,
    Link,
    Paragraph,
)
from drafter.components.page_content import Component, PageContent
from drafter.helpers.urls import is_external_url
from drafter.payloads.kinds.page import Page


def render_information_value(value) -> list[PageContent]:
    """Convert one site-information value into renderable page content.

    Strings that look like URLs become links; lists and tuples become
    bulleted lists (with each entry converted the same way); components
    pass through unchanged.

    Args:
        value: A site information field value (str, list, tuple, or
            component).

    Returns:
        A list of content items to append to the page (possibly empty).
    """
    if isinstance(value, str):
        if not value:
            return []
        if is_external_url(value):
            return [Link(value, value)]
        return [value]
    if isinstance(value, Component):
        return [value]
    if isinstance(value, (list, tuple)):
        items: list[PageContent] = []
        for item in value:
            if isinstance(item, str) and is_external_url(item):
                items.append(Link(item, item))
            elif isinstance(item, (Component, str)):
                items.append(item)
            else:
                items.append(str(item))
        if not items:
            return []
        return [BulletedList(items)]
    return [str(value)]


def default_about(state, _server: ClientServer):
    """Generate the About page from site information settings.

    Displays the site title plus the author, description, sources,
    planning, and links sections that have been filled in. Includes
    external pages if configured, and a back button.

    Args:
        state: Current application state, passed through to the returned Page.
        _server: The running ClientServer; the underscore prefix marks this as
            a framework-injected parameter, so it is supplied automatically
            rather than from the request payload.

    Returns:
        Page: The About page, or a fallback Page explaining how to set site
        information when none has been configured.
    """
    configuration = _server.get_current_configuration()
    title = getattr(configuration, "site_title", "") or ""
    if not configuration.information:
        return Page(
            state,
            [
                Header(f"About {title}".strip(), level=1),
                Paragraph(
                    "No site information has been set. Use the ",
                    InlineCode("set_site_information()"),
                    " function to set the information about your site.",
                ),
                Button("Back to Index (Main Page)", "index"),
            ],
        )

    # Build the about page content
    information = configuration.information
    content_parts: list[PageContent | str] = [Header(f"About {title}".strip(), level=1)]

    for section_title, content in information.get_parts():
        rendered = render_information_value(content)
        if rendered:
            content_parts.append(Header(section_title, level=2))
            content_parts.extend(rendered)

    if configuration.external_pages:
        content_parts.append(Header("External Pages", level=2))
        external_items = []
        for page_item in configuration.external_pages:
            if isinstance(page_item, tuple) and len(page_item) == 2:
                url, label = page_item
            elif isinstance(page_item, str):
                url, label = page_item, page_item
            else:
                raise ValueError(
                    "Invalid external page format in configuration: " + repr(page_item)
                )
            external_items.append(Link(label, url))
        if external_items:
            content_parts.append(BulletedList(external_items))

    content_parts.append(Button("Back to Index (Main Page)", "index"))

    return Page(state, content_parts)
