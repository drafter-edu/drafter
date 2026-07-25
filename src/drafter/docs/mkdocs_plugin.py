"""MkDocs plugin for embedding runnable Drafter apps from fenced code blocks.

The fence info line may carry optional parameters (on drafter blocks and
plain code fences alike)::

    ```python drafter hl_lines="2-4 7" height=300
    ...
    ```

``hl_lines`` highlights the given lines/ranges in the rendered source block
(via pymdownx.highlight) and ``height`` sets the embedded demo iframe's
height, overriding the plugin's ``iframe_height`` option for that block
(bare numbers are pixels; CSS lengths like ``20em`` also work).
"""

from __future__ import annotations

import hashlib
import html
import logging
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

LOGGER = logging.getLogger("mkdocs.plugins.drafter_codeblocks")
"""Logger for the Drafter code block MkDocs plugin."""

# Match fenced code blocks with optional language/info string.
FENCE_RE = re.compile(
    r"```(?P<info>[^\n]*)\n(?P<code>.*?)\n```",
    flags=re.DOTALL,
)
"""Regular expression matching fenced code blocks with an optional info string."""

# Match key=value parameters in a fence info string (values may be quoted).
PARAM_RE = re.compile(r"""(?P<key>[A-Za-z_][\w-]*)=(?P<value>"[^"]*"|'[^']*'|\S+)""")
"""Regular expression matching ``key=value`` parameters in a fence info string."""

# Parameters the plugin understands on a fence info line, e.g.
# ```python drafter hl_lines="2-4 7" height=300
KNOWN_PARAMS = frozenset({"hl_lines", "height"})
"""Fence parameters handled by this plugin (all others pass through untouched)."""

HL_LINES_TOKEN_RE = re.compile(r"^\d+(-\d+)?$")
"""A single hl_lines entry: a line number or an inclusive ``start-end`` range."""

CSS_LENGTH_RE = re.compile(r"^\d+(\.\d+)?(px|em|rem|vh|vw|%)$")
"""CSS lengths accepted for the ``height`` parameter (bare integers mean px)."""


