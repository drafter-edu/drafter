"""Core data types shared across layers.

This package init deliberately re-exports nothing: submodules like
``drafter.data.converter`` and ``drafter.data.payload`` are light leaves
that the component layer imports eagerly at module-definition time.
Importing e.g. ``drafter.data.response`` here would drag in the payloads,
config, and router layers on every ``drafter.data.*`` import and recreate
the component->router circular import. Import the submodule you need
directly (``from drafter.data.request import Request``).
"""
