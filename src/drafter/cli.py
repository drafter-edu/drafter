from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from typing import Optional

import typer
from rich import print, box
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

from .server import serve_app_once
from .templating import render_index_html
from .utils import copy_assets_to, pkg_assets_dir

app = typer.Typer(add_completion=False, help="Drafter CLI")

console = Console()


def _read_user_code(py_path: Path) -> str:
    try:
        return py_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        typer.echo(f"[red]File not found:[/red] {py_path}", err=True)
        raise typer.Exit(2)


@app.command(help="Build a static index.html for a given Python file.")
def build(
    file: Path = typer.Argument(
        ..., exists=True, readable=True, help="User Python file"
    ),
    outdir: Path = typer.Option(
        Path("dist"),
        "--outdir",
        "-o",
        help="Output directory for index.html and assets.",
    ),
    title: str = typer.Option("Drafter App", "--title"),
    inline: bool = typer.Option(
        True,
        "--inline/--no-inline",
        help="Embed the user's Python source in index.html (text/python).",
    ),
    copy_assets: bool = typer.Option(
        True,
        "--copy-assets/--no-copy-assets",
        help="Copy JS/CSS assets beside index.html.",
    ),
):
    outdir.mkdir(parents=True, exist_ok=True)
    user_code = _read_user_code(file)

    # Optionally copy packaged assets next to the HTML
    assets_url: str
    if copy_assets:
        target_assets = outdir / "assets"
        copy_assets_to(target_assets)
        assets_url = "assets"
    else:
        # Serve directly from the installed package path (useful for internal hosting)
        assets_url = None  # templating will resolve to package:// path

    html = render_index_html(
        title=title,
        inline_py=inline,
        user_code=user_code if inline else None,
        python_url=str(file.resolve()) if not inline else None,
        dev_ws_url=None,
        assets_url_override=assets_url,
    )

    out = outdir / "index.html"
    out.write_text(html, encoding="utf-8")

    # Pretty summary
    table = Table.grid(padding=(0, 1))
    table.add_row("•", f"[bold]index.html[/bold] → {out}")
    if copy_assets:
        table.add_row("•", f"assets/ → {outdir / 'assets'} (copied)")
    else:
        table.add_row("•", "assets resolved from installed package")

    console.print(Panel(table, title="Build complete", border_style="green"))


@app.command(help="Run the dev server with hot reload for a given Python file.")
def serve(
    file: Path = typer.Argument(
        ..., exists=True, readable=True, help="User Python file"
    ),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    title: str = typer.Option("Drafter App", "--title"),
    inline: bool = typer.Option(
        True,
        "--inline/--no-inline",
        help="Embed the user's Python source in index.html (text/python).",
    ),
    open_browser: bool = typer.Option(
        True, "--open/--no-open", help="Open browser at start."
    ),
):
    # One-shot handoff to the server module. It will manage watch & reload.
    serve_app_once(
        user_file=str(file),
        title=title,
        host=host,
        port=port,
        inline_py=inline,
        open_browser=open_browser,
    )


if __name__ == "__main__":
    app()
