"""HTML template rendering for the development server.

Provides functions to load and render Jinja2 templates for the index page,
supporting multiple Python engines (Skulpt, Pyodide).
"""

from base64 import b64encode
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, Template

from drafter.config.system import SystemConfiguration
from drafter.scaffolding.utils import pkg_scaffold_dir
from drafter.site.site import DRAFTER_TAG_IDS

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
        return f"{assets_url}/{asset_name}"

    return template.render(
        # General variables
        system=system,
        system_json=system.to_json(),
        modified_system=modified_system or {},
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
