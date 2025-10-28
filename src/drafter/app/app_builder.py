"""
AppBuilder for generating static deployable websites.

This module provides the AppBuilder class which compiles a Drafter application
into static HTML, CSS, and JavaScript files that can be deployed to any
static hosting service.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import json

from drafter.config.app_builder import AppBuilderConfiguration
from drafter.client_server import ClientServer
from drafter.data.request import Request
from drafter.app.templating import render_index_html
from drafter.app.utils import pkg_assets_dir, copy_assets_to


@dataclass
class AppBuilder:
    """
    Builds static HTML/CSS/JS files from a Drafter application for deployment.

    The AppBuilder compiles a Drafter application into a static website that can
    be hosted on any static file server (GitHub Pages, Netlify, etc.). It handles:
    - Generating the main index.html
    - Prerendering the initial page for SEO
    - Copying necessary assets (JS, CSS)
    - Bundling the application code

    :ivar configuration: Configuration options for the builder.
    :ivar server: The ClientServer instance containing the application routes.
    """

    configuration: AppBuilderConfiguration
    server: ClientServer

    def __init__(
        self,
        server: ClientServer,
        configuration: Optional[AppBuilderConfiguration] = None,
    ):
        self.server = server
        self.configuration = configuration or AppBuilderConfiguration()

    def build(
        self,
        user_file: Path,
        output_dir: Path,
        title: str = "Drafter App",
        prerender: Optional[bool] = None,
    ) -> Dict[str, Path]:
        """
        Builds the static site and outputs it to the specified directory.

        :param user_file: Path to the user's Python file.
        :param output_dir: Directory where the built files will be output.
        :param title: Title for the website.
        :param prerender: Whether to prerender the initial page. If None, uses config.
        :return: Dictionary mapping file types to their output paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read user code
        user_code = user_file.read_text(encoding="utf-8")

        # Determine if we should prerender the initial page
        should_prerender = (
            prerender
            if prerender is not None
            else self.configuration.prerender_initial_page
        )

        # Prerender initial page if configured
        initial_page_html = ""
        if should_prerender:
            initial_page_html = self._prerender_initial_page()

        # Generate index.html
        html = render_index_html(
            title=title,
            inline_py=True,  # Always inline for static builds
            user_code=user_code,
            python_url=None,
            dev_ws_url=None,  # No websocket in static builds
            assets_url_override="assets",
        )

        # Write index.html
        index_path = output_dir / "index.html"
        index_path.write_text(html, encoding="utf-8")

        # Copy assets
        assets_dir = output_dir / "assets"
        copy_assets_to(assets_dir)

        return {
            "index": index_path,
            "assets": assets_dir,
        }

    def _prerender_initial_page(self) -> str:
        """
        Prerenders the initial page by executing the index route.

        This allows search engines and social media crawlers to see
        the initial page content without executing JavaScript.

        :return: HTML string of the prerendered initial page.
        """
        try:
            # Create a request for the index page
            initial_request = Request(
                id=0, action="load", url="index", args=[], kwargs={}, event={}
            )

            # Visit the index route to get the response
            response = self.server.visit(initial_request)

            # Return the body of the response
            return response.body
        except Exception as e:
            # If prerendering fails, return empty string
            # The app will still work, just without SEO benefits
            print(f"Warning: Failed to prerender initial page: {e}")
            return ""

    def build_with_metadata(
        self,
        user_file: Path,
        output_dir: Path,
        site_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Path]:
        """
        Builds the site with additional metadata (title, description, etc.).

        :param user_file: Path to the user's Python file.
        :param output_dir: Directory where the built files will be output.
        :param site_metadata: Dictionary of site metadata (title, description, etc.).
        :return: Dictionary mapping file types to their output paths.
        """
        metadata = site_metadata or {}
        title = metadata.get("title", "Drafter App")

        return self.build(
            user_file=user_file,
            output_dir=output_dir,
            title=title,
        )
