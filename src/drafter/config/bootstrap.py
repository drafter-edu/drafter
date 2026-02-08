from dataclasses import dataclass
from typing import Union, Optional


@dataclass
class BootstrapConfiguration:
    mode: str = "start_server"  # Options: "start_server", "compile_site"