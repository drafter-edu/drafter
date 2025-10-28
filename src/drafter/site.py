"""
Site class for managing website metadata and configuration.

This module provides the Site class which represents a complete Drafter website,
including metadata like title, description, favicon, language, etc., and manages
routes for the application.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Callable, Any
from drafter.routes import Router


@dataclass
class Site:
    """
    Represents a complete Drafter website with metadata and routes.

    A Site holds configuration information about the website and manages
    the routes that define the application's pages.

    :ivar title: The title of the website, shown in browser tabs and search results.
    :ivar description: A description of the website for SEO and metadata purposes.
    :ivar favicon: URL or path to the favicon for the website.
    :ivar language: The primary language of the website (e.g., "en", "es").
    :ivar author: The author or creator of the website.
    :ivar keywords: Keywords for SEO purposes.
    :ivar router: The Router instance managing URL routing for this site.
    :ivar metadata: Additional custom metadata as key-value pairs.
    """

    title: str = "Drafter Application"
    description: str = ""
    favicon: Optional[str] = None
    language: str = "en"
    author: str = ""
    keywords: list[str] = field(default_factory=list)
    router: Router = field(default_factory=Router)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_route(self, url: str, func: Callable) -> None:
        """
        Adds a new route to the site.

        :param url: The URL path for the route.
        :param func: The function to call when the route is accessed.
        """
        self.router.add_route(url, func)

    def get_route(self, url: str) -> Optional[Callable]:
        """
        Retrieves the function associated with a given URL.

        :param url: The URL to look up.
        :return: The function associated with the URL, or None if not found.
        """
        return self.router.get_route(url)

    def get_all_routes(self) -> Dict[str, Callable]:
        """
        Gets all routes registered in this site.

        :return: Dictionary mapping URLs to their handler functions.
        """
        return self.router.routes.copy()
