from typing import Optional
from dataclasses import dataclass, field
from difflib import get_close_matches


@dataclass
class Theme:
    """Represents a visual theme with associated CSS and JavaScript assets.

    Attributes:
        name: The name identifier for the theme.
        css_paths: List of paths to CSS files that define the theme styling.
        js_paths: List of paths to JavaScript files associated with the theme.
    """

    name: str
    css_paths: list[str]
    js_paths: list[str]


@dataclass
class ThemeSystem:
    """Manages registration and lookup of themes for the application.

    Attributes:
        themes: Dictionary mapping theme names to Theme objects.
        default_theme: The name of the theme to use when none is specified.
        none_theme: The name of the theme to use for no styling.
    """

    themes: dict[str, Theme] = field(default_factory=dict)
    default_theme: str = "default"
    none_theme: str = "none"

    def register_theme(self, theme: Theme) -> None:
        """Register a new theme with the system.

        Args:
            theme: The Theme object to register.
        """
        self.themes[theme.name] = theme

    def get_theme(self, name: Optional[str]) -> Theme:
        """Retrieve a theme by name, with fallback to defaults.

        Args:
            name: The name of the theme to retrieve, or None for the none_theme.

        Returns:
            The requested Theme, or the default theme if the name is not found.
        """
        if name is None or name == self.none_theme:
            return Theme(name=self.none_theme, css_paths=[], js_paths=[])
        return self.themes.get(name, self.themes[self.default_theme])

    def is_valid_theme(self, name: str) -> bool:
        """Check if a theme name is registered in the system.

        Args:
            name: The name of the theme to validate.

        Returns:
            True if the theme is registered, False otherwise.
        """
        return name in self.themes

    def suggest_mistake(self, name: str) -> str:
        """Generate a helpful error message suggesting correct theme names.

        Args:
            name: The misspelled or incorrect theme name.

        Returns:
            A message suggesting the closest match or listing available themes.
        """
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
        css_paths=["css/default.css"],
        js_paths=[],
    )
)
theme_system.register_theme(
    Theme(
        name="none",
        css_paths=["css/none.css"],
        js_paths=[],
    ),
)
# TODO: Classic Drafter theme


def get_theme_system() -> ThemeSystem:
    """Retrieve the global theme system instance.

    Returns:
        The singleton ThemeSystem instance.
    """
    return theme_system
