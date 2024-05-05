"""
TODO:
Custom Error pages
Shareable link to get a link to the current page
Download/upload state button
"""

from dataclasses import dataclass, field
import os

from drafter.setup import DEFAULT_BACKEND

@dataclass
class ServerConfiguration:
    # Launch parameters
    host: str = "localhost"
    port: int = 8080
    debug: bool = True
    # "none", "flask", etc.
    backend: str = DEFAULT_BACKEND
    reloader: bool = False
    # This makes the server not run (e.g., to only run tests)
    skip: bool = os.environ.get('DRAFTER_SKIP', False)

    # Website configuration
    title: str = "Drafter Website"
    framed: bool = True
    skulpt: bool = os.environ.get('DRAFTER_SKULPT', False)

    # Page configuration
    style: str = 'skeleton'
    additional_header_content: list[str] = field(default_factory=list)
    additional_css_content: list[str] = field(default_factory=list)
    image_folder: str = '' if skulpt else 'images'
