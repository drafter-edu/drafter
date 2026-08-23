"""User-facing functions for configuring site appearance and deployment.

Provides convenience wrappers around ClientServer.reconfigure for settings
such as debug information visibility, site title, theme, framing, custom
header/CSS content, and site metadata.
"""

from typing import Any

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server
from drafter.data.errors import StudentFacingError
from drafter.files.website_files import is_url, resolve_website_file


def hide_debug_information(server: ClientServer | None = None):
    """
    Hides debug information from the website, so that it will not appear. Useful
    for deployed websites.

    Args:
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(in_debug_mode=False)


def show_debug_information(server: ClientServer | None = None):
    """
    Shows debug information on the website. Useful for development.

    Args:
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(in_debug_mode=True)


def set_website_title(title: str, server: ClientServer | None = None):
    """
    Sets the title of the website, as it appears in the browser tab.

    Args:
        title: The title of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(site_title=title)


def set_website_favicon(favicon: str, server: ClientServer | None = None):
    """
    Sets the favicon of the website, the small icon shown in the browser tab.
    Give the name of an image file (svg, png, ico, ...) next to your Python
    file, or a full URL to an image. By default, websites use the built-in
    Drafter icon.

    Args:
        favicon: The path or URL of the image to use as the favicon.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(favicon=favicon)


def set_website_framed(framed: bool, server: ClientServer | None = None):
    """
    Sets whether the website should be framed or not. If you are deploying the website, then
    this would be a common thing to set to False.

    Args:
        framed: Whether the website should be framed or not.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(framed=framed)


def set_site_information(
    author,
    description,
    sources,
    planning,
    links,
    server: ClientServer | None = None,
):
    """
    Sets the information about the website, such as the author, description,
    sources, planning information, and related links.

    Args:
        author: The author of the website.
        description: Description of the website.
        sources: Sources used in the website.
        planning: Planning information.
        links: Related links.
        server: The server to configure. If None, uses the main server.

    Returns:
        None
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(
        author=author,
        description=description,
        sources=sources,
        planning=planning,
        links=links,
    )


def get_site_information(server: ClientServer | None = None):
    """
    Gets the information about the website, such as the author, description, sources.

    Args:
        server: The server to query. If None, uses the main server.

    Returns:
        The site information configuration.
    """
    if server is None:
        server = get_main_server()
    return server.get_config_setting("information")


def set_website_style(style: str | None, server: ClientServer | None = None):
    """
    Sets the style of the website. This must be the name of a valid theme.

    Args:
        style: The theme of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if style is None:
        style = "none"
    server.reconfigure(theme=style)


def set_website_theme(theme: str | None, server: ClientServer | None = None):
    """
    Sets the theme of the website. This must be the name of a valid theme.

    Args:
        theme: The theme of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if theme is None:
        theme = "none"
    server.reconfigure(theme=theme)


def set_page_transition(
    transition: str | None = "fade",
    duration: float | None = None,
    server: ClientServer | None = None,
):
    """
    Sets a site-wide visual transition that plays whenever the user navigates
    between pages. By default, pages change instantly; this setting makes the
    new page fade in instead.

    The transition can be:

    - `"fade"` (or `"transparent"`): the new page fades in from transparent.
    - A CSS color such as `"black"`, `"white"`, or `"#004488"`: the new page
      fades in from a solid veil of that color.
    - `"none"` (or `None`): disables the transition again.

    Args:
        transition: The transition style ("fade", "none", or a CSS color).
        duration: How long the transition lasts, in seconds. If not given,
            the current duration (0.5 seconds by default) is kept.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if transition is None:
        transition = "none"
    elif transition == "transparent":
        transition = "fade"
    server.reconfigure(page_transition=transition)
    if duration is not None:
        server.reconfigure(page_transition_duration=float(duration))


def set_error_page(
    title: str | None = None,
    message: str | None = None,
    show_details: bool | None = None,
    server: ClientServer | None = None,
):
    """
    Customizes the content of the built-in error page.

    Args:
        title: A custom heading to show instead of "Something Went Wrong".
        message: A custom friendly message to show instead of the default
            explanation of what went wrong.
        show_details: Whether the technical details (error message,
            traceback, etc.) are included. Set to False for deployed sites
            where users should not see tracebacks.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if title is not None:
        server.reconfigure(error_page_title=title)
    if message is not None:
        server.reconfigure(error_page_message=message)
    if show_details is not None:
        server.reconfigure(error_page_show_details=bool(show_details))


