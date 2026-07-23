"""Tests for the Map component: center/marker normalization, attribute
serialization, event handler wiring, persistence identity, repr round-trip,
and the MapLocation/MapMarker/MapView converters."""

import json

import pytest

from drafter.components.map import Map, MapLocation, MapMarker, MapView
from drafter.components.utilities.contracts import HelperContext
from drafter.components.utilities.persistence import PERSIST_KEY_ATTR
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY
from drafter.data.converter import ConversionContext

# Loading the router conversion module installs the shared converters and is
# how the app guarantees component converters are registered too.
from drafter.router.parameters.conversion import CONVERTER_REGISTRY


def convert(value, expected_type, param_name="value"):
    """Convert one value through the shared registry."""
    return CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name=param_name,
            expected_type=expected_type,
            raw_value=value,
        )
    )


class TestCenterNormalization:
    def test_accepts_map_location(self):
        component = Map("spot", center=MapLocation(39.68, -75.75))
        assert component.center == MapLocation(39.68, -75.75)

    def test_accepts_pair(self):
        component = Map("spot", center=(39.68, -75.75))
        assert component.center == MapLocation(39.68, -75.75)

    def test_accepts_string(self):
        component = Map("spot", center="39.68,-75.75")
        assert component.center == MapLocation(39.68, -75.75)

    def test_defaults_to_none(self):
        assert Map("spot").center is None

    @pytest.mark.parametrize("bad_center", ["not-a-place", (1, 2, 3), 5])
    def test_rejects_bad_center(self, bad_center):
        with pytest.raises(ValueError):
            Map("spot", center=bad_center)


class TestMarkerNormalization:
    def test_accepts_map_markers(self):
        component = Map("spot", markers=[MapMarker(1.0, 2.0, "Home")])
        assert component.markers == [MapMarker(1.0, 2.0, "Home")]

    def test_accepts_locations_and_pairs(self):
        component = Map(
            "spot", markers=[MapLocation(1.0, 2.0), (3.0, 4.0), (5.0, 6.0, "C")]
        )
        assert component.markers == [
            MapMarker(1.0, 2.0),
            MapMarker(3.0, 4.0),
            MapMarker(5.0, 6.0, "C"),
        ]

    def test_rejects_bad_marker(self):
        with pytest.raises(ValueError):
            Map("spot", markers=["nope"])


class TestAttributes:
    def test_center_and_markers_serialize(self):
        attributes = Map(
            "spot",
            center=MapLocation(39.68, -75.75),
            markers=[MapMarker(39.68, -75.75, "Newark")],
        ).get_attributes(None)
        assert attributes["center"] == "39.68,-75.75"
        assert json.loads(attributes["markers"]) == [
            {"latitude": 39.68, "longitude": -75.75, "label": "Newark"}
        ]

    def test_defaults_are_omitted(self):
        attributes = Map("spot").get_attributes(None)
        assert "center" not in attributes
        assert "markers" not in attributes
        assert "zoom" not in attributes
        assert "height" not in attributes

    def test_event_handlers_map_to_custom_events(self):
        def add_stop(state):
            pass

        def show_stop(state):
            pass

        def update_view(state):
            pass

        attributes = Map(
            "spot",
            on_click=add_stop,
            on_marker_click=show_stop,
            on_move=update_view,
        ).get_attributes(None)
        handlers = json.loads(attributes["data--drafter-handlers"])
        assert handlers == {
            "pin": "add_stop",
            "marker": "show_stop",
            "view": "update_view",
        }

    def test_persist_key_stable_across_marker_changes(self):
        plain = Map("spot", persistent=True).get_attributes(None)
        with_markers = Map(
            "spot",
            center=MapLocation(1.0, 2.0),
            zoom=10,
            markers=[MapMarker(1.0, 2.0)],
            persistent=True,
        ).get_attributes(None)
        assert plain[PERSIST_KEY_ATTR] == with_markers[PERSIST_KEY_ATTR]

    def test_persist_key_differs_by_name(self):
        first = Map("first").get_attributes(None)
        second = Map("second").get_attributes(None)
        assert first[PERSIST_KEY_ATTR] != second[PERSIST_KEY_ATTR]


