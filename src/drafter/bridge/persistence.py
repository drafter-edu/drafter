"""Client-side persistence of components across simulated page reloads.

When a page is about to be replaced, elements marked ``data-drafter-persistent``
are "parked": moved (not recreated) into the hidden ``#drafter-persist--`` area
of the footer, so timers keep ticking and media keeps playing. After the new
page is inserted, freshly-rendered elements whose ``data-drafter-persist-key``
matches a parked element are replaced by the parked (live) version. Rendering a
*non*-persistent component with a matching key evicts the parked version, as
does an explicit ``data-drafter-persist-evict`` marker
(:class:`drafter.components.persistence.RemovePersistent`).

The parking area's DOM is the only registry: no Python-side references to
elements are kept, so there is nothing to leak or go stale. A full site restart
rewrites the root's innerHTML, which discards the parking area and everything
in it.

Elements are moved with ``Element.moveBefore`` when the browser supports it
(atomic move: no pause, no custom-element disconnect/connect churn). Otherwise
a plain reparent is used, bracketed by the ``_drafterBeginMove``/
``_drafterEndMove`` protocol that DrafterHTMLElement subclasses implement to
skip their teardown/reset during the move; native media elements get their
playback explicitly resumed.
"""

from typing import Any, Optional

from drafter.components.utilities.persistence import (
    PERSIST_EVICT_ATTR,
    PERSIST_FLAG_ATTR,
    PERSIST_KEY_ATTR,
)
from drafter.bridge.error_handling import report_bridge_warning

PERSIST_SOFT_CAP = 10
"""Soft cap on simultaneously-parked components; exceeding it usually means an
app is accidentally minting a new key per visit (e.g., interpolating state
into a src), so surface a warning instead of growing silently."""

_MEDIA_TAGS = ("audio", "video")


def _tag_name(element: Any) -> str:
    try:
        return str(element.tagName or "").lower()
    except Exception:
        return ""


def _is_media(element: Any) -> bool:
    return _tag_name(element) in _MEDIA_TAGS


def find_parked(parking_area: Any, key: str) -> Optional[Any]:
    """Find the parked element with the given persistence key, if any."""
    for child in list(parking_area.children):
        if child.getAttribute(PERSIST_KEY_ATTR) == key:
            return child
    return None


def _release_media(element: Any) -> None:
    """Stop playback and release buffers held by a media element."""
    try:
        element.pause()
        element.removeAttribute("src")
        element.load()
    except Exception:
        pass


def evict_element(element: Any) -> None:
    """Permanently discard a parked element.

    Media (including nested media) is stopped and its buffers released; the
    final ``remove()`` runs real disconnectedCallback teardown for custom
    elements (clearing intervals and window listeners).
    """
    if _is_media(element):
        _release_media(element)
    for media in list(element.querySelectorAll("audio, video")):
        _release_media(media)
    element.remove()


def evict_key(parking_area: Any, key: str) -> bool:
    """Evict the parked element with the given key. Returns True if found."""
    parked = find_parked(parking_area, key)
    if parked is None:
        return False
    evict_element(parked)
    return True


def _fallback_move(element: Any, new_parent: Any, reference: Optional[Any]) -> None:
    """Reparent without moveBefore, preserving as much state as possible."""
    begin_move = getattr(element, "_drafterBeginMove", None)
    if begin_move is not None:
        begin_move()
    try:
        media_was_playing = _is_media(element) and not element.paused
        if reference is not None:
            new_parent.insertBefore(element, reference)
        else:
            new_parent.appendChild(element)
        if media_was_playing:
            # A synchronous remove+reinsert usually keeps media playing, but
            # some engines still pause at the next stable state; play() on an
            # already-playing element is a no-op.
            try:
                element.play()
            except Exception:
                pass
    finally:
        end_move = getattr(element, "_drafterEndMove", None)
        if end_move is not None:
            end_move()


def move_element(
    element: Any, new_parent: Any, reference: Optional[Any] = None
) -> None:
    """Move an element into new_parent (before reference, or appended).

    Uses the atomic ``moveBefore`` API when available so playback, animation,
    and custom-element state survive the move untouched.
    """
    move_before = getattr(new_parent, "moveBefore", None)
    if move_before is not None:
        try:
            move_before(element, reference)
            return
        except Exception:
            # e.g., element and parent in different documents; fall back.
            pass
    _fallback_move(element, new_parent, reference)


def park_persistent_components(container: Any, parking_area: Any) -> None:
    """Move persistent elements out of a subtree that is about to be replaced.

    Args:
        container: The element whose contents are about to be replaced.
        parking_area: The ``#drafter-persist--`` element.
    """
    nodes = list(container.querySelectorAll(f'[{PERSIST_FLAG_ATTR}="true"]'))
    for node in nodes:
        key = node.getAttribute(PERSIST_KEY_ATTR)
        if not key:
            continue
        existing = find_parked(parking_area, key)
        if existing is not None and not existing.isSameNode(node):
            report_bridge_warning(
                "bridge.persistence_duplicate_key",
                f"Multiple persistent components share the key '{key}'; "
                "keeping the most recent one. Give each persistent component "
                "a unique id to disambiguate.",
                "bridge.persistence.park_persistent_components",
                f"Key: {key}",
                phase="navigation",
            )
            evict_element(existing)
        move_element(node, parking_area)
    parked_count = int(parking_area.childElementCount)
    if parked_count > PERSIST_SOFT_CAP:
        report_bridge_warning(
            "bridge.persistence_cap_exceeded",
            f"There are {parked_count} persisted components, which is more "
            f"than the recommended maximum of {PERSIST_SOFT_CAP}. If this "
            "number keeps growing, a persistent component is probably "
            "getting a new identity on every visit; give it a fixed id.",
            "bridge.persistence.park_persistent_components",
            f"Parked count: {parked_count}",
            phase="navigation",
        )


def apply_persistence(scope: Any, parking_area: Any) -> None:
    """Process evict markers and adopt parked components into fresh content.

    Runs after new page content is inserted. For each freshly-rendered element
    carrying a persistence key:

    - persistent + a parked match: the parked (live) element replaces the
      fresh one, so its running state carries over.
    - non-persistent + a parked match: the fresh element stands and the parked
      version is evicted (rendering a non-persistent version reads as "I want
      a fresh one").
    """
    for marker in list(scope.querySelectorAll(f"[{PERSIST_EVICT_ATTR}]")):
        key = marker.getAttribute(PERSIST_EVICT_ATTR)
        if key:
            evict_key(parking_area, key)
        marker.remove()

    for fresh in list(scope.querySelectorAll(f"[{PERSIST_KEY_ATTR}]")):
        if parking_area.contains(fresh):
            continue
        key = fresh.getAttribute(PERSIST_KEY_ATTR)
        if not key:
            continue
        parked = find_parked(parking_area, key)
        if parked is None or parked.isSameNode(fresh):
            continue
        if fresh.getAttribute(PERSIST_FLAG_ATTR) == "true":
            parent = fresh.parentNode
            if parent is None:
                continue
            move_element(parked, parent, fresh)
            fresh.remove()
        else:
            evict_element(parked)
