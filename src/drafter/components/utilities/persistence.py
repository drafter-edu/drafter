"""Shared constants and key derivation for persistent components.

Persistent components (e.g., ``Timer``, ``Clock``, ``Audio``, ``Video`` with
``persistent=True``) survive simulated page reloads: instead of being destroyed
with the page body, the live DOM node is "parked" in a hidden area of the
drafter footer and re-adopted when a page renders the same component again.

Two rendered attributes drive the client-side mechanism:

- ``data-drafter-persist-key``: a stable identity for the component, emitted on
  every persistence-capable component (persistent or not, so that rendering a
  non-persistent version of the same component can evict the parked one).
- ``data-drafter-persistent``: ``"true"`` only when the component was created
  with ``persistent=True``.

A third attribute, ``data-drafter-persist-evict``, marks an explicit removal
request (see :class:`drafter.components.persistence.RemovePersistent`).

Identity rules: an explicit ``id`` is used verbatim as the key; otherwise the
key is derived from the tag name and a deterministic hash of the rendered
attributes, so "the same constructor call" on two pages produces the same key.
The ``persistent`` flag itself is excluded from the hash so the persistent and
non-persistent versions of a component share a key.

This module must stay free of browser (``js``) imports: it is shared between
the server-side render pipeline and the client-side bridge.
"""

import json

PERSIST_KEY_ATTR = "data-drafter-persist-key"
PERSIST_FLAG_ATTR = "data-drafter-persistent"
PERSIST_EVICT_ATTR = "data-drafter-persist-evict"

#: Attributes that must not influence a component's persistence identity.
_IDENTITY_EXCLUDED_ATTRS = {
    "persistent",
    PERSIST_KEY_ATTR,
    PERSIST_FLAG_ATTR,
}


def _fnv1a_hash(text: str) -> str:
    """Deterministic 32-bit FNV-1a hash, hex-encoded.

    Implemented by hand (rather than hashlib) so it works identically under
    Skulpt, Pyodide, and CPython.
    """
    state = 0x811C9DC5
    for character in text:
        state ^= ord(character)
        state = (state * 0x01000193) & 0xFFFFFFFF
    return format(state, "08x")


def derive_persist_key(tag: str, attributes: dict) -> str:
    """Derive the stable persistence identity for a component.

    Args:
        tag: The component's HTML tag name.
        attributes: The component's rendered attributes (pre-serialization).

    Returns:
        The explicit ``id`` attribute if one was provided, otherwise
        ``"<tag>:<hash>"`` derived from the remaining attributes.
    """
    explicit_id = attributes.get("id")
    if explicit_id:
        return str(explicit_id)
    identity = {
        str(key): str(value)
        for key, value in attributes.items()
        if key not in _IDENTITY_EXCLUDED_ATTRS
    }
    serialized = json.dumps(identity, sort_keys=True)
    return f"{tag}:{_fnv1a_hash(serialized)}"


def add_persistence_attributes(tag: str, attributes: dict, known_attrs: list) -> None:
    """Add persistence marker attributes to a component's attribute dict.

    Mutates ``attributes`` in place. The ``persistent`` entry is removed when
    the component does not render it as a real HTML attribute (native tags like
    ``<audio>``/``<video>``); custom elements that list ``persistent`` in their
    ``KNOWN_ATTRS`` keep it.
    """
    persistent = bool(attributes.get("persistent", False))
    if "persistent" not in known_attrs:
        attributes.pop("persistent", None)
    attributes[PERSIST_KEY_ATTR] = derive_persist_key(tag, attributes)
    if persistent:
        attributes[PERSIST_FLAG_ATTR] = "true"