class TestReprRoundTrip:
    def test_eval_round_trip(self):
        component = Map(
            "spot",
            center=MapLocation(39.68, -75.75),
            zoom=10,
            markers=[MapMarker(39.68, -75.75, "Newark")],
            height=400,
        )
        recreated = eval(repr(component))
        assert recreated == component


class TestConverters:
    def test_location_from_json_string(self):
        result = convert('{"latitude": 39.68, "longitude": -75.75}', MapLocation)
        assert result.ok
        assert result.value == MapLocation(39.68, -75.75)

    def test_location_from_dict(self):
        result = convert({"latitude": 1.5, "longitude": 2.5}, MapLocation)
        assert result.ok
        assert result.value == MapLocation(1.5, 2.5)

    def test_marker_from_dict(self):
        result = convert(
            {"latitude": 1.0, "longitude": 2.0, "label": "Home"}, MapMarker
        )
        assert result.ok
        assert result.value == MapMarker(1.0, 2.0, "Home")

    def test_view_from_dict(self):
        result = convert({"latitude": 1.0, "longitude": 2.0, "zoom": 13}, MapView)
        assert result.ok
        assert result.value == MapView(1.0, 2.0, 13)

    def test_passthrough(self):
        location = MapLocation(1.0, 2.0)
        result = convert(location, MapLocation)
        assert result.ok
        assert result.value is location

    def test_invalid_json_fails_cleanly(self):
        result = convert("{broken", MapLocation)
        assert not result.ok

    def test_unexpected_fields_fail_cleanly(self):
        result = convert({"latitude": 1.0, "wrong": 2.0}, MapLocation)
        assert not result.ok


def test_contract_registered():
    contract = COMPONENT_CONTRACT_REGISTRY.get("Map")
    assert contract is not None
    assert contract.html_tag == "drafter-map"
    assert {event.event_name for event in contract.emitted_events} == {
        "pin",
        "marker",
        "view",
    }


class FakeElement:
    """Stand-in for the live <drafter-map> DOM element."""

    def __init__(self, attributes=None):
        self.attributes = dict(attributes or {})

    def getAttribute(self, name):
        return self.attributes.get(name)

    def setAttribute(self, name, value):
        self.attributes[name] = value


def make_add_marker(element, values):
    (helper_spec,) = COMPONENT_CONTRACT_REGISTRY.helpers_for("drafter-map", "pin")
    return helper_spec.factory(HelperContext(element=element, values=values))


class TestAddMarkerHelper:
    def test_registered_for_pin_and_marker_but_not_view(self):
        for event in ("pin", "marker"):
            helpers = COMPONENT_CONTRACT_REGISTRY.helpers_for("drafter-map", event)
            assert [helper.name for helper in helpers] == ["add_marker"]
        assert COMPONENT_CONTRACT_REGISTRY.helpers_for("drafter-map", "view") == ()

    def test_tag_lookup_is_case_insensitive(self):
        # DOM tagName is uppercase.
        helpers = COMPONENT_CONTRACT_REGISTRY.helpers_for("DRAFTER-MAP", "pin")
        assert [helper.name for helper in helpers] == ["add_marker"]

    def test_unknown_tag_provides_nothing(self):
        assert COMPONENT_CONTRACT_REGISTRY.helpers_for("button", "pin") == ()

    def test_adds_pin_at_event_location(self):
        element = FakeElement()
        add_marker = make_add_marker(element, {"latitude": 39.68, "longitude": -75.75})
        add_marker("Home")
        assert json.loads(element.attributes["markers"]) == [
            {"latitude": 39.68, "longitude": -75.75, "label": "Home"}
        ]

    def test_label_defaults_to_empty(self):
        element = FakeElement()
        add_marker = make_add_marker(element, {"latitude": 1.0, "longitude": 2.0})
        add_marker()
        assert json.loads(element.attributes["markers"]) == [
            {"latitude": 1.0, "longitude": 2.0, "label": ""}
        ]

    def test_appends_to_existing_markers(self):
        element = FakeElement(
            {
                "markers": json.dumps(
                    [{"latitude": 0.0, "longitude": 0.0, "label": "Origin"}]
                )
            }
        )
        add_marker = make_add_marker(element, {"latitude": 1.0, "longitude": 2.0})
        add_marker("New")
        add_marker("Newer")
        markers = json.loads(element.attributes["markers"])
        assert [marker["label"] for marker in markers] == [
            "Origin",
            "New",
            "Newer",
        ]
