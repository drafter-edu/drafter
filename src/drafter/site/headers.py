from dataclasses import dataclass, field

@dataclass
class CSSLink:
    """Represents a CSS link with optional classes.

    Attributes:
        url: The URL or path to the CSS file.
        classes: Optional list of CSS classes to attach to the link element.
    """

    url: str
    classes: set[str] = field(default_factory=set)

    def __repr__(self):
        return f"CSSLink(url='{self.url}', classes={self.classes})"
    
    def precompile_to_html(self, with_extra_classes=None) -> str:
        """Precompiles the CSS link to an HTML <link> element string.

        Returns:
            str: The HTML string for the CSS link.
        """
        all_classes = self.classes.union(with_extra_classes or set())
        class_attr = f' class="{" ".join(all_classes)}"' if all_classes else ""
        return f'<link type="text/css" rel="stylesheet" href="{self.url}"{class_attr}>'