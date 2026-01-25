from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template

from drafter.app.utils import pkg_scaffold_dir
from drafter.site.site import DRAFTER_TAG_IDS

_env = Environment(loader=FileSystemLoader(str(pkg_scaffold_dir())), autoescape=False)


def _load_template_text(engine: str) -> Template:
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
    """
    assets_url_override:
      - "assets" to use /assets (dev server)
      - None to point to package files via /assets (still works in dev)
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
