from importlib.resources import files
from typing import Optional
from jinja2 import Environment, BaseLoader
from pathlib import Path

from drafter.app.utils import pkg_scaffold_dir
from drafter.site.site import DRAFTER_TAG_IDS

_env = Environment(loader=BaseLoader(), autoescape=False)


def _load_template_text() -> str:
    path = pkg_scaffold_dir() / "index.template.html"
    return path.read_text(encoding="utf-8")


def render_index_html(
    *,
    title: str,
    inline_py: bool,
    user_code: Optional[str],
    python_url: Optional[str],
    dev_ws_url: Optional[str],
    assets_url_override: Optional[str] = None,
) -> str:
    """
    assets_url_override:
      - "assets" to use /assets (dev server)
      - None to point to package files via /assets (still works in dev)
    """
    template = _env.from_string(_load_template_text())

    def static(asset_name: str) -> str:
        # In dev we mount /assets → package dir, and in build we copy to ./assets
        if assets_url_override:
            return f"{assets_url_override}/{asset_name}"
        return f"assets/{asset_name}"

    return template.render(
        title=title,
        inline_py=inline_py,
        user_code=user_code or "",
        python_url=python_url or "",
        dev_ws_url=dev_ws_url,
        drafter_root=DRAFTER_TAG_IDS["ROOT"],
        static=static,
    )
