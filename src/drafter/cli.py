from __future__ import annotations

from pathlib import Path
from typing import List

import typer
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

from drafter.app.app_server import serve_app_once
from drafter.app.templating import render_index_html
from drafter.app.utils import copy_assets_to
from drafter.files import TEMPLATE_SKULPT_DEPLOY, DEPLOYED_404_TEMPLATE_HTML
from drafter.raw_files import get_raw_files

app = typer.Typer(add_completion=False, help="Drafter CLI")

console = Console()


def protect_script_tags(content: str) -> str:
    """
    Protects `<script>` tags in the given HTML content by escaping them.
    """
    return content.replace("<script", "&lt;script").replace(
        "</script>", "&lt;/script&gt;"
    )


def _read_user_code(py_path: Path) -> str:
    try:
        return py_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        typer.echo(f"[red]File not found:[/red] {py_path}", err=True)
        raise typer.Exit(2)


def _build_environment_js(variables: List[tuple[str, any]]) -> str:
    """Build Skulpt environment variable setup code."""
    SKULPT_ENV_VAR_TEMPLATE = 'Sk.environ.set$item(new Sk.builtin.str("{name}"), {value});'
    lines = []
    for key, value in variables:
        if isinstance(value, str):
            js_value = f'new Sk.builtin.str("{value}")'
        elif value is True:
            js_value = "Sk.builtin.bool.true$"
        elif value is False:
            js_value = "Sk.builtin.bool.false$"
        else:
            raise ValueError(f"Unsupported environment variable type: {type(value)} for {key}")
        lines.append(SKULPT_ENV_VAR_TEMPLATE.format(name=key, value=js_value))
    return "\n".join(lines)


def _build_skulpt_deployment(
    file: Path,
    user_code: str,
    outdir: Path,
    output_filename: str,
    additional_files: List[Path],
    external_pages: List[str],
    create_404: str,
    warn_missing_info: bool,
    cdn_skulpt: str,
    cdn_skulpt_std: str,
    cdn_skulpt_drafter: str,
):
    """Build a Skulpt-based deployment (old CLI behavior)."""
    SK_TEMPLATE_LINE = "Sk.builtinFiles.files[{filename!r}] = {content!r};\n"
    js_lines = []
    
    # Add main site file
    site_code = protect_script_tags(user_code)
    js_lines.append(SK_TEMPLATE_LINE.format(filename="main.py", content=site_code))
    console.print(f"• Adding site file: {file}")
    
    # Add additional files
    for filename in additional_files:
        if not filename.exists():
            console.print(f"[yellow]Warning:[/yellow] Additional file {filename} does not exist - skipping.")
            continue
        try:
            content = filename.read_text(encoding="utf-8")
            content = protect_script_tags(content)
            js_lines.append(SK_TEMPLATE_LINE.format(filename=str(filename), content=content))
            console.print(f"• Adding additional file: {filename}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Failed to read file {filename} - skipping. Error: {e}")
    
    # Build environment variables
    environment_variables = []
    if warn_missing_info:
        environment_variables.append(("DRAFTER_MUST_HAVE_SITE_INFORMATION", True))
    if external_pages:
        external_pages_str = ";".join(external_pages)
        environment_variables.append(("DRAFTER_EXTERNAL_PAGES", external_pages_str))
    environment_settings = _build_environment_js(environment_variables)
    
    # Get setup files
    setup_files = list(get_raw_files('global').deploy.values())
    if environment_settings:
        setup_files.append(f"<script>{environment_settings}</script>")
    setup_code = "\n".join(setup_files)
    
    # Generate complete website
    complete_website = TEMPLATE_SKULPT_DEPLOY.format(
        cdn_skulpt=cdn_skulpt,
        cdn_skulpt_std=cdn_skulpt_std,
        cdn_skulpt_drafter=cdn_skulpt_drafter,
        website_setup=setup_code,
        website_code="".join(js_lines),
    )
    
    # Write main output file
    output_path = outdir / output_filename
    output_path.write_text(complete_website, encoding="utf-8")
    
    # Create 404 file if needed
    need_404 = create_404 == "if_missing" and not (outdir / "404.html").exists()
    if create_404 == "always" or need_404:
        output_404_path = outdir / "404.html"
        output_404_path.write_text(DEPLOYED_404_TEMPLATE_HTML, encoding="utf-8")
        console.print(f"• Created 404.html: {output_404_path}")
    
    # Pretty summary
    table = Table.grid(padding=(0, 1))
    table.add_row("•", f"[bold]{output_filename}[/bold] → {output_path}")
    if additional_files:
        table.add_row("•", f"Included {len(additional_files)} additional file(s)")
    if external_pages:
        table.add_row("•", f"Added {len(external_pages)} external page(s)")
    
    console.print(Panel(table, title="Skulpt Build Complete", border_style="green"))