def set_button_spinners(enabled: bool = True, server: ClientServer | None = None):
    """
    Enables or disables loading spinners on buttons: while a pressed
    button's request is being processed, the button shows a small spinner
    and is temporarily disabled.

    Args:
        enabled: Whether buttons should show loading spinners.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(button_spinners=bool(enabled))


def set_browser_history(enabled: bool = True, server: ClientServer | None = None):
    """
    Enables or disables mirroring navigation into the browser's history
    stack. When enabled (the default for standalone sites), the browser's
    back/forward buttons time travel through the app, restoring each page's
    state. When disabled, Drafter never touches the browser's history or
    URL, so the back button leaves the page — the right behavior for an app
    embedded in another page (documentation demos disable it
    automatically).

    Call before start_server(); the setting is read when the site boots.

    Args:
        enabled: Whether to mirror navigation into browser history.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(browser_history=bool(enabled))


def add_website_header(header: str, server: ClientServer | None = None):
    """
    Adds additional header content to the website. This is useful for adding custom
    CSS or JavaScript to the website, or other arbitrary header tags like meta tags.

    Args:
        header: The raw header content to add. This will not be wrapped in additional tags.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(additional_header_content=header)


def add_website_css(
    selector: str, css: str | None = None, server: ClientServer | None = None
):
    """
    Adds additional CSS content to the website. This is useful for adding custom
    CSS to the website, either for specific selectors or for general styles.
    If you only provide one parameter, it will be used as raw CSS content.
    If you provide both parameters, they will be used to create a CSS rule; the first parameter
    is the CSS selector, and the second parameter is the CSS content that will be wrapped in {}.

    Args:
        selector: The CSS selector to apply the CSS to, or the CSS content if the second parameter is None.
        css: The CSS content to apply to the selector.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if css is None:
        _reject_filename_given_as_code(selector, "add_website_css", "css")
        # Treat selector as raw CSS content
        server.reconfigure(additional_style_content=selector)
    else:
        # Create a CSS rule from selector and content
        server.reconfigure(additional_style_content=f"{selector} {{{css}}}\n")


def _reject_filename_given_as_code(content: str, function_name: str, kind: str):
    """Raise a helpful error when a file name was passed to an inline helper.

    `add_website_css("style.css")` is a common slip: the student meant to
    link the file, but the helper would inject the literal text "style.css"
    as CSS and silently do nothing useful.

    Args:
        content: The argument the inline helper received.
        function_name: The inline helper's name (for the message).
        kind: "css" or "js", selecting the file-based helper to suggest.

    Raises:
        StudentFacingError: If `content` is a bare file name or URL.
    """
    if not isinstance(content, str):
        return
    stripped = content.strip()
    if not stripped or any(ch.isspace() for ch in stripped):
        return
    if any(marker in stripped for marker in "{};()"):
        return
    extensions = (".css",) if kind == "css" else (".js", ".mjs")
    if not stripped.lower().endswith(extensions) and not is_url(stripped):
        return
    language = "CSS" if kind == "css" else "JavaScript"
    file_helper = f"{function_name}_file"
    example = (
        "add_website_css('h1', 'color: red;')"
        if kind == "css"
        else "add_website_js('console.log(\"hello\");')"
    )
    raise StudentFacingError(
        f"{function_name}: got a file name or URL ({stripped!r}) instead of"
        f" {language} code",
        friendly=(
            f"{function_name} expects {language} code written directly in your"
            f" program, but '{stripped}' looks like the name of a file or a URL."
            f" Adding it as {language} would do nothing."
        ),
        steps=(
            f"To add a {language} file to every page, use"
            f" {file_helper}('{stripped}') instead.",
            f"To write {language} directly, pass the code itself, for example"
            f" {example}.",
        ),
        title=f"File Name Given Instead of {language}",
    )


def _add_registered_file(server: ClientServer, key: str, value: str) -> None:
    """Append `value` to the list-valued config `key` unless already present.

    Args:
        server: The server whose configuration is updated.
        key: A list-valued configuration key (e.g. `additional_files`).
        value: The path or URL to register.
    """
    current = server.get_config_setting(key) or []
    if value in current:
        return
    update: dict[str, Any] = {key: value}
    server.reconfigure(**update)


