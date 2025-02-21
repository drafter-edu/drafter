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
    Configuration for the server.
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
