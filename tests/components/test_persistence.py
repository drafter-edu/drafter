"""Tests for persistent-component marker rendering and key derivation."""

import pytest

from drafter import Audio, Clock, RemovePersistent, Text, Timer, Video
from drafter.components.persistence import resolve_persist_key
from drafter.components.utilities.persistence import (
    PERSIST_EVICT_ATTR,
    PERSIST_FLAG_ATTR,
    PERSIST_KEY_ATTR,
    derive_persist_key,
)
from drafter.payloads.renderer import render


def render_html(component) -> str:
    return render(component).flatten()


def get_key(component) -> str:
    return component.get_attributes(None)[PERSIST_KEY_ATTR]


class TestMarkerRendering:
    def test_persistent_timer_renders_flag_and_key(self):
        html = render_html(Timer(5000, "finished", persistent=True))
        assert f'{PERSIST_FLAG_ATTR}="true"' in html
        assert f'{PERSIST_KEY_ATTR}="' in html

    def test_non_persistent_timer_renders_key_but_no_flag(self):
        html = render_html(Timer(5000, "finished"))
        assert PERSIST_FLAG_ATTR not in html
        assert f'{PERSIST_KEY_ATTR}="' in html

    def test_timer_keeps_bare_persistent_attribute(self):
        # The custom element reads `persistent` from KNOWN_ATTRS.
        html = render_html(Timer(5000, "finished", persistent=True))
        assert ' persistent="True"' in html

    def test_persistent_audio_renders_markers_without_attribute_leak(self):
        html = render_html(Audio("theme.mp3", persistent=True))
        assert f'{PERSIST_FLAG_ATTR}="true"' in html
        # `persistent` is not a real HTML attribute on native tags: it must
        # not render as a bare attribute nor leak into the style attribute.
        assert ' persistent="' not in html
        assert "persistent: True" not in html

    def test_persistent_video_renders_markers(self):
        html = render_html(Video("clip.mp4", persistent=True))
        assert f'{PERSIST_FLAG_ATTR}="true"' in html
        assert ' persistent="' not in html

    def test_persistent_clock_renders_markers(self):
        html = render_html(Clock(1000, "ticked", persistent=True))
        assert f'{PERSIST_FLAG_ATTR}="true"' in html

    def test_non_persistable_component_has_no_markers(self):
        html = render_html(Text("Hello"))
        assert PERSIST_KEY_ATTR not in html
        assert PERSIST_FLAG_ATTR not in html


class TestKeyDerivation:
    def test_same_arguments_produce_same_key(self):
        assert get_key(Audio("theme.mp3", persistent=True)) == get_key(
            Audio("theme.mp3", persistent=True)
        )

    def test_different_arguments_produce_different_keys(self):
        assert get_key(Audio("theme.mp3", persistent=True)) != get_key(
            Audio("other.mp3", persistent=True)
        )

    def test_different_tags_produce_different_keys(self):
        assert get_key(Audio("a.mp3", persistent=True)) != get_key(
            Video("a.mp3", persistent=True)
        )

    def test_persistent_flag_does_not_change_key(self):
        # A non-persistent render of the same component must share the key so
        # it can evict the parked version.
        assert get_key(Audio("theme.mp3")) == get_key(
            Audio("theme.mp3", persistent=True)
        )
        assert get_key(Timer(5000, "finished")) == get_key(
            Timer(5000, "finished", persistent=True)
        )

    def test_explicit_id_used_verbatim_as_key(self):
        component = Audio("theme.mp3", persistent=True, id="background-music")
        assert get_key(component) == "background-music"

    def test_derived_key_includes_tag(self):
        key = derive_persist_key("audio", {"src": "theme.mp3"})
        assert key.startswith("audio:")


class TestRemovePersistent:
    def test_renders_hidden_evict_marker(self):
        html = render_html(RemovePersistent("background-music"))
        assert f'{PERSIST_EVICT_ATTR}="background-music"' in html
        assert "hidden" in html

    def test_component_target_matches_component_key(self):
        audio = Audio("theme.mp3", persistent=True)
        html = render_html(RemovePersistent(Audio("theme.mp3", persistent=True)))
        assert f'{PERSIST_EVICT_ATTR}="{get_key(audio)}"' in html

    def test_resolve_key_from_string(self):
        assert resolve_persist_key("some-key") == "some-key"

    def test_resolve_key_rejects_non_persistable_component(self):
        with pytest.raises(ValueError):
            resolve_persist_key(Text("Hello"))

    def test_resolve_key_rejects_non_component(self):
        with pytest.raises(ValueError):
            resolve_persist_key(42)

    def test_repr_round_trips(self):
        component = RemovePersistent("background-music")
        assert eval(repr(component), {"RemovePersistent": RemovePersistent})