class DrafterCodeBlockPlugin(BasePlugin):
    """Compile marked Drafter code fences into embedded runnable iframes."""

    config_scheme = (
        ("marker", config_options.Type(str, default="drafter")),
        ("language", config_options.Type(str, default="python")),
        ("output_subdir", config_options.Type(str, default="drafter-demos")),
        ("iframe_height", config_options.Type(int, default=-1)),
        ("show_source", config_options.Type(bool, default=True)),
        ("python_executable", config_options.Optional(config_options.Type(str))),
        ("compile_timeout", config_options.Type(int, default=120)),
        (
            "pyodide_package_style",
            config_options.Choice(("build", "cdn", "pypi"), default="pypi"),
        ),
        ("subtle_debug_entry", config_options.Type(bool, default=True)),
        ("production", config_options.Type(bool, default=True)),
        # One Pyodide runtime per page, shared by all demos on it. Each demo's
        # iframe only keeps HTML/CSS encapsulated; the parent page hosts the
        # (expensive) Python runtime and every demo attaches to it.
        ("shared_runtime", config_options.Type(bool, default=True)),
        # Adds a pencil button to each demo's source block that swaps it for
        # an editor whose run button pushes the edited code into the live
        # demo below. Requires shared_runtime and show_source.
        ("editable", config_options.Type(bool, default=True)),
    )

    # All demos on a page share one copy of the JS/CSS assets (and the parent
    # page loads the Drafter bundle from here to host the shared runtime).
    SHARED_ASSETS_DIRNAME = "_shared"

    def __init__(self) -> None:
        super().__init__()
        self._docs_dir = Path(".")
        self._site_dir = Path("site")
        self._site_output_dir = Path("site")
        self._temp_root: Path | None = None
        self._compiled_cache: dict[str, PurePosixPath] = {}
        self._pyodide_package_style = "pypi"
        self._pages_with_demos: set[str] = set()

    def on_config(self, config):
        """Prepare build state when the MkDocs configuration is loaded.

        Resolves docs/site directories, creates the demo output directory
        and a temporary build directory, clears per-build caches, and
        determines the pyodide package style (honoring DRAFTER_MKDOCS_DEV).

        Args:
            config: The MkDocs configuration object.

        Returns:
            The (unmodified) MkDocs configuration object.
        """
        self._docs_dir = Path(config["docs_dir"]).resolve()
        self._site_dir = Path(config["site_dir"]).resolve()
        self._site_output_dir = self._site_dir / self.config["output_subdir"]
        self._site_output_dir.mkdir(parents=True, exist_ok=True)
        self._temp_root = Path(tempfile.mkdtemp(prefix="mkdocs-drafter-"))
        self._compiled_cache.clear()
        self._pages_with_demos.clear()
        self._pyodide_package_style = self._resolve_pyodide_package_style()
        return config

    def on_page_markdown(self, markdown, /, *, page, config, files):
        """Replace marked Drafter code fences with embedded demo iframes.

        Each fenced block whose info string carries the configured marker is
        compiled into a standalone demo site and replaced by an iframe
        (optionally preceded by the original source block). Blocks that fail
        to build are left intact with a warning note appended.

        Args:
            markdown: Raw markdown source of the page.
            page: The MkDocs page being processed.
            config: The MkDocs configuration object.
            files: The MkDocs files collection.

        Returns:
            The transformed markdown for the page.
        """
        block_counter = {"value": 0}

        def replace_block(match: re.Match[str]) -> str:
            info = match.group("info").strip()
            code = match.group("code")

            params, info = self._extract_block_params(info)

            if not self._is_drafter_block(info):
                if params:
                    # Plain fences still get hl_lines support; height only
                    # applies to demo iframes.
                    if "height" in params:
                        LOGGER.warning(
                            "Ignoring height=%s on a non-drafter code block "
                            "in %s; height only applies to embedded demos.",
                            params["height"],
                            page.file.src_uri,
                        )
                    return self._apply_block_params(info, code, params)
                return match.group(0)

            block_counter["value"] += 1
            demo_id = self._make_demo_id(
                page.file.src_uri, block_counter["value"], code
            )

            try:
                demo_rel_path = self._build_demo(code, demo_id)
                iframe_src = self._relative_url_for_page(page.url, demo_rel_path)
                iframe_html = self._build_iframe_html(
                    demo_id,
                    iframe_src,
                    height=self._normalized_height(params.get("height")),
                )
            except Exception as exc:  # pragma: no cover - only on build failures
                LOGGER.warning(
                    "Failed to compile Drafter code block in %s: %s",
                    page.file.src_uri,
                    exc,
                )
                failure = (
                    "\n\n> **Drafter embed failed to build.** "
                    "The original code block is still shown above."
                )
                return f"{match.group(0)}{failure}"

            if self.config["show_source"]:
                source_block = self._build_source_block(info, code, params)
                return f"{source_block}\n\n{iframe_html}"
            return iframe_html

        result = FENCE_RE.sub(replace_block, markdown)
        if block_counter["value"] > 0:
            self._pages_with_demos.add(page.file.src_uri)
        return result

    def on_page_content(self, page_html, /, *, page, config, files):
        """Host the shared Pyodide runtime on pages that embed demos.

        Loads the Drafter bundle in the PARENT page (before any demo iframes,
        so an iframe can never race ahead and boot its own runtime) and every
        embedded demo attaches to the resulting single shared runtime.
        """
        if not self.config["shared_runtime"]:
            return page_html
        if page.file.src_uri not in self._pages_with_demos:
            return page_html
        bundle_path = (
            PurePosixPath(self.config["output_subdir"])
            / self.SHARED_ASSETS_DIRNAME
            / "js"
            / "drafter.pyodide.js"
        )
        bundle_url = self._relative_url_for_page(page.url, bundle_path)
        host_script = f'<script src="{html.escape(bundle_url)}"></script>\n'
        return host_script + self._editor_assets_html() + page_html

    def _editor_assets_html(self) -> str:
        """Inline the editable-demo script/styles, or "" when disabled.

        The editor needs the source block visible (to attach its pencil
        button to) and the shared runtime host (whose ``restart`` mechanism
        it uses to push edited code into the demo's live instance).
        """
        if not (self.config["editable"] and self.config["show_source"]):
            return ""
        assets_dir = Path(__file__).resolve().parent
        css = (assets_dir / "embed_editor.css").read_text(encoding="utf-8")
        js = (assets_dir / "embed_editor.js").read_text(encoding="utf-8")
        return f"<style>\n{css}</style>\n<script>\n{js}</script>\n"

    def on_post_build(self, *, config):
        """Clean up the temporary build directory after the site is built.

        Args:
            config: The MkDocs configuration object.
        """
        if self._temp_root and self._temp_root.exists():
            shutil.rmtree(self._temp_root, ignore_errors=True)

    def _is_drafter_block(self, info: str) -> bool:
        if not info:
            return False

        tokens = [
            token.strip().lower() for token in info.replace(",", " ").split() if token
        ]
        if not tokens:
            return False

        marker = self.config["marker"].lower()
        language = self.config["language"].lower()

        if tokens[0] == marker:
            return True

        return marker in tokens and (language in tokens or tokens[0] == language)

    def _make_demo_id(self, src_uri: str, block_index: int, code: str) -> str:
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:12]
        stem = PurePosixPath(src_uri).stem
        normalized_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-") or "page"
        return f"{normalized_stem}-{block_index}-{digest}"

    def _build_demo(self, code: str, demo_id: str) -> PurePosixPath:
        existing = self._compiled_cache.get(demo_id)
        if existing is not None:
            return existing

        target_dir = self._site_output_dir / demo_id
        target_index = target_dir / "index.html"
        if target_index.exists():
            rel_path = (
                PurePosixPath(self.config["output_subdir"]) / demo_id / "index.html"
            )
            self._compiled_cache[demo_id] = rel_path
            return rel_path

        if self._temp_root is None:
            raise RuntimeError("Temporary build directory was not initialized.")

        script_path = self._temp_root / f"{demo_id}.py"
        prepared_code = self._prepare_code(code)
        script_path.write_text(prepared_code, encoding="utf-8")

        python_executable = self.config["python_executable"] or sys.executable
        command = [
            python_executable,
            "-m",
            "drafter",
            str(script_path),
            "--compile",
            "--output-directory",
            str(target_dir),
            "--output-filename",
            "index.html",
            "--pyodide-package-style",
            self._pyodide_package_style,
            "--production" if self.config["production"] else "",
            "--subtle-debug-entry" if self.config["subtle_debug_entry"] else "",
            "--system-packages",
            "bakery",
            "--verbose",
        ]
        if self.config["shared_runtime"]:
            command.append("--shared-runtime")
            # All demos on the site share one assets folder (a sibling of the
            # per-demo output folders), instead of one full copy per demo.
            command.extend(["--override-asset-url", f"../{self.SHARED_ASSETS_DIRNAME}"])

        build_result = subprocess.run(
            command,
            cwd=str(self._docs_dir.parent),
            capture_output=True,
            text=True,
            timeout=int(self.config["compile_timeout"]),
            check=False,
        )

        if build_result.returncode != 0:
            stderr = (build_result.stderr or "").strip()
            stdout = (build_result.stdout or "").strip()
            details = stderr or stdout or "Unknown error while compiling Drafter app"
            raise RuntimeError(details)

        target_script_path = target_dir / f"{demo_id}.py"
        target_script_path.write_text(prepared_code, encoding="utf-8")

        rel_path = PurePosixPath(self.config["output_subdir"]) / demo_id / "index.html"
        self._compiled_cache[demo_id] = rel_path
        return rel_path

    def _resolve_pyodide_package_style(self) -> str:
        dev_flag = os.getenv("DRAFTER_MKDOCS_DEV", "").strip().lower()
        if dev_flag in {"1", "true", "yes", "on"}:
            return "build"
        return str(self.config["pyodide_package_style"])

    def _extract_block_params(self, info: str) -> tuple[dict[str, str], str]:
        """Pull known ``key=value`` parameters out of a fence info string.

        Returns the recognized parameters (values unquoted) and the info
        string with those parameters removed; unrecognized ``key=value``
        pairs are left in place for downstream markdown extensions.
        """
        params: dict[str, str] = {}

        def strip_param(match: re.Match[str]) -> str:
            key = match.group("key").lower()
            if key not in KNOWN_PARAMS:
                return match.group(0)
            params[key] = match.group("value").strip("\"'")
            return ""

        remaining = PARAM_RE.sub(strip_param, info)
        return params, " ".join(remaining.split())

    def _apply_block_params(
        self, source_info: str, code: str, params: dict[str, str]
    ) -> str:
        """Rebuild a fence with a normalized ``hl_lines`` re-emitted on it.

        Used both for the source block of a demo and for plain fences that
        carried recognized parameters (which must be stripped either way so
        they don't confuse pymdownx). ``height`` is handled by the caller
        (it only applies to demo iframes) and is ignored here.
        """
        hl_lines = self._normalized_hl_lines(params.get("hl_lines"))
        if hl_lines:
            source_info = f'{source_info} hl_lines="{hl_lines}"'.strip()
        return f"```{source_info}\n{code}\n```"

    def _normalized_hl_lines(self, value: str | None) -> str | None:
        """Validate an hl_lines value, normalizing commas to spaces.

        Accepts line numbers and inclusive ranges (``2``, ``2-4``) separated
        by spaces or commas, matching what pymdownx.highlight understands.
        """
        if value is None:
            return None
        tokens = [token for token in value.replace(",", " ").split() if token]
        if tokens and all(HL_LINES_TOKEN_RE.match(token) for token in tokens):
            return " ".join(tokens)
        LOGGER.warning(
            "Ignoring invalid hl_lines value %r in fenced code block "
            "(expected line numbers or ranges like '2 4-6').",
            value,
        )
        return None

    def _normalized_height(self, value: str | None) -> str | None:
        """Validate a height value, defaulting bare integers to pixels."""
        if value is None:
            return None
        if value.isdigit():
            return f"{value}px"
        if CSS_LENGTH_RE.match(value):
            return value
        LOGGER.warning(
            "Ignoring invalid height value %r in fenced code block "
            "(expected a CSS length like 300, 300px, or 20em).",
            value,
        )
        return None

    def _build_source_block(self, info: str, code: str, params: dict[str, str]) -> str:
        return self._apply_block_params(
            self._normalized_source_info(info), code, params
        )

    def _normalized_source_info(self, info: str) -> str:
        marker = self.config["marker"].lower()
        language = self.config["language"]
        language_lower = language.lower()

        tokens = info.split()
        kept_tokens: list[str] = []
        has_language = False

        for token in tokens:
            normalized_token = token.strip(",").lower()
            if normalized_token == marker:
                continue
            if normalized_token == language_lower:
                has_language = True
            kept_tokens.append(token)

        if not has_language:
            kept_tokens.insert(0, language)

        return " ".join(kept_tokens).strip() or language

    def _prepare_code(self, code: str) -> str:
        prepared = code.rstrip() + "\n"
        if re.search(r"\bstart_server\s*\(", prepared):
            return prepared
        return prepared + "\nstart_server()\n"

    def _relative_url_for_page(self, page_url: str, target: PurePosixPath) -> str:
        clean_page_url = (page_url or "").strip("/")
        if not clean_page_url:
            page_dir = "."
        elif clean_page_url.endswith(".html"):
            page_dir = str(PurePosixPath(clean_page_url).parent)
        else:
            page_dir = clean_page_url

        if not page_dir or page_dir == ".":
            return target.as_posix()

        return posixpath.relpath(target.as_posix(), start=page_dir)

    def _build_iframe_html(
        self, demo_id: str, iframe_src: str, height: str | None = None
    ) -> str:
        title = html.escape(f"Drafter Demo {demo_id}")
        src = html.escape(iframe_src)
        style_parts = [
            "width: 100%",
            "border: 1px solid #c6c6c6",
            "border-radius: 8px",
        ]
        if height is None:
            default_height = int(self.config["iframe_height"])
            if default_height > 0:
                height = f"{default_height}px"
        if height:
            style_parts.append(f"min-height: {height}")
        style_value = "; ".join(style_parts) + ";"
        return (
            '<div class="drafter-demo" data-drafter-demo="'
            + html.escape(demo_id)
            + '">\n'
            + "  <iframe "
            + f'src="{src}" '
            + f'title="{title}" '
            # The iframe's name reaches the embed as window.name, giving its
            # shared-runtime instance a stable id (registry key + FS folder).
            + f'name="{html.escape(demo_id)}" '
            + 'loading="lazy" '
            + 'sandbox="allow-scripts allow-forms allow-same-origin allow-downloads" '
            + f'style="{style_value}" '
            + "></iframe>\n"
            + "</div>"
        )
