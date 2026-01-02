from dataclasses import dataclass, asdict
from typing import Any, List
import json
import html as html_module
from drafter.components.layout import _HtmlGroup
from drafter.components.page_content import Component


@dataclass(repr=False)
class Pre(_HtmlGroup):
    content: List[Any]
    kind = "pre"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


PreformattedText = Pre


@dataclass
class Header(Component):
    body: str
    level: int = 1

    def __init__(self, body: str, level: int = 1, **kwargs):
        self.body = body
        self.level = level
        if "extra_settings" in kwargs:
            self.extra_settings = kwargs.pop("extra_settings")
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

    def __str__(self):
        return f"<h{self.level}>{self.body}</h{self.level}>"

    def __repr__(self):
        pieces = [repr(self.body)]
        if self.level != 1:
            pieces.append(f"{repr(self.level)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Header({', '.join(pieces)})"


@dataclass
class Text(Component):
    body: str
    extra_settings: dict

    def __init__(self, body: str, **kwargs):
        self.body = body
        if "body" in kwargs:
            self.body = kwargs.pop("content")
        if "extra_settings" in kwargs:
            self.extra_settings = kwargs.pop("extra_settings")
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

    def __eq__(self, other):
        if isinstance(other, Text):
            return (
                self.body == other.body and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, str):
            return self.extra_settings == {} and self.body == other
        return NotImplemented

    def __hash__(self):
        if self.extra_settings:
            items = tuple(sorted(self.extra_settings.items()))
            return hash((self.body, items))
        else:
            return hash(self.body)

    def __repr__(self):
        if self.extra_settings:
            return f"Text({self.body!r}, {self.extra_settings})"
        return f"Text({self.body!r})"

    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if not parsed_settings:
            return self.body
        return f"<span {parsed_settings}>{self.body}</span>"


@dataclass
class RawHTML(Component):
    """
    A component that renders raw HTML without escaping. 
    
    WARNING: Only use with trusted HTML content to avoid XSS vulnerabilities.
    This component bypasses HTML escaping and renders content as-is.
    
    :param html: The raw HTML string to render
    """
    html: str
    
    def __init__(self, html: str, **kwargs):
        self.html = html
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        # Return raw HTML without escaping
        return self.html
    
    def __repr__(self) -> str:
        pieces = [repr(self.html)]
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"RawHTML({', '.join(pieces)})"


class State(Component):
    """
    A component that displays the current application state in a structured format.
    
    This component is useful for debugging or displaying state information to users.
    The state will be rendered as formatted JSON in a preformatted text block.
    
    :param state_obj: The state object to display (will be converted to JSON)
    :param title: Optional title to display above the state (default: "Current State")
    :param indent: Number of spaces to use for JSON indentation (default: 2)
    """
    
    def __init__(self, state_obj: Any, title: str = "Current State", indent: int = 2, **kwargs):
        self.state_obj = state_obj
        self.title = title
        self.indent = indent
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        # Try to convert state to JSON, fallback to repr if not serializable
        try:
            # Handle dataclass instances
            if hasattr(self.state_obj, '__dataclass_fields__'):
                state_dict = asdict(self.state_obj)
                state_json = json.dumps(state_dict, indent=self.indent, default=str)
            else:
                state_json = json.dumps(self.state_obj, indent=self.indent, default=str)
        except (TypeError, ValueError):
            # If JSON serialization fails, use repr
            state_json = repr(self.state_obj)
        
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        
        # Return formatted HTML with title and state display
        escaped_title = html_module.escape(self.title)
        escaped_state = html_module.escape(state_json)
        
        return f"""<div class='drafter-state' {parsed_settings}>
  <h4>{escaped_title}</h4>
  <pre>{escaped_state}</pre>
</div>"""
    
    def __repr__(self) -> str:
        pieces = [repr(self.state_obj)]
        if self.title != "Current State":
            pieces.append(f"title={repr(self.title)}")
        if self.indent != 2:
            pieces.append(f"indent={repr(self.indent)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"State({', '.join(pieces)})"
