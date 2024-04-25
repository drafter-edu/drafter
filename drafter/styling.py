"""
TODO:
- [ ] indent
- [ ] center
- [ ] Superscript, subscript
- [ ] border/margin/padding (all sides)
"""
from drafter.components import PageContent, Text


def update_style(component, style, value):
    if isinstance(component, str):
        component = Text(component)
    return component.update_style(style, value)


def update_attr(component, attr, value):
    if isinstance(component, str):
        component = Text(component)
    return component.update_attr(attr, value)


def float_right(component: PageContent) -> PageContent:
    return update_style(component, 'float', 'right')


def float_left(component: PageContent) -> PageContent:
    return update_style(component, 'float', 'left')


def bold(component: PageContent) -> PageContent:
    return update_style(component, 'font-weight', 'bold')


def italic(component: PageContent) -> PageContent:
    return update_style(component, 'font-style', 'italic')


def underline(component: PageContent) -> PageContent:
    return update_style(component, 'text-decoration', 'underline')


def strikethrough(component: PageContent) -> PageContent:
    return update_style(component, 'text-decoration', 'line-through')


def monospace(component: PageContent) -> PageContent:
    return update_style(component, 'font-family', 'monospace')


def small_font(component: PageContent) -> PageContent:
    return update_style(component, 'font-size', 'small')


def large_font(component: PageContent) -> PageContent:
    return update_style(component, 'font-size', 'large')


def change_color(component: PageContent, c: str) -> PageContent:
    return update_style(component, 'color', c)


def change_background_color(component: PageContent, color: str) -> PageContent:
    return update_style(component, 'background-color', color)


def change_text_size(component: PageContent, size: str) -> PageContent:
    return update_style(component, 'font-size', size)


def change_text_font(component: PageContent, font: str) -> PageContent:
    return update_style(component, 'font-family', font)


def change_text_align(component: PageContent, align: str) -> PageContent:
    return update_style(component, 'text-align', align)


def change_text_decoration(component: PageContent, decoration: str) -> PageContent:
    return update_style(component, 'text-decoration', decoration)


def change_text_transform(component: PageContent, transform: str) -> PageContent:
    return update_style(component, 'text-transform', transform)


def change_height(component: PageContent, height: str) -> PageContent:
    return update_style(component, 'height', height)


def change_width(component: PageContent, width: str) -> PageContent:
    return update_style(component, 'width', width)


def change_border(component: PageContent, border: str) -> PageContent:
    return update_style(component, 'border', border)


def change_margin(component: PageContent, margin: str) -> PageContent:
    return update_style(component, 'margin', margin)


def change_padding(component: PageContent, padding: str) -> PageContent:
    return update_style(component, 'padding', padding)
