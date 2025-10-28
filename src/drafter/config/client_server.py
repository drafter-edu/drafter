from dataclasses import dataclass


@dataclass
class ClientServerConfiguration:
    in_debug_mode: bool = True
    enable_audit_logging: bool = True
    site_title: str = "Drafter Application"
