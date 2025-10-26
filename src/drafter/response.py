from dataclasses import dataclass
from drafter.page import Page


@dataclass
class Response:
    page: Page
