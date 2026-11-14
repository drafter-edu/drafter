"""Default "about" route, rendering the configured site information page."""

import html

from drafter.client_server.client_server import ClientServer
from drafter.components import (
    BulletedList,
    Button,
    Header,
    InlineCode,
    Link,
    Paragraph,
    RawHTML,
)
from drafter.components.page_content import Component, PageContent
from drafter.helpers.urls import is_external_url
from drafter.payloads.kinds.page import Page

FILE_LINK_SECTIONS = ("Planning",)
"""Site information sections whose entries name files published with the
site (such as `plan.pdf` or `My Plan.pdf`), so every string there becomes a
link to the file of that name, as in Drafter 1."""


def make_file_link(url: str, label: str) -> RawHTML:
    """Create a link to a file or folder published alongside the site.

    A `Link` always means "go to this route" unless its address starts with
    `http://` or `https://`, so it cannot point at `plan.pdf` or
    `dashboard/`. This plain anchor is followed by the browser itself, which
    resolves the address against the page's own folder (the right place on
    a site deployed under a path, like `https://user.github.io/project/`).

    Args:
        url: The address of the file, usually relative to the site.
        label: The text shown for the link.

    Returns:
        An anchor element with the address and label escaped.
    """
    return RawHTML(f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>')


def render_information_text(text: str, link_files: bool) -> PageContent:
    """Convert one string of site information into page content.

    Args:
        text: The string to convert.
        link_files: Whether the string names a file published with the
            site, and so becomes a link to that file. File names may
            contain spaces.

    Returns:
        A `Link` for a web address, a file link for any other non-blank
        string when `link_files` is set, and otherwise the text unchanged.
    """
    if is_external_url(text):
        return Link(text, text)
    if link_files and text.strip():
        return make_file_link(text.strip(), text)
    return text


def render_information_value(value, link_files: bool = False) -> list[PageContent]:
    """Convert one site-information value into renderable page content.

    Strings that look like URLs become links; lists and tuples become
    bulleted lists (with each entry converted the same way); components
    pass through unchanged.

    Args:
        value: A site information field value (str, list, tuple, or
            component).
        link_files: Whether every string is the name of a file published
            with the site (such as `plan.pdf`) and becomes a link to it.

    Returns:
        A list of content items to append to the page (possibly empty).
    """
    if isinstance(value, str):
        if not value:
            return []
        return [render_information_text(value, link_files)]
    if isinstance(value, Component):
        return [value]
    if isinstance(value, (list, tuple)):
        items: list[PageContent] = []
        for item in value:
            if isinstance(item, str):
                items.append(render_information_text(item, link_files))
            elif isinstance(item, Component):
                items.append(item)
            else:
                items.append(str(item))
        if not items:
            return []
        return [BulletedList(items)]
    return [str(value)]


def parse_external_page(entry) -> tuple[str, str] | None:
    """Split one configured external page into its address and link text.

    An entry is a `"URL"` string (the address doubles as the text), a
    `"URL Text"` string (everything after the first space is the text, as
    in `--external-pages "dashboard/ Dashboard"`), or a `(URL, Text)` pair.

    Args:
        entry: One item of the `external_pages` setting.

    Returns:
        The `(url, text)` pair, or None for a blank entry.

    Raises:
        ValueError: If the entry is not a string or a pair of strings.
    """
    if isinstance(entry, str):
        parts = entry.strip().split(None, 1)
        if not parts:
            return None
        return parts[0], parts[-1]
    if (
        isinstance(entry, (tuple, list))
        and len(entry) == 2
        and all(isinstance(part, str) for part in entry)
    ):
        return entry[0].strip(), entry[1].strip()
    raise ValueError("Invalid external page format in configuration: " + repr(entry))


def default_about(state, _server: ClientServer):
    """Generate the About page from site information settings.

    Displays the site title plus the author, description, sources,
    planning, and links sections that have been filled in. Each string in
    the planning section links to the file of that name. Includes external
    pages if configured, and a back button.

    Args:
        state: Current application state, passed through to the returned Page.
        _server: The running ClientServer; the underscore prefix marks this as
            a framework-injected parameter, so it is supplied automatically
            rather than from the request payload.

    Returns:
        Page: The About page, or a fallback Page explaining how to set site
        information when none has been configured.

    Raises:
        ValueError: If an `external_pages` entry is not a string or a pair
            of strings.
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
        rendered = render_information_value(
            content, link_files=section_title in FILE_LINK_SECTIONS
        )
        if rendered:
            content_parts.append(Header(section_title, level=2))
            content_parts.extend(rendered)

    if configuration.external_pages:
        external_items: list[PageContent] = []
        for page_item in configuration.external_pages:
            parsed = parse_external_page(page_item)
            if parsed is None:
                continue
            url, label = parsed
            if is_external_url(url):
                external_items.append(Link(label, url))
            else:
                # A page published next to the site, such as the deployment
                # dashboard at "dashboard/"; a Link would treat it as a route.
                external_items.append(make_file_link(url, label))
        if external_items:
            content_parts.append(Header("External Pages", level=2))
            content_parts.append(BulletedList(external_items))

    content_parts.append(Button("Back to Index (Main Page)", "index"))

    return Page(state, content_parts)
