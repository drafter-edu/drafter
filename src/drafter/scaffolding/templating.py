"""HTML template rendering for the development server.

Provides functions to load and render Jinja2 templates for the index page,
supporting multiple Python engines (Skulpt, Pyodide).
"""

import hashlib
import os
from base64 import b64encode
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, Template

from drafter.config.system import SystemConfiguration
from drafter.scaffolding.utils import pkg_scaffold_dir
from drafter.site.site import DRAFTER_TAG_IDS
from drafter.version import CURRENT_DRAFTER_VERSION

_env = Environment(loader=FileSystemLoader(str(pkg_scaffold_dir())), autoescape=False)


@lru_cache(maxsize=1)
def default_favicon_data_uri() -> str:
    """Return the built-in Drafter favicon as an inline data URI.

    Inlining the SVG keeps the default favicon working in every mode (dev
    server, static build, downloaded single-file pages) without needing a
    served asset path.

    Returns:
        A `data:image/svg+xml;base64,...` URI for `scaffolding/favicon.svg`.
    """
    favicon_bytes = (pkg_scaffold_dir() / "favicon.svg").read_bytes()
    return "data:image/svg+xml;base64," + b64encode(favicon_bytes).decode("ascii")


MAIN_FILE_ID_LENGTH = 16
"""Number of hexadecimal digits kept from the hash in `main_file_id`."""


def main_file_id(system: SystemConfiguration) -> str:
    """Identify the student's main file without revealing where it is.

    The page stores a few things in the browser (the debug panel's save
    slots, the theme picked in the theme switcher, the open debug tab).
    Browser storage is shared by every page at one address, and every
    program the development server runs is at the same address, so the
    page's script keys those values by this id as well (see
    js/src/storage_keys.ts). The id is a hash of the file's full path, so
    two files with the same name in different folders get different ids,
    and the folder names (which usually include the student's user name)
    never reach the page or the browser's storage.

    Args:
        system: System configuration, whose bootstrap section holds the
            path to the main file.

    Returns:
        A short hexadecimal id, or an empty string when no main file path
        is known.

    Example:
        ```python
        main_file_id(system)  # "3f9a0c1d5e7b2a44"
        ```
    """
    path = system.bootstrap.path
    if not path:
        return ""
    full_path = os.path.normcase(os.path.abspath(path))
    digest = hashlib.sha256(full_path.encode("utf-8")).hexdigest()
    return digest[:MAIN_FILE_ID_LENGTH]


def _load_template_text(engine: str) -> Template:
    """Load the index HTML template for the specified engine.

    Args:
        engine: The Python engine name (e.g., 'skulpt', 'pyodide').

    Returns:
        Jinja2 Template object.
    """
    return _env.get_template(f"index.{engine}.template.html")


def render_index_html(
    *,
    system: SystemConfiguration,
    modified_system: dict,
    inline_py: bool,
    user_code: str | None,
    python_url: str | None,
    dev_ws_url: str | None,
    assets_url: str | None = None,
    compiled_body: str = "",
    compiled_headers: str = "",
    pyodide_drafter_path: str = "",
) -> str:
    """Render the index HTML page with provided configuration.

    Loads the appropriate template for the engine and renders it with the
    provided values. The assets_url parameter controls how assets are served.
    Asset URLs written by the template end in a `?v=<Drafter version>` query,
    so upgrading Drafter changes them and a browser cannot reuse a script it
    cached from an older release.

    Args:
        system: System configuration; selects the engine template and is
            exposed to the template (along with its JSON form and the
            site title).
        modified_system: Dict of configuration values that differ from
            the defaults, made available to the template (an empty dict
            when falsy).
        inline_py: Whether Python code is inlined in HTML.
        user_code: User Python code to inline (if inline_py=True).
        python_url: URL to load user code from (if inline_py=False).
        dev_ws_url: WebSocket URL for live reload.
        assets_url: Asset URL prefix (None for package defaults).
        compiled_body: Pre-rendered HTML body content.
        compiled_headers: Pre-rendered header content.
        pyodide_drafter_path: Where Pyodide should load the drafter
            package from — an asset path to a built zip or a pip
            requirement spec (e.g. `drafter==<version>`); empty to use
            the default.

    Returns:
        Rendered HTML string ready to send to client.
    """
    template = _load_template_text(system.app_common.engine)

    def static(asset_name: str) -> str:
        # The version query gives every Drafter release its own asset URLs,
        # so a browser never pairs this page with a bundle it cached from an
        # older release (whose Pyodide loader would not match the Pyodide
        # version this page points at).
        return f"{assets_url}/{asset_name}?v={CURRENT_DRAFTER_VERSION}"

    return template.render(
        # General variables
        system=system,
        system_json=system.to_json(),
        modified_system=modified_system or {},
        main_file_id=main_file_id(system),
        # Specific variables
        title=system.app_common.site_title,
        favicon=system.app_common.favicon or default_favicon_data_uri(),
        favicon_id=DRAFTER_TAG_IDS["FAVICON"],
        inline_py=inline_py,
        user_code=user_code or "",
        python_url=python_url or "",
        dev_ws_url=dev_ws_url,
        drafter_root=DRAFTER_TAG_IDS["ROOT"],
        assets_url=assets_url or "",
        compiled_body=compiled_body,
        compiled_headers=compiled_headers,
        pyodide_drafter_path=pyodide_drafter_path,
        static=static,
    )
