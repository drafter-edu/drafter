# Helper function to render different SiteInformationType values
def render_site_info(self, value: SiteInformationType) -> str:
    if isinstance(value, PageContent):
        # If it's PageContent, render it using its render method
        return value.render(self._state, self.configuration)
    elif isinstance(value, (list, tuple)):
        # If it's a list/tuple of strings, render as an unordered list with links converted to <a> tags
        items = []
        for item in value:
            if isinstance(item, str):
                # Check if the item looks like a URL
                if is_external_url(item):
                    items.append(
                        f'<a href="{html.escape(item)}">{html.escape(item)}</a>'
                    )
                else:
                    items.append(html.escape(item))
            else:
                items.append(str(item))
        items_html = "\n".join(f"<li>{item}</li>" for item in items)
        return f"<ul>{items_html}</ul>"
    else:
        # If it's a string, render as text with links converted to <a> tags
        value_str = str(value)
        # Check if the value looks like a URL
        if is_external_url(value_str):
            return f'<a href="{html.escape(value_str)}">{html.escape(value_str)}</a>'
        else:
            return html.escape(value_str)


def about(self):
    """
    Generates the "About" page based on default information.
    :return:
    """
    if not self._site_information:
        return "No site information has been set. Use the <code>set_site_information()</code> function to set the information about your site."

    # Build the about page content
    content_parts = []
    site_parts = [
        ("Author", self._site_information.author),
        ("Description", self._site_information.description),
        ("Sources", self._site_information.sources),
        ("Planning", self._site_information.planning),
        ("Links", self._site_information.links),
    ]

    for title, content in site_parts:
        if content:
            content_parts.append(f"<h2>{title}</h2>")
            content_parts.append(f"<div>{self.render_site_info(content)}</div>")

    # Add external pages if configured
    if self.configuration.external_pages:
        content_parts.append("<h2>External Pages</h2>")
        external_items = []
        # Parse semicolon-separated format: "URL Text;URL Text;..."
        for entry in self.configuration.external_pages.split(";"):
            entry = entry.strip()
            if not entry:
                continue
            # Split on first whitespace to separate URL from optional label
            parts = entry.split(None, 1)
            if len(parts) == 2:
                url, label = parts
                external_items.append(
                    f'<a href="{html.escape(url)}">{html.escape(label)}</a>'
                )
            elif len(parts) == 1:
                url = parts[0]
                external_items.append(
                    f'<a href="{html.escape(url)}">{html.escape(url)}</a>'
                )
        if external_items:
            items_html = "\n".join(f"<li>{item}</li>" for item in external_items)
            content_parts.append(f"<ul>{items_html}</ul>")

    # Back button
    content_parts.append(
        '<p><a href="/" class="btlw-back">← Back to the main page</a></p>'
    )

    return "\n".join(content_parts)
