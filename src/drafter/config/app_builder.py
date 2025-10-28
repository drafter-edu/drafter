from dataclasses import dataclass


@dataclass
class AppBuilderConfiguration:
    prerender_initial_page: bool = True
