from typing import Optional
from dataclasses import dataclass, field
from difflib import get_close_matches


@dataclass
class Theme:
    name: str
    css_paths: list[str]
    js_paths: list[str]


@dataclass
class ThemeSystem:
    themes: dict[str, Theme] = field(default_factory=dict)
    default_theme: str = "default"
    none_theme: str = "none"

    def register_theme(self, theme: Theme) -> None:
        self.themes[theme.name] = theme

    def get_theme(self, name: Optional[str]) -> Theme:
        if name is None or name == self.none_theme:
            return Theme(name=self.none_theme, css_paths=[], js_paths=[])
        return self.themes.get(name, self.themes[self.default_theme])

    def is_valid_theme(self, name: str) -> bool:
        return name in self.themes

    def suggest_mistake(self, name: str) -> str:
        suggestions = get_close_matches(name, self.themes.keys(), n=1)
        if suggestions:
            return f"Theme '{name}' not found. Did you mean '{suggestions[0]}'?"
        else:
            return f"Theme '{name}' not found. Available themes: {', '.join(self.themes.keys())}."


# Initialize the theme system with default themes
theme_system = ThemeSystem()
theme_system.register_theme(
    Theme(
        name="default",
        css_paths=["assets/css/default.css"],
        js_paths=[],
    )
)
theme_system.register_theme(
    Theme(
        name="none",
        css_paths=["assets/css/none.css"],
        js_paths=[],
    ),
)


def get_theme_system() -> ThemeSystem:
    return theme_system
