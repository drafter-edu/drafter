"""
Tests for the router-side parameter pipeline:
Collect -> Normalize -> Bind -> Convert -> Diagnose.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Literal, Optional, Union

import pytest

from drafter.components.geolocation import Location
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
)
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY
from drafter.data.converter import ConversionContext
from drafter.data.files import DrafterBinaryFile, DrafterTextFile
from drafter.data.payload import PayloadValue
from drafter.data.request import Request
from drafter.router.parameters.binding import PayloadMerger, RouteBinder
from drafter.router.parameters.collect import collect_payload, normalize_payload
from drafter.router.parameters.conversion import CONVERTER_REGISTRY
from drafter.router.parameters.diagnostics import ParameterBindingError
from drafter.router.parameters.introspect import get_signature
from drafter.router.routes import Router


def convert(value: Any, expected_type: Any, param_name: str = "value"):
    """Convert one value through the shared registry."""
    return CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name=param_name,
            expected_type=expected_type,
            raw_value=value,
        )
    )


def form_value(name: str, value: Any) -> PayloadValue:
    return PayloadValue(name=name, value=value, source="form_field")


def bind(func, payload_values: list[PayloadValue], state=None, deps=None):
    signature = get_signature(func)
    merged, merge_diagnostics = PayloadMerger().merge(
        payload_values, route_name=signature.function_name
    )
    bound = RouteBinder().bind(
        signature,
        merged,
        converter_registry=CONVERTER_REGISTRY,
        state=state,
        extra_dependencies=deps or {},
    )
    return bound, merge_diagnostics


def upload(content: bytes, filename="report.txt", mimetype="text/plain") -> dict:
    return {
        "__file_upload__": True,
        "filename": filename,
        "content": content,
        "type": mimetype,
        "size": len(content),
    }


# ============================================================================
# CONVERSION
# ============================================================================


class TestScalarConversion:
    def test_untyped_passes_through(self):
        import inspect

        result = convert(["raw", "list"], inspect.Parameter.empty)
        assert result.ok and result.value == ["raw", "list"]

    def test_int_from_string(self):
        assert convert("5", int).value == 5

    def test_int_from_integral_float_string(self):
        assert convert("5.0", int).value == 5

    def test_int_failure_is_student_friendly(self):
        result = convert("twenty", int, param_name="age")
        assert not result.ok
        assert "Parameter 'age' expects int but got 'twenty'" in result.message
        assert result.hint

    def test_float_from_string(self):
        assert convert("2.5", float).value == 2.5

    def test_bool_from_checkbox_strings(self):
        assert convert("on", bool).value is True
        assert convert("false", bool).value is False
        assert convert("", bool).value is False
        assert convert(True, bool).value is True

    def test_bool_failure(self):
        assert not convert("maybe", bool).ok

    def test_str_unchanged(self):
        result = convert("hello", str)
        assert result.ok and result.value == "hello"

    def test_str_from_bytes(self):
        assert convert(b"hello", str).value == "hello"

    def test_single_item_list_flattens_for_scalar(self):
        assert convert(["7"], int).value == 7


class TestTypingConstructs:
    def test_optional_none(self):
        assert convert(None, Optional[int]).value is None

    def test_optional_converts(self):
        assert convert("5", Optional[int]).value == 5

    def test_union_prefers_existing_instance(self):
        result = convert(5, Union[int, str])
        assert result.value == 5

    def test_union_passthrough_when_member_already_matches(self):
        # "5" is already a valid str, so it is not coerced to int.
        assert convert("5", Union[int, str]).value == "5"

    def test_union_tries_members_in_order(self):
        assert convert("5", Union[int, float]).value == 5

    def test_literal_match(self):
        assert convert("red", Literal["red", "blue"]).value == "red"

    def test_literal_converts_stringified_option(self):
        assert convert("3", Literal[3, 5]).value == 3

    def test_literal_failure_lists_options(self):
        result = convert("green", Literal["red", "blue"])
        assert not result.ok
        assert "'red'" in result.hint and "'blue'" in result.hint


class TestCollectionConversion:
    def test_list_kept(self):
        assert convert(["a", "b"], list).value == ["a", "b"]

    def test_scalar_wrapped_into_list(self):
        assert convert("a", list).value == ["a"]

    def test_list_elements_converted(self):
        assert convert(["1", "2"], list[int]).value == [1, 2]

    def test_list_scalar_wrapped_and_converted(self):
        assert convert("1", list[int]).value == [1]

    def test_element_failure_reports_index(self):
        result = convert(["1", "x"], list[int], param_name="scores")
        assert not result.ok
        assert "scores[1]" in result.message

    def test_set_conversion(self):
        assert convert(["a", "a", "b"], set).value == {"a", "b"}


class TestDatetimeConversion:
    def test_datetime_from_iso(self):
        assert convert("2024-01-31T13:30:00", datetime).value == datetime(
            2024, 1, 31, 13, 30
        )

    def test_date_from_iso(self):
        assert convert("2024-01-31", date).value == date(2024, 1, 31)

    def test_time_from_iso(self):
        assert convert("13:30:00", time).value == time(13, 30)

    def test_bad_iso_fails_with_hint(self):
        result = convert("yesterday", date)
        assert not result.ok
        assert "ISO" in result.hint


class TestDataclassConversion:
    def test_dict_to_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        result = convert({"x": "1", "y": 2}, Point)
        assert result.ok and result.value == Point(1, 2)

    def test_json_string_to_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        result = convert(json.dumps({"x": 1, "y": 2}), Point)
        assert result.ok and result.value == Point(1, 2)

    def test_missing_required_field_fails(self):
        @dataclass
        class Point:
            x: int
            y: int

        result = convert({"x": 1}, Point)
        assert not result.ok
        assert "'y'" in result.hint

    def test_defaults_apply(self):
        @dataclass
        class Config:
            name: str
            level: int = 3

        result = convert({"name": "a"}, Config)
        assert result.ok and result.value == Config("a", 3)

    def test_nested_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        @dataclass
        class Line:
            start: Point
            end: Point

        result = convert(
            {"start": {"x": "0", "y": "0"}, "end": {"x": "3", "y": "4"}}, Line
        )
        assert result.ok and result.value == Line(Point(0, 0), Point(3, 4))

    def test_dataclass_to_dict(self):
        @dataclass
        class Point:
            x: int
            y: int

        result = convert(Point(1, 2), dict)
        assert result.ok and result.value == {"x": 1, "y": 2}


class TestFileUploadConversion:
    def test_to_bytes(self):
        assert convert(upload(b"data"), bytes).value == b"data"

    def test_to_str(self):
        assert convert(upload(b"hello"), str).value == "hello"

    def test_to_str_bad_unicode_fails(self):
        result = convert(upload(b"\xff\xfe\xfa"), str)
        assert not result.ok

    def test_to_dict(self):
        result = convert(upload(b"data", filename="f.bin"), dict)
        assert result.ok
        assert result.value["filename"] == "f.bin"
        assert result.value["content"] == b"data"

    def test_to_binary_file(self):
        result = convert(upload(b"data", filename="f.bin"), DrafterBinaryFile)
        assert result.ok
        assert result.value == DrafterBinaryFile("f.bin", b"data", "text/plain", 4)

    def test_to_text_file(self):
        result = convert(upload(b"hello"), DrafterTextFile)
        assert result.ok
        assert result.value.content == "hello"
        assert result.value.filename == "report.txt"

    def test_upload_dict_wins_over_dataclass_conversion(self):
        # DrafterBinaryFile is itself a dataclass; the file-upload converter
        # must intercept before the generic dict->dataclass converter.
        result = convert(upload(b"x"), DrafterBinaryFile)
        assert result.ok and isinstance(result.value, DrafterBinaryFile)


def png_upload(filename="dog.png"):
    import io

    from PIL import Image as PILImage

    output = io.BytesIO()
    PILImage.new("RGB", (4, 3), "red").save(output, format="PNG")
    return upload(output.getvalue(), filename=filename, mimetype="image/png")


class TestPictureConversion:
    def make_data_url(self):
        from drafter.data.images import Picture, bytes_to_data_url

        return bytes_to_data_url(Picture.new(2, 2, "blue").to_bytes(), "image/png")

    def test_upload_to_picture(self):
        from drafter.data.images import Picture

        result = convert(png_upload(), Picture)
        assert result.ok
        assert isinstance(result.value, Picture)
        assert result.value.filename == "dog.png"
        assert (result.value.width, result.value.height) == (4, 3)

    def test_upload_to_pil_still_works(self):
        from PIL import Image as PILImage

        result = convert(png_upload(), PILImage.Image)
        assert result.ok
        assert isinstance(result.value, PILImage.Image)

    def test_non_image_upload_fails_helpfully(self):
        from drafter.data.images import Picture

        result = convert(upload(b"just text", filename="notes.txt"), Picture)
        assert not result.ok
        assert "notes.txt" in result.hint

    def test_empty_upload_fails_for_bare_picture(self):
        from drafter.data.images import Picture

        result = convert(upload(b"", filename=""), Picture, param_name="photo")
        assert not result.ok
        assert result.error_code == "missing_value"
        assert "optional" in result.hint.lower()

    def test_empty_upload_becomes_none_for_optional_picture(self):
        from typing import Optional

        from drafter.data.images import Picture

        result = convert(upload(b"", filename=""), Optional[Picture])
        assert result.ok and result.value is None

    def test_camera_dict_to_picture(self):
        from drafter.data.images import Picture

        result = convert(
            {"status": "granted", "data_url": self.make_data_url()}, Picture
        )
        assert result.ok
        assert isinstance(result.value, Picture)
        assert (result.value.width, result.value.height) == (2, 2)

    def test_denied_camera_fails_for_bare_picture(self):
        from drafter.data.images import Picture

        result = convert(
            {"status": "denied", "message": "no camera", "data_url": None}, Picture
        )
        assert not result.ok
        assert result.error_code == "missing_value"
        assert "denied" in result.hint

    def test_denied_camera_becomes_none_for_optional_picture(self):
        from drafter.data.images import Picture

        result = convert({"status": "denied", "data_url": None}, Picture | None)
        assert result.ok and result.value is None

    def test_data_url_string_to_picture(self):
        from drafter.data.images import Picture

        result = convert(self.make_data_url(), Picture)
        assert result.ok and result.value.width == 2

    def test_url_string_to_lazy_picture(self):
        from drafter.data.images import Picture

        result = convert("https://example.com/dog.png", Picture)
        assert result.ok
        assert not result.value.is_loaded()
        assert result.value.url == "https://example.com/dog.png"

    def test_photo_to_picture(self):
        from drafter.components.data.photo import Photo
        from drafter.data.images import Picture

        photo = Photo(status="granted", data_url=self.make_data_url())
        result = convert(photo, Picture)
        assert result.ok and isinstance(result.value, Picture)

    def test_picture_passes_through(self):
        from drafter.data.images import Picture

        picture = Picture.new(2, 2)
        result = convert(picture, Picture)
        assert result.ok and result.value is picture

    def test_photo_picture_property(self):
        from drafter.components.data.photo import Photo

        photo = Photo(status="granted", data_url=self.make_data_url())
        assert photo.picture is not None
        assert photo.picture.width == 2
        assert photo.picture is photo.picture  # cached
        assert Photo(status="denied").picture is None


class TestCameraBytesConversion:
    def make_data_url(self):
        from drafter.data.images import Picture, bytes_to_data_url

        return bytes_to_data_url(Picture.new(2, 2, "blue").to_bytes(), "image/png")

    def test_camera_dict_to_bytes(self):
        from drafter.data.images import sniff_image_mime

        result = convert({"status": "granted", "data_url": self.make_data_url()}, bytes)
        assert result.ok
        assert sniff_image_mime(result.value) == "image/png"

    def test_data_url_string_to_bytes(self):
        from drafter.data.images import sniff_image_mime

        result = convert(self.make_data_url(), bytes)
        assert result.ok
        assert sniff_image_mime(result.value) == "image/png"

    def test_denied_camera_fails_for_bare_bytes(self):
        result = convert({"status": "denied", "data_url": None}, bytes)
        assert not result.ok
        assert result.error_code == "missing_value"

    def test_denied_camera_becomes_none_for_optional_bytes(self):
        result = convert({"status": "denied", "data_url": None}, bytes | None)
        assert result.ok and result.value is None

    def test_upload_to_bytes_still_works(self):
        assert convert(upload(b"data"), bytes).value == b"data"


class TestLocationConversion:
    def test_from_json_string(self):
        raw = json.dumps({"status": "granted", "latitude": 39.68, "longitude": -75.75})
        result = convert(raw, Location)
        assert result.ok
        assert result.value.status == "granted"
        assert result.value.latitude == 39.68

    def test_from_dict(self):
        result = convert({"status": "denied"}, Location)
        assert result.ok and result.value.status == "denied"

    def test_bad_json_becomes_error_status(self):
        result = convert("{not json", Location)
        assert result.ok
        assert result.value.status == "error"


# ============================================================================
# MERGING
# ============================================================================


class TestPayloadMerger:
    def test_component_argument_beats_form_field(self):
        merged, diagnostics = PayloadMerger().merge(
            [
                form_value("count", "3"),
                PayloadValue("count", "9", "component_argument"),
            ]
        )
        assert merged["count"].value == "9"
        assert merged["count"].source == "component_argument"
        assert len(diagnostics) == 1
        assert diagnostics[0].code == "payload_collision"
        assert "'9'" in diagnostics[0].message and "'3'" in diagnostics[0].message

    def test_event_detail_beats_form_field(self):
        merged, _ = PayloadMerger().merge(
            [
                form_value("remaining", "100"),
                PayloadValue("remaining", 42, "event_detail"),
            ]
        )
        assert merged["remaining"].value == 42

    def test_equal_values_do_not_warn(self):
        merged, diagnostics = PayloadMerger().merge(
            [
                form_value("count", "3"),
                PayloadValue("count", "3", "event_detail"),
            ]
        )
        assert merged["count"].value == "3"
        assert diagnostics == ()


# ============================================================================
# BINDING
# ============================================================================


class TestRouteBinder:
    def test_binds_and_converts(self):
        def add(x: int, y: int):
            return x + y

        bound, _ = bind(add, [form_value("x", "5"), form_value("y", "3")])
        assert bound.diagnostics == ()
        assert bound.kwargs == {"x": 5, "y": 3}
        assert bound.consumed_payload_keys == {"x", "y"}

    def test_default_applies_when_missing(self):
        def greet(name: str = "World"):
            return name

        bound, _ = bind(greet, [])
        assert bound.diagnostics == ()
        assert "name" not in bound.kwargs

    def test_missing_required_is_error(self):
        def greet(name: str, other: str):
            return name

        bound, _ = bind(greet, [form_value("name", "x")])
        errors = [d for d in bound.diagnostics if d.severity == "error"]
        assert len(errors) == 1
        assert errors[0].code == "missing_required_parameter"
        assert errors[0].parameter == "other"

    def test_missing_gets_near_miss_suggestion(self):
        def greet(name: str):
            return name

        bound, _ = bind(greet, [form_value("nmae", "x")])
        errors = [d for d in bound.diagnostics if d.severity == "error"]
        assert "'nmae'" in errors[0].hint

    def test_unused_key_is_warning(self):
        def greet(name: str):
            return name

        bound, _ = bind(greet, [form_value("name", "x"), form_value("extra", "y")])
        warnings = [d for d in bound.diagnostics if d.severity == "warning"]
        assert len(warnings) == 1
        assert warnings[0].code == "unused_request_parameter"
        assert warnings[0].parameter == "extra"
        assert "extra" not in bound.kwargs

    def test_var_keyword_absorbs_unused_without_warning(self):
        def flexible(name: str, **rest):
            return name

        bound, _ = bind(flexible, [form_value("name", "x"), form_value("extra", "y")])
        assert bound.diagnostics == ()
        assert bound.kwargs["extra"] == "y"

    def test_state_injected_by_name(self):
        def index(state):
            return state

        bound, _ = bind(index, [], state={"count": 1})
        assert bound.args == ({"count": 1},)

    def test_state_injected_by_arity(self):
        def index(my_state):
            return my_state

        bound, _ = bind(index, [], state={"count": 1})
        assert bound.args == ({"count": 1},)

    def test_state_not_injected_when_payload_fills_signature(self):
        def greet(name: str):
            return name

        bound, _ = bind(greet, [form_value("name", "x")], state={"count": 1})
        assert bound.args == ()
        assert bound.kwargs == {"name": "x"}

    def test_dependencies_injected_by_name(self):
        def inspect_route(_request, value: int):
            return value

        request = object()
        bound, _ = bind(
            inspect_route,
            [form_value("value", "2")],
            deps={"_request": request},
        )
        assert bound.kwargs["_request"] is request
        assert bound.kwargs["value"] == 2

    def test_underscore_dependency_not_required(self):
        def inspect_route(_request, value: int = 0):
            return value

        bound, _ = bind(inspect_route, [])
        errors = [d for d in bound.diagnostics if d.severity == "error"]
        assert errors == []

    def test_framework_meta_never_warns_when_unused(self):
        def greet(name: str = "x"):
            return name

        bound, _ = bind(
            greet,
            [PayloadValue("button_pressed", "save", "framework_meta")],
        )
        assert bound.diagnostics == ()

    def test_framework_meta_binds_when_declared(self):
        def handle(button_pressed: str = ""):
            return button_pressed

        bound, _ = bind(
            handle,
            [PayloadValue("button_pressed", "save", "framework_meta")],
        )
        assert bound.kwargs["button_pressed"] == "save"

    def test_conversion_failure_is_error_diagnostic(self):
        def add(x: int):
            return x

        bound, _ = bind(add, [form_value("x", "twenty")])
        errors = [d for d in bound.diagnostics if d.severity == "error"]
        assert len(errors) == 1
        assert errors[0].code == "conversion_failed"
        assert "form field 'x'" in errors[0].message

    def test_conversion_records_kept_for_debugging(self):
        def add(x: int, label: str):
            return x

        bound, _ = bind(add, [form_value("x", "5"), form_value("label", "hi")])
        kinds = {type(record).__name__ for record in bound.conversions}
        assert kinds == {"ConversionRecord", "UnchangedRecord"}


# ============================================================================
# COLLECT AND NORMALIZE
# ============================================================================


class TestCollect:
    def test_kwargs_fallback_is_form_field(self):
        request = Request("submit", "greet", {"name": "x"}, {})
        payload = collect_payload(request)
        assert len(payload) == 1
        assert payload[0].source == "form_field"

    def test_raw_payload_preferred_with_sources(self):
        request = Request(
            "submit",
            "greet",
            {"name": "x", "remaining": 42},
            {},
            raw_payload=[
                {"name": "name", "value": "x", "source": "form_field"},
                {"name": "remaining", "value": 42, "source": "event_detail"},
            ],
        )
        payload = collect_payload(request)
        sources = {value.name: value.source for value in payload}
        assert sources == {"name": "form_field", "remaining": "event_detail"}

    def test_submit_button_key_excluded(self):
        request = Request("submit", "greet", {"--submit-button": "x"}, {})
        assert collect_payload(request) == []

    def test_button_pressed_becomes_framework_meta(self):
        request = Request("submit", "greet", {}, {})
        payload = collect_payload(request, button_pressed="save")
        assert payload[0].name == "button_pressed"
        assert payload[0].source == "framework_meta"

    def test_normalize_applies_alias(self):
        payload = [form_value("remaining_ms", 10)]
        normalized = normalize_payload(payload, {"remaining_ms": "remaining"})
        assert normalized[0].name == "remaining"
        assert "remaining_ms" in normalized[0].source_detail


class TestContractRegistry:
    def test_timer_contract_registered(self):
        contract = COMPONENT_CONTRACT_REGISTRY.get("Timer")
        assert contract is not None
        assert contract.html_tag == "drafter-timer"
        event_names = {event.event_name for event in contract.emitted_events}
        assert event_names == {"tick", "finish"}

    def test_alias_map_aggregation(self):
        contract = ComponentContract(
            component_name="__TestWidget",
            html_tag="test-widget",
            emitted_events=[
                EventPayloadSpec(
                    event_name="ping",
                    fields=[EventPayloadFieldSpec("count", int, "The count.")],
                    aliases={"count": ["total", "n"]},
                )
            ],
        )
        COMPONENT_CONTRACT_REGISTRY.register(contract)
        try:
            alias_map = COMPONENT_CONTRACT_REGISTRY.alias_map()
            assert alias_map["total"] == "count"
            assert alias_map["n"] == "count"
        finally:
            COMPONENT_CONTRACT_REGISTRY._contracts.pop("__TestWidget")


# ============================================================================
# FULL PIPELINE THROUGH THE ROUTER
# ============================================================================


class TestRouterPipeline:
    def make_router(self, func, url="test"):
        router = Router()
        router.add_route(url, func)
        return router

    def prepare(self, router, request, state=None, deps=None):
        return router.prepare_arguments(request, state, None, deps or {})

    def test_prepares_converted_arguments(self):
        def add(x: int, y: int):
            return x + y

        router = self.make_router(add)
        request = Request("submit", "test", {"x": "5", "y": "3"}, {})
        args, kwargs, representation, _provenance = self.prepare(router, request)
        assert args == []
        assert kwargs == {"x": 5, "y": 3}
        assert representation == "add(5, 3)"

    def test_missing_parameter_raises_binding_error(self):
        def greet(name: str):
            return name

        router = self.make_router(greet)
        request = Request("submit", "test", {"nmae": "oops"}, {})
        with pytest.raises(ParameterBindingError) as exc_info:
            self.prepare(router, request)
        assert "name" in str(exc_info.value)
        assert exc_info.value.diagnostics[0].code == "missing_required_parameter"

    def test_conversion_failure_raises_with_source_and_hint(self):
        def age_route(age: int):
            return age

        router = self.make_router(age_route)
        request = Request("submit", "test", {"age": "twenty"}, {})
        with pytest.raises(ParameterBindingError) as exc_info:
            self.prepare(router, request)
        message = str(exc_info.value)
        assert "Parameter 'age' expects int but got 'twenty'" in message
        assert "form field 'age'" in message

    def test_unused_parameter_warns_but_succeeds(self):
        def greet(name: str = "World"):
            return name

        router = self.make_router(greet)
        request = Request("submit", "test", {"name": "x", "stray": "y"}, {})
        args, kwargs, _, _provenance = self.prepare(router, request)
        assert kwargs == {"name": "x"}

    def test_injected_dependencies_bind_but_stay_out_of_representation(self):
        def add_stop(state, x: int, add_marker):
            return x

        helper = lambda label="": None  # noqa: E731

        router = self.make_router(add_stop)
        request = Request("pin", "test", {"x": "5"}, {})
        args, kwargs, representation, _provenance = self.prepare(
            router, request, state="STATE", deps={"add_marker": helper}
        )
        assert kwargs["add_marker"] is helper
        assert kwargs["x"] == 5
        assert representation == "add_stop('STATE', 5)"

    def test_state_injection_still_works(self):
        def index(state):
            return state

        router = self.make_router(index)
        request = Request("click", "test", {}, {})
        args, kwargs, _, _provenance = self.prepare(router, request, state={"count": 3})
        assert args == [{"count": 3}]
        assert kwargs == {}

    def test_event_detail_beats_form_field_through_pipeline(self):
        def on_tick(remaining: int):
            return remaining

        router = self.make_router(on_tick)
        request = Request(
            "tick",
            "test",
            {"remaining": 42},
            {},
            raw_payload=[
                {"name": "remaining", "value": "999", "source": "form_field"},
                {"name": "remaining", "value": 42, "source": "event_detail"},
            ],
        )
        args, kwargs, _, _provenance = self.prepare(router, request)
        assert kwargs == {"remaining": 42}

    def test_add_route_reports_signature_string(self):
        def add(x: int, y: int = 0):
            return x + y

        router = Router()
        info = router.add_route("add", add)
        assert info["signature"] == "add(x: int, y: int)"

    def test_add_route_reports_structured_parameters(self):
        def add(state, x: int, y: int = 0, _server=None):
            return x + y

        router = Router()
        info = router.add_route("add", add)
        # state and injected parameters are omitted; request parameters
        # carry name/type/required/default for the debug panel's forms.
        assert info["parameters"] == [
            {"name": "x", "type": "int", "required": True, "default": None},
            {"name": "y", "type": "int", "required": False, "default": "0"},
        ]

    def test_provenance_tracks_sources_and_conversions(self):
        def guess(state, answer: int, hint: str = "none"):
            return answer

        router = self.make_router(guess)
        request = Request(
            "submit",
            "test",
            {"answer": "5"},
            {},
            raw_payload=[
                {"name": "answer", "value": "5", "source": "form_field"},
            ],
        )
        _, _, _, provenance = self.prepare(router, request, state={"n": 1})

        by_name = {entry["name"]: entry for entry in provenance}
        assert by_name["state"]["source"] == "state"
        assert by_name["answer"]["source"] == "form_field"
        assert by_name["answer"]["changed"] is True
        assert by_name["answer"]["converted"] == "5"
        assert by_name["answer"]["expected_type"] == "int"
        assert by_name["hint"]["source"] == "default"
        assert by_name["hint"]["value"] == "'none'"