def add_website_css_file(path: str, server: ClientServer | None = None):
    """
    Adds a CSS file to every page.

    `path` may be the path to a CSS file next to the student's program,
    or a full URL to a stylesheet.

    A file next to the program is checked right away: if it cannot be
    found, a friendly error explains where Drafter looked and suggests
    similarly named files. The file is also registered like
    `add_website_file`, so it travels with the site when it is built.

    Args:
        path: The path of a `.css` file next to your program (such as
            `"style.css"` or `"static/style.css"`), or a full URL.
        server: The server to configure. If None, uses the main server.

    Raises:
        StudentFacingError: If the path is not a string, looks like CSS code
            rather than a file name, is not a `.css` file, or cannot be found.
    """
    if server is None:
        server = get_main_server()
    resolved = resolve_website_file(path, "add_website_css_file", kind="css")
    if not is_url(resolved):
        _add_registered_file(server, "additional_files", resolved)
    _add_registered_file(server, "additional_css_files", resolved)


def add_website_js(js: str, server: ClientServer | None = None):
    """
    Adds JavaScript code to every page. The code runs once, when the site
    first loads, before any page content is shown.

    Args:
        js: The raw JavaScript code to run.
        server: The server to configure. If None, uses the main server.

    Raises:
        StudentFacingError: If the argument looks like a file name or URL
            rather than code (use `add_website_js_file` for those).
    """
    if server is None:
        server = get_main_server()
    _reject_filename_given_as_code(js, "add_website_js", "js")
    server.reconfigure(additional_js_content=js)


def add_website_js_file(path: str, server: ClientServer | None = None):
    """
    Adds a JavaScript file to every page.

    `path` may be the path to a `.js` file next to the student's program,
    or a full URL to a script. Files next to the program are checked right
    away (with suggestions for similarly named files when missing) and are
    registered like `add_website_file`, so they travel with the built site.

    Args:
        path: The path of a `.js` file next to your program (such as
            `"app.js"`), or a full URL.
        server: The server to configure. If None, uses the main server.

    Raises:
        StudentFacingError: If the path is not a string, looks like
            JavaScript code rather than a file name, is not a `.js` file,
            or cannot be found.
    """
    if server is None:
        server = get_main_server()
    resolved = resolve_website_file(path, "add_website_js_file", kind="js")
    if not is_url(resolved):
        _add_registered_file(server, "additional_files", resolved)
    _add_registered_file(server, "additional_js_files", resolved)


def add_website_file(*filenames: str, server: ClientServer | None = None):
    """
    Registers files next to the student's program as part of the website,
    so that they are copied into the built site when it is deployed.

    Use this for files the site needs at runtime (data files that are
    `open()`ed, images, fonts, and so on). Each file is checked right
    away; a missing file raises a friendly error that suggests similarly
    named files.

    Args:
        filenames: One or more paths, relative to your program's folder
            (such as `"words.txt"` or `"images/logo.png"`).
        server: The server to configure. If None, uses the main server.

    Raises:
        StudentFacingError: If no filenames are given, or if any path is
            not a string, is a URL or absolute path, or cannot be found.
    """
    if server is None:
        server = get_main_server()
    if not filenames:
        raise StudentFacingError(
            "add_website_file: no filenames were given",
            friendly=(
                "add_website_file needs at least one file name, but it was called"
                " with nothing."
            ),
            steps=("Call it like add_website_file('words.txt', 'logo.png').",),
            title="No Website Files Given",
        )
    resolved_paths = []
    for filename in filenames:
        if isinstance(filename, str) and is_url(filename):
            raise StudentFacingError(
                "add_website_file: expected a file next to your program, got a"
                f" URL: {filename!r}",
                friendly=(
                    "add_website_file only works with files next to your program,"
                    f" but '{filename}' is a URL. Files on other websites do not"
                    " need to be added; your site can use them directly."
                ),
                steps=(
                    "Remove this call, and use the URL directly where you need it"
                    " (for example in Image(...), add_website_css_file(...), or"
                    " add_website_js_file(...)).",
                ),
                title="Website File Must Be Next to Your Program",
            )
        resolved_paths.append(
            resolve_website_file(filename, "add_website_file", kind="file")
        )
    for resolved in resolved_paths:
        _add_registered_file(server, "additional_files", resolved)


def deploy_site(image_folder="images", server: ClientServer | None = None):
    """
    Prepares the website for deployment. Currently this only turns off debug
    information; the `image_folder` argument is accepted for compatibility
    but is not yet used.

    Args:
        image_folder: The folder where images are stored (currently unused).
        server: The server to configure. If None, uses the main server.
    """
    hide_debug_information(server=server)
    # TODO: Implement production mode and image folder in V2
    pass
