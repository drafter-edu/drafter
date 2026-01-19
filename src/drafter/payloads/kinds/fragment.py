from dataclasses import dataclass, field
from textwrap import indent
from typing import Any, Dict, List, Optional

from drafter.data.channel import Message
from drafter.config.client_server import ClientServerConfiguration
from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY
from drafter.components import Component, PageContent, Link
from drafter.data.request import Request
from drafter.history.formatting import format_page_content
from drafter.history.state import SiteState
from drafter.payloads.renderer import render, Renderer
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.kinds.page import Page
from drafter.payloads.failure import VerificationFailure
from drafter.router.routes import Router


@dataclass
class Fragment(Page):
    """
    A Fragment is a payload that will render a fragment of HTML to be injected
    into an existing page, rather than a full page by itself.
    """

    target: Optional[str] = None

    def __init__(self, state, content=None, target=None, css=None, js=None):
        super().__init__(state, content, css, js)
        self.target = target

    def get_target(self, request: Request) -> Optional[str]:
        """
        Gets the target element ID that this Fragment should be injected into.
        If None, the Fragment will be injected into a default location (e.g. the body).
        """
        if self.target is None:
            return request.dom_id or None
        return self.target
