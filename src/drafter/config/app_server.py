from dataclasses import dataclass


@dataclass
class AppServerConfiguration:
    prerender_initial_page: bool = True
