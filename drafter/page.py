from dataclasses import dataclass
from typing import Any

from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY
from drafter.components import PageContent, Link


@dataclass
class Page:
    state: Any
    content: list

    def __init__(self, state, content=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content

        if not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError("The content of a page must be a list of strings or components."
                             f" Found {incorrect_type} instead.")
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, PageContent)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError("The content of a page must be a list of strings or components."
                                     f" Found {incorrect_type} at index {index} instead.")

    def render_content(self, current_state, configuration: ServerConfiguration) -> str:
        # TODO: Decide if we want to dump state on the page
        chunked = [
            # f'<input type="hidden" name="{RESTORABLE_STATE_KEY}" value={current_state!r}/>'
        ]
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(chunk.render(current_state, configuration))
        content = "\n".join(chunked)
        content = f"<form>{content}</form>"
        if configuration.framed:
            content = (f"<div class='container btlw-header'>{configuration.title}</div>"
                       f"<div class='container btlw-container'>{content}</div>")
        return content

    def verify_content(self, server) -> bool:
        for chunk in self.content:
            if isinstance(chunk, Link):
                chunk.verify(server)
        return True
