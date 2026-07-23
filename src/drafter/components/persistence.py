"""Component for removing ("evicting") persisted components.

Persistent components (``Timer``, ``Clock``, ``Audio``, ``Video`` created with
``persistent=True``) keep running in a hidden area of the drafter footer when
the page that created them is replaced. Including a :class:`RemovePersistent`
component on a page removes the matching persisted component for good.
"""

from dataclasses import dataclass
from typing import Union

from drafter.components.page_content import Component, ComponentArgument
from drafter.components.utilities.persistence import (
    PERSIST_EVICT_ATTR,
    PERSIST_KEY_ATTR,
)


def resolve_persist_key(target: Union[str, Component]) -> str:
    """Resolve a persistence key from a key string, id, or component.

    Args:
        target: Either the key itself (the component's explicit ``id``, or a
            derived ``tag:hash`` key), or a persistence-capable component whose
            key should be computed.

    Returns:
        The persistence key string.

    Raises:
        ValueError: If given a component that does not support persistence.
    """
    if isinstance(target, str):
        return target
    if isinstance(target, Component):
        attributes = target.get_attributes(None)
        key = attributes.get(PERSIST_KEY_ATTR)
        if key:
            return str(key)
        raise ValueError(
            f"{target.__class__.__name__} components do not support persistence, "
            "so there is no persisted version to remove."
        )
    raise ValueError(
        "RemovePersistent expects a key string or a Component, "
        f"but was given {target!r}."
    )


@dataclass(repr=False)
class RemovePersistent(Component):
    """Removes a persisted component when this page is rendered.

    Renders as an invisible marker element; when the page loads, the persisted
    component whose key matches ``target`` is stopped and discarded. If no
    matching component is currently persisted, nothing happens.

    The target can be identified three ways:

    - The ``id`` the persistent component was created with (recommended):
      ``RemovePersistent("background-music")``
    - An equivalent component instance (same constructor arguments):
      ``RemovePersistent(Audio("theme.mp3", persistent=True))``
    - A raw derived key string (shown in the debug panel's Persisted list).

    Attributes:
        target: The key string, id, or component identifying what to remove.
    """

    target: Union[str, Component]

    tag = "span"
    ARGUMENTS = [
        ComponentArgument("target"),
    ]

    def __init__(self, target: Union[str, Component], **kwargs):
        """Initialize the removal marker.

        Args:
            target: The key string, id, or component identifying the persisted
                component to remove.
            **kwargs: Additional HTML attributes and styles.
        """
        self.target = target
        self.extra_settings = kwargs

    def get_attributes(self, context) -> dict:
        """Build the eviction marker's attributes.

        Args:
            context: The render context, passed through to extra-settings
                handling.

        Returns:
            An attribute dictionary carrying the resolved persistence key
            in the eviction attribute, plus `hidden` so the marker is
            invisible.
        """
        attributes = {
            PERSIST_EVICT_ATTR: resolve_persist_key(self.target),
            "hidden": True,
        }
        return self._handle_extra_settings(attributes, context, {})
