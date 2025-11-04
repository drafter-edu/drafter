from dataclasses import dataclass, field
from typing import List


@dataclass
class ClientServerConfiguration:
    in_debug_mode: bool = True
    enable_audit_logging: bool = True
    site_title: str = "Drafter Application"
    framed: bool = True
    style: str = "skeleton"
    additional_header_content: List[str] = field(default_factory=list)
    additional_css_content: List[str] = field(default_factory=list)
