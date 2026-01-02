from dataclasses import dataclass
from drafter.components.page_content import Component
from drafter.components.forms import FormComponent
from typing import Union

@dataclass
class Output(FormComponent):
    """
    A component to display output content, typically used for showing results or responses.
    
    Args:
        content: The content to be displayed as output.
        **kwargs: Additional HTML attributes.
    """
    content: str
    for_id: Union[None, str, FormComponent] = None
    EXTRA_ATTRS = ["for"]

    def __init__(self, content: str, for_id: Union[None, str, FormComponent] = None, **kwargs):
        self.content = content
        if isinstance(for_id, FormComponent):
            for_id = for_id.get_id()
        self.for_id = for_id
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = dict(self.extra_settings)
        if self.for_id:
            extra_settings["for"] = self.for_id
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<output {parsed_settings}>{self.content}</output>"

    def __repr__(self) -> str:
        pieces = [repr(self.content)]
        if self.for_id:
            pieces.append(f"for_id={repr(self.for_id)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Output({', '.join(pieces)})"

@dataclass
class Progress(Component):
    """
    HTML5 progress bar element for showing task completion.
    
    Args:
        value: Current progress value (typically 0-max)
        max: Maximum value (default: 1)
        **kwargs: Additional HTML attributes
        
    Example:
        Progress(0.5, max=1)  # 50% progress bar
        Progress(0.6, max=1, style_width="200px")  # 60% progress, custom width
    """
    value: float
    max: float
    
    def __init__(self, value: float, max: float = 1.0, **kwargs):
        self.value = float(value)
        self.max = float(max)
        self.extra_settings = kwargs
    
    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<progress value='{self.value}' max='{self.max}' {parsed_settings}></progress>"
    
    def __repr__(self) -> str:
        pieces = [repr(self.value)]
        if self.max != 1.0:
            pieces.append(f"max={repr(self.max)}")
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Progress({', '.join(pieces)})"