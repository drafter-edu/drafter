"""MkDocs plugin for embedding runnable Drafter apps from fenced code blocks."""

from __future__ import annotations

import hashlib
import html
import logging
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

# Match fenced code blocks with optional language/info string.
FENCE_RE = re.compile(
    r"```(?P<info>[^\n]*)\n(?P<code>.*?)\n```",
    flags=re.DOTALL,
)


class DrafterCodeBlockPlugin(BasePlugin):
    """Compile marked Drafter code fences into embedded runnable iframes."""

    config_scheme = (
        ("marker", config_options.Type(str, default="drafter")),
        ("language", config_options.Type(str, default="python")),
        ("output_subdir", config_options.Type(str, default="drafter-demos")),
        ("iframe_height", config_options.Type(int, default=430)),
        ("show_source", config_options.Type(bool, default=True)),
        ("python_executable", config_options.Optional(config_options.Type(str))),
        ("compile_timeout", config_options.Type(int, default=120)),
        (
            "pyodide_package_style",
            config_options.Choice(("build", "cdn", "pypi"), default="pypi"),
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self._docs_dir = Path(".")
        self._site_dir = Path("site")
        self._site_output_dir = Path("site")
        self._temp_root: Path | None = None
        self._compiled_cache: dict[str, PurePosixPath] = {}

    def on_config(self, config):
        self._docs_dir = Path(config["docs_dir"]).resolve()
        self._site_dir = Path(config["site_dir"]).resolve()
        self._site_output_dir = self._site_dir / self.config["output_subdir"]
        self._site_output_dir.mkdir(parents=True, exist_ok=True)
        self._temp_root = Path(tempfile.mkdtemp(prefix="mkdocs-drafter-"))
        self._compiled_cache.clear()
        return config

    def on_page_markdown(self, markdown, page, config, files):
        block_counter = {"value": 0}

        def replace_block(match: re.Match[str]) -> str:
            info = match.group("info").strip()
            code = match.group("code")

            if not self._is_drafter_block(info):
                return match.group(0)

            block_counter["value"] += 1
            demo_id = self._make_demo_id(
                page.file.src_uri, block_counter["value"], code
            )

            try:
                demo_rel_path = self._build_demo(code, demo_id)
                iframe_src = self._relative_url_for_page(page.url, demo_rel_path)
                iframe_html = self._build_iframe_html(demo_id, iframe_src)
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
                return f"{match.group(0)}\n\n{iframe_html}"
            return iframe_html

        return FENCE_RE.sub(replace_block, markdown)

    def on_post_build(self, config):
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
        script_path.write_text(self._prepare_code(code), encoding="utf-8")

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
            self.config["pyodide_package_style"],
        ]

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

        rel_path = PurePosixPath(self.config["output_subdir"]) / demo_id / "index.html"
        self._compiled_cache[demo_id] = rel_path
        return rel_path

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

    def _build_iframe_html(self, demo_id: str, iframe_src: str) -> str:
        title = html.escape(f"Drafter Demo {demo_id}")
        src = html.escape(iframe_src)
        height = int(self.config["iframe_height"])
        return (
            '<div class="drafter-demo" data-drafter-demo="'
            + html.escape(demo_id)
            + '">\n'
            + "  <iframe "
            + f'src="{src}" '
            + f'title="{title}" '
            + 'loading="lazy" '
            + 'sandbox="allow-scripts allow-forms allow-same-origin allow-downloads" '
            + 'style="width: 100%; border: 1px solid #c6c6c6; border-radius: 8px; '
            + f'min-height: {height}px;"'
            + "></iframe>\n"
            + "</div>"
        )
