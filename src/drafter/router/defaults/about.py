from drafter.client_server.client_server import ClientServer
from drafter.payloads.kinds.page import Page
from drafter.components import (
    Paragraph,
    Header,
    InlineCode,
    Link,
    BulletedList,
    Button,
)


def default_about(state, _server: ClientServer):
    """Generate the About page from site information settings.

    Displays author, description, sources, planning, and links sections.
    Includes external pages if configured, and a back button.

    Returns:
        str: Complete HTML for the About page.
    """
    configuration = _server.get_current_configuration()
    if not configuration.information:
        return Page(
            state,
            [
                Paragraph(
                    "No site information has been set. Use the ",
                    InlineCode("set_site_information()"),
                    " function to set the information about your site.",
                )
            ],
        )

    # Build the about page content
    information = configuration.information
    content_parts = []
    site_parts = list(information.get_parts())

    for title, content in site_parts:
        if content:
            content_parts.append(Header(title, level=2))
            content_parts.append(content)

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
            external_items.append(Link(url, label))
        if external_items:
            content_parts.append(BulletedList(external_items))

    content_parts.append(Button("Back to Index (Main Page)", "index"))

    return Page(state, content_parts)


# # Helper function to render different SiteInformationType values
# def render_site_info(self, value: SiteInformationType) -> str:
#     """Convert site information values to HTML.

#     Handles PageContent objects, lists/tuples (rendered as lists),
#     and strings. Detects and converts URLs to clickable links.

#     Args:
#         value: Site information to render.

#     Returns:
#         str: HTML representation of the value.
#     """
#     # TODO: Need a "is_page_content" helper to properly typecheck
#     # TODO: This whole function seems broken
#     if isinstance(value, PageContent):
#         # If it's PageContent, render it using its render method
#         return value.render(self._state, self.configuration)
#     elif isinstance(value, (list, tuple)):
#         # If it's a list/tuple of strings, render as an unordered list with links converted to <a> tags
#         items = []
#         for item in value:
#             if isinstance(item, str):
#                 # Check if the item looks like a URL
#                 if is_external_url(item):
#                     items.append(
#                         f'<a href="{html.escape(item)}">{html.escape(item)}</a>'
#                     )
#                 else:
#                     items.append(html.escape(item))
#             else:
#                 items.append(str(item))
#         items_html = "\n".join(f"<li>{item}</li>" for item in items)
#         return f"<ul>{items_html}</ul>"
#     else:
#         # If it's a string, render as text with links converted to <a> tags
#         value_str = str(value)
#         # Check if the value looks like a URL
#         if is_external_url(value_str):
#             return f'<a href="{html.escape(value_str)}">{html.escape(value_str)}</a>'
#         else:
#             return html.escape(value_str)


# # Add external pages if configured
# if self.configuration.external_pages:
#     content_parts.append("<h2>External Pages</h2>")
#     external_items = []
#     # Parse semicolon-separated format: "URL Text;URL Text;URL;..."
#     for entry in self.configuration.external_pages.split(";"):
#         entry = entry.strip()
#         if not entry:
#             continue
#         # Split on first whitespace to separate URL from optional label
#         parts = entry.split(None, 1)
#         if len(parts) == 2:
#             url, label = parts
#             external_items.append(
#                 f'<a href="{html.escape(url)}">{html.escape(label)}</a>'
#             )
#         elif len(parts) == 1:
#             url = parts[0]
#             external_items.append(
#                 f'<a href="{html.escape(url)}">{html.escape(url)}</a>'
#             )
#     if external_items:
#         items_html = "\n".join(f"<li>{item}</li>" for item in external_items)
#         content_parts.append(f"<ul>{items_html}</ul>")
