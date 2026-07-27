"""Render planning structures for components.

Contains the `render_plan` module, whose `RenderPlan` and `AssetBundle`
dataclasses describe how a component should become HTML (tag, fragment,
emitter, or raw HTML) along with the CSS/JS assets it needs, without
performing the rendering itself.
"""