def _build_static_site(
    file: Path,
    user_code: str,
    outdir: Path,
    output_filename: str,
    title: str,
):
    """Build a static site using the new templating approach."""
    # Copy packaged assets next to the HTML
    target_assets = outdir / "assets"
    copy_assets_to(target_assets)
    assets_url = "assets"
    
    html = render_index_html(
        title=title,
        inline_py=True,
        user_code=user_code,
        python_url=None,
        dev_ws_url=None,
        assets_url_override=assets_url,
    )
    
    out = outdir / output_filename
    out.write_text(html, encoding="utf-8")
    
    # Pretty summary
    table = Table.grid(padding=(0, 1))
    table.add_row("•", f"[bold]{output_filename}[/bold] → {out}")
    table.add_row("•", f"assets/ → {target_assets} (copied)")
    
    console.print(Panel(table, title="Static Build Complete", border_style="green"))


@app.command(help="Build a static website for a given Python file.")
def build(
    file: Path = typer.Argument(
        ..., exists=True, readable=True, help="User Python file"
    ),
    outdir: Path = typer.Option(
        Path("./"),
        "--output-directory",
        "-o",
        help="Output directory for built files.",
    ),
    output_filename: str = typer.Option(
        "index.html",
        "--output-filename",
        help="Filename for the main output HTML file.",
    ),
    additional_files: List[Path] = typer.Option(
        [],
        "--additional-files",
        help="Additional files to include in the build.",
    ),
    external_pages: List[str] = typer.Option(
        [],
        "--external-pages",
        help="External pages to link to in the generated site.",
    ),
    create_404: str = typer.Option(
        "if_missing",
        "--create-404",
        help="Whether to create a 404.html file (always/never/if_missing).",
    ),
    warn_missing_info: bool = typer.Option(
        False,
        "--warn-missing-info",
        help="Warn if set_site_information is missing.",
    ),
    title: str = typer.Option("Drafter App", "--title", help="Site title."),
    deploy_skulpt: bool = typer.Option(
        True,
        "--deploy-skulpt/--no-deploy-skulpt",
        help="Build for Skulpt deployment (old behavior) vs new static build.",
    ),
    cdn_skulpt: str = typer.Option(
        "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt.js",
        "--cdn-skulpt",
        help="CDN URL for Skulpt library.",
    ),
    cdn_skulpt_std: str = typer.Option(
        "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt-stdlib.js",
        "--cdn-skulpt-std",
        help="CDN URL for Skulpt standard library.",
    ),
    cdn_skulpt_drafter: str = typer.Option(
        "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt-drafter.js",
        "--cdn-skulpt-drafter",
        help="CDN URL for Skulpt Drafter library.",
    ),
):
    """
    Build a static website from a Drafter Python file.
    
    Supports two build modes:
    - Skulpt deployment (default): Builds a site that runs Python in the browser
    - Static build: Generates a pre-rendered static HTML site
    """
    outdir.mkdir(parents=True, exist_ok=True)
    user_code = _read_user_code(file)
    
    if deploy_skulpt:
        # Old deployment logic using Skulpt
        _build_skulpt_deployment(
            file=file,
            user_code=user_code,
            outdir=outdir,
            output_filename=output_filename,
            additional_files=additional_files,
            external_pages=external_pages,
            create_404=create_404,
            warn_missing_info=warn_missing_info,
            cdn_skulpt=cdn_skulpt,
            cdn_skulpt_std=cdn_skulpt_std,
            cdn_skulpt_drafter=cdn_skulpt_drafter,
        )
    else:
        # New static build using templating
        _build_static_site(
            file=file,
            user_code=user_code,
            outdir=outdir,
            output_filename=output_filename,
            title=title,
        )


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
