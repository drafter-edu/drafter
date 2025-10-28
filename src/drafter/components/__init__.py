"""Drafter components for building interactive pages.

This module provides all the components needed to build pages in Drafter.
Components have been organized into logical modules but are all exported
here for backward compatibility.
"""

# Import base classes and utilities
from drafter.components.base import (
    PageContent,
    LinkContent,
    Content,
    BASELINE_ATTRS,
    validate_parameter_name,
    make_safe_json_argument,
    make_safe_argument,
    make_safe_name,
)

# Import navigation components
from drafter.components.argument import Argument
from drafter.components.navigation import Link, Button, SubmitButton

# Import remaining components from the main file (temporarily)
from drafter.components.components import (
    Image,
    TextBox,
    TextArea,
    SelectBox,
    CheckBox,
    LineBreak,
    HorizontalRule,
    Span,
    Div,
    Pre,
    Row,
    NumberedList,
    BulletedList,
    Header,
    Table,
    Text,
    MatPlotLibPlot,
    Download,
    FileUpload,
)

__all__ = [
    # Base classes
    'PageContent',
    'LinkContent',
    'Content',
    'BASELINE_ATTRS',
    # Utilities
    'validate_parameter_name',
    'make_safe_json_argument',
    'make_safe_argument',
    'make_safe_name',
    # Navigation
    'Argument',
    'Link',
    'Button',
    'SubmitButton',
    # Forms
    'TextBox',
    'TextArea',
    'SelectBox',
    'CheckBox',
    'FileUpload',
    # Layout
    'LineBreak',
    'HorizontalRule',
    'Span',
    'Div',
    'Pre',
    'Row',
    # Lists
    'NumberedList',
    'BulletedList',
    # Content
    'Header',
    'Text',
    'Table',
    # Media
    'Image',
    'MatPlotLibPlot',
    'Download',
]
