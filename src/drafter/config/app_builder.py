from dataclasses import dataclass

from drafter.config.engines import EngineType


@dataclass
class AppBuilderConfiguration:
    prerender_initial_page: bool = True
    engine: EngineType = "skulpt"
