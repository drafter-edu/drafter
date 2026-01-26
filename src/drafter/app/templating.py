"""HTML template rendering for the development server.

Provides functions to load and render Jinja2 templates for the index page,
supporting multiple Python engines (Skulpt, Pyodide).
"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template

from drafter.app.utils import pkg_scaffold_dir
from drafter.site.site import DRAFTER_TAG_IDS

_env = Environment(loader=FileSystemLoader(str(pkg_scaffold_dir())), autoescape=False)


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
    title: str,
    inline_py: bool,
    user_code: Optional[str],
    python_url: Optional[str],
    dev_ws_url: Optional[str],
    assets_url: Optional[str] = None,
    compiled_body: str = "",
    compiled_headers: str = "",
    engine: str = "skulpt",
    mount_drafter_locally: bool = False,
) -> str:
    """Render the index HTML page with provided configuration.

    Loads the appropriate template for the engine and renders it with the
    provided values. The assets_url parameter controls how assets are served.

    Args:
        title: Page title.
        inline_py: Whether Python code is inlined in HTML.
        user_code: User Python code to inline (if inline_py=True).
        python_url: URL to load user code from (if inline_py=False).
        dev_ws_url: WebSocket URL for live reload.
        assets_url: Asset URL prefix (None for package defaults).
        compiled_body: Pre-rendered HTML body content.
        compiled_headers: Pre-rendered header content.
        engine: Python engine name ('skulpt' or 'pyodide').
        mount_drafter_locally: Whether to mount Drafter locally.

    Returns:
        Rendered HTML string ready to send to client.
    """
    template = _load_template_text(engine)

    def static(asset_name: str) -> str:
        return f"{assets_url}/{asset_name}"

    return template.render(
        title=title,
        inline_py=inline_py,
        user_code=user_code or "",
        python_url=python_url or "",
        dev_ws_url=dev_ws_url,
        drafter_root=DRAFTER_TAG_IDS["ROOT"],
        assets_url=assets_url or "",
        compiled_body=compiled_body,
        compiled_headers=compiled_headers,
        mount_drafter_locally=mount_drafter_locally,
        static=static,
    )
