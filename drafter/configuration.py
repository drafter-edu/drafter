"""
TODO:
Custom Error pages
Shareable link to get a link to the current page
Download/upload state button
"""

from dataclasses import dataclass, field
from typing import List, Dict
import os

from drafter.setup import DEFAULT_BACKEND

@dataclass
class ServerConfiguration:
    """
    Represents a configuration for a server, including launch settings, website
    settings, page configurations, and test deployment CDN parameters.

    This class encapsulates all the necessary settings to configure and launch a
    server. It provides fields for specifying server connection parameters, behavior
    modifiers, website customizations, and CDN configurations for test deployments.

    - Launch parameters allow setting options like host address and port for initiating
      the server.
    - Website settings provide options to define the appearance and behavior
      of the site served by the server.
    - Additional fields configure page styling and
      resource path management.
    - Test deployment parameters facilitate url-based
      customization for specific development or testing environments.

    :ivar host: The server's host address.
    :type host: str
    :ivar port: The port on which the server runs.
    :type port: int
    :ivar debug: Whether to enable debug mode for the server.
    :type debug: bool
    :ivar backend: The backend system used (e.g., "none", "flask").
    :type backend: str
    :ivar reloader: Whether to use the reloader (typically for development purposes).
    :type reloader: bool
    :ivar skip: Whether to skip running the server, often used for testing purposes.
    :type skip: bool

    :ivar title: Title for the website server.
    :type title: str
    :ivar framed: Whether the website should operate in a framed mode.
    :type framed: bool
    :ivar skulpt: Whether the Skulpt environment is enabled for the server.
    :type skulpt: bool

    :ivar style: The page styling framework or theme.
    :type style: str
    :ivar additional_header_content: A list of additional header content for the page.
    :type additional_header_content: List[str]
    :ivar additional_css_content: A list of additional CSS content for the page.
    :type additional_css_content: List[str]
    :ivar src_image_folder: Source folder for server-stored images.
    :type src_image_folder: str
    :ivar save_uploaded_files: Whether uploaded files should be saved to storage.
    :type save_uploaded_files: bool
    :ivar deploy_image_path: Path for deploying images (defaults vary based on Skulpt usage).
    :type deploy_image_path: str

    :ivar cdn_skulpt: CDN URL for accessing Skulpt library files.
    :type cdn_skulpt: str
    :ivar cdn_skulpt_std: CDN URL for accessing the Skulpt standard library.
    :type cdn_skulpt_std: str
    :ivar cdn_skulpt_drafter: CDN URL for accessing Skulpt-related Drafter files.
    :type cdn_skulpt_drafter: str
    :ivar cdn_drafter_setup: CDN URL for accessing Skulpt Drafter setup files.
    :type cdn_drafter_setup: str
    """
    # Launch parameters
    host: str = "localhost"
    port: int = 8080
    debug: bool = True
    # "none", "flask", etc.
    backend: str = DEFAULT_BACKEND
    reloader: bool = False
    # This makes the server not run (e.g., to only run tests)
    skip: bool = bool(os.environ.get('DRAFTER_SKIP', False))

    # Website configuration
    title: str = "Drafter Website"
    framed: bool = True
    skulpt: bool = bool(os.environ.get('DRAFTER_SKULPT', False))

    # Page configuration
    style: str = 'skeleton'
    additional_header_content: List[str] = field(default_factory=list)
    additional_css_content: List[str] = field(default_factory=list)
    src_image_folder: str = ''
    save_uploaded_files: bool = not skulpt
    deploy_image_path: str = 'website' if skulpt else 'images'

    # Test Deployment CDN configurations
    cdn_skulpt: str = os.environ.get("DRAFTER_CDN_SKULPT", "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt.js")
    cdn_skulpt_std: str = os.environ.get("DRAFTER_CDN_SKULPT_STD", "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt-stdlib.js")
    cdn_skulpt_drafter: str = os.environ.get("DRAFTER_CDN_SKULPT_DRAFTER", "https://drafter-edu.github.io/drafter-cdn/skulpt/skulpt-drafter.js")
    cdn_drafter_setup: str = os.environ.get("DRAFTER_CDN_SETUP", "https://drafter-edu.github.io/drafter-cdn/skulpt/drafter-setup.js")
