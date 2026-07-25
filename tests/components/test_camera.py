"""Tests for the Camera component: validation, attribute serialization,
its registered contract, and the Photo converter."""

import json

import pytest

from drafter.components.camera import Camera, Photo
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


class TestCameraValidation:
    def test_rejects_bad_name(self):
        with pytest.raises(ValueError):
            Camera("not a name!")

    def test_rejects_bad_facing(self):
        with pytest.raises(ValueError):
            Camera("photo", facing="sideways")

    def test_accepts_both_facing_modes(self):
        Camera("photo", facing="user")
        Camera("photo", facing="environment")

    @pytest.mark.parametrize("bad_dimension", [0, -100, 2.5, True, "wide"])
    def test_rejects_bad_dimensions(self, bad_dimension):
        with pytest.raises(ValueError):
            Camera("photo", width=bad_dimension)
        with pytest.raises(ValueError):
            Camera("photo", height=bad_dimension)


class TestAttributeSerialization:
    def test_defaults_are_omitted_from_attributes(self):
        # Keyword arguments still at their defaults are not rendered; the
        # <drafter-camera> element supplies the same defaults itself.
        attributes = Camera("photo").get_attributes(None)
        assert attributes["name"] == "photo"
        for omitted in ("width", "height", "facing", "mirror", "show"):
            assert omitted not in attributes

    def test_non_default_settings_render(self):
        attributes = Camera(
            "photo", width=1280, height=720, facing="environment", mirror=False
        ).get_attributes(None)
        assert attributes["width"] == 1280
        assert attributes["height"] == 720
        assert attributes["facing"] == "environment"
        assert attributes["mirror"] is False

    def test_renders_handlers(self):
        def got_photo(state):
            pass

        attributes = Camera("photo", on_capture=got_photo).get_attributes(None)
        handlers = json.loads(attributes["data--drafter-handlers"])
        assert handlers == {"capture": "got_photo"}


class TestContractRegistered:
    def test_contract_registered(self):
        contract = COMPONENT_CONTRACT_REGISTRY.get("Camera")
        assert contract is not None
        assert contract.html_tag == "drafter-camera"

    def test_capture_event_in_contract(self):
        contract = COMPONENT_CONTRACT_REGISTRY.get("Camera")
        event_names = {event.event_name for event in contract.emitted_events}
        assert event_names == {"capture", "denied", "error"}


class TestPhotoConversion:
    def test_json_string_converts(self):
        payload = json.dumps(
            {
                "status": "granted",
                "message": "Photo captured",
                "data_url": "data:image/png;base64,AAAA",
                "width": 640,
                "height": 480,
            }
        )
        result = convert(payload, Photo, param_name="photo")
        assert result.ok
        assert result.value == Photo(
            status="granted",
            message="Photo captured",
            data_url="data:image/png;base64,AAAA",
            width=640,
            height=480,
        )

    def test_dict_converts(self):
        result = convert({"status": "denied"}, Photo)
        assert result.ok
        assert result.value.status == "denied"

    def test_malformed_json_becomes_error_status(self):
        result = convert("{not json", Photo)
        assert result.ok
        assert result.value.status == "error"
        assert "Failed to parse" in result.value.message

    def test_unknown_fields_become_error_status(self):
        result = convert(json.dumps({"status": "granted", "extra": 1}), Photo)
        assert result.ok
        assert result.value.status == "error"

    def test_existing_instance_passes_through(self):
        photo = Photo(status="granted", data_url="data:image/png;base64,AAAA")
        result = convert(photo, Photo)
        assert result.ok
        assert result.value is photo

    def test_prompt_status_converts(self):
        result = convert(
            json.dumps({"status": "prompt", "message": "Nothing yet"}),
            Photo,
        )
        assert result.ok
        assert result.value.status == "prompt"
        assert result.value.data_url is None
