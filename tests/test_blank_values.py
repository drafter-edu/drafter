"""Tests for what a route receives when a field is left blank.

One rule covers every type. A blank number or date field, a file field
with no file chosen, and a camera with no photo are all "no value", and
the parameter receives, in this order:

1. None, when the annotation allows it;
2. the parameter's default, when it has one;
3. the type's own empty value, when it has one (today, for a `date`);
4. otherwise the request fails, saying no value was provided.

Blank text is not "no value" for `str` (it is the empty string) or for
`bool` (an unchecked box). Before this rule, `int | None` and `int = 7`
both failed on a blank field, and a file field with no file gave `''` for
`str | None` but None for `Picture | None`.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Literal, Optional

import pytest

from drafter.data.converter import (
    MISSING_VALUE_ERROR_CODE,
    ConversionContext,
)
from drafter.data.files import DrafterBinaryFile, DrafterTextFile
from drafter.data.images import Picture
from drafter.data.payload import PayloadValue
from drafter.router.parameters.binding import BoundArguments, RouteBinder
from drafter.router.parameters.conversion import CONVERTER_REGISTRY
from drafter.router.parameters.introspect import get_signature

NO_FILE = {
    "__file_upload__": True,
    "filename": "",
    "content": b"",
    "type": "application/octet-stream",
    "size": 0,
}
"""What the browser sends for a file field with no file chosen."""

A_DAY = date(2020, 1, 2)


def bind_one(func, value: Any, source: str = "form_field") -> BoundArguments:
    """Bind a route whose one form value is named `value`, after the state."""
    return RouteBinder().bind(
        get_signature(func),
        {"value": PayloadValue(name="value", value=value, source=source)},
        converter_registry=CONVERTER_REGISTRY,
        state={"count": 1},
    )


def errors_of(bound: BoundArguments) -> list:
    return [d for d in bound.diagnostics if d.severity == "error"]


class TestBlankNumber:
    @pytest.mark.parametrize("blank", ["", "   "])
    def test_optional_int_receives_none(self, blank):
        def route(state, value: int | None):
            return value

        bound = bind_one(route, blank)

        assert bound.diagnostics == ()
        assert bound.kwargs == {"value": None}

    def test_typing_optional_float_receives_none(self):
        def route(state, value: Optional[float]):
            return value

        assert bind_one(route, "").kwargs == {"value": None}

    def test_default_is_used(self):
        def route(state, value: int = 7):
            return value

        bound = bind_one(route, "")

        assert bound.diagnostics == ()
        # Left out of the call, so Python itself supplies the default.
        assert "value" not in bound.kwargs
        assert route(*bound.args, **bound.kwargs) == 7

    def test_default_use_is_recorded_for_the_debug_panel(self):
        def route(state, value: int = 7):
            return value

        (entry,) = [
            entry
            for entry in bind_one(route, "").provenance
            if entry["name"] == "value"
        ]

        assert entry["source"] == "default"
        assert entry["value"] == "7"
        assert "left blank" in entry["source_detail"]

    def test_none_comes_before_the_default(self):
        def route(state, value: int | None = 7):
            return value

        assert bind_one(route, "").kwargs == {"value": None}

    @pytest.mark.parametrize("number_type", [int, float])
    def test_required_number_fails_and_says_nothing_was_provided(self, number_type):
        def route(state, value):
            return value

        route.__annotations__["value"] = number_type

        (error,) = errors_of(bind_one(route, ""))

        assert error.code == "conversion_failed"
        assert f"expects {number_type.__name__} but no value was provided" in (
            error.message
        )
        assert "default value" in error.hint
        assert f"{number_type.__name__} | None" in error.hint

    def test_a_filled_field_still_wins_over_the_default(self):
        def route(state, value: int = 7):
            return value

        assert bind_one(route, "12").kwargs == {"value": 12}

    def test_text_that_is_not_a_number_is_still_a_plain_failure(self):
        def route(state, value: int | None = 7):
            return value

        (error,) = errors_of(bind_one(route, "twelve"))

        assert "but got 'twelve'" in error.message


class TestBlankTextAndCheckbox:
    """Blank text is a real value for these two types, so nothing changes."""

    def test_str_receives_the_empty_string(self):
        def route(state, value: str):
            return value

        assert bind_one(route, "").kwargs == {"value": ""}

    def test_optional_str_receives_the_empty_string(self):
        def route(state, value: str | None):
            return value

        assert bind_one(route, "").kwargs == {"value": ""}

    def test_str_default_is_not_used(self):
        def route(state, value: str = "World"):
            return value

        assert bind_one(route, "").kwargs == {"value": ""}

    def test_unchecked_box_is_false_even_with_a_true_default(self):
        def route(state, value: bool = True):
            return value

        assert bind_one(route, "").kwargs == {"value": False}

    def test_optional_bool_is_false(self):
        def route(state, value: bool | None):
            return value

        assert bind_one(route, "").kwargs == {"value": False}


class TestBlankDate:
    def test_bare_date_still_receives_today(self):
        def route(state, value: date):
            return value

        bound = bind_one(route, "")

        assert bound.diagnostics == ()
        assert bound.kwargs == {"value": date.today()}

    def test_bare_datetime_and_time_still_receive_now(self):
        def at(state, value: datetime):
            return value

        def clock(state, value: time):
            return value

        before = datetime.now()
        moment = bind_one(at, "").kwargs["value"]
        time_of_day = bind_one(clock, "").kwargs["value"]

        assert before <= moment <= datetime.now()
        assert isinstance(time_of_day, time)

    @pytest.mark.parametrize("date_type", [date, datetime, time])
    def test_optional_receives_none(self, date_type):
        def route(state, value):
            return value

        route.__annotations__["value"] = date_type | None

        assert bind_one(route, "").kwargs == {"value": None}

    def test_default_is_used(self):
        def route(state, value: date = A_DAY):
            return value

        bound = bind_one(route, "")

        assert route(*bound.args, **bound.kwargs) == A_DAY

    def test_a_chosen_date_is_unaffected(self):
        def route(state, value: date | None = A_DAY):
            return value

        assert bind_one(route, "2024-01-31").kwargs == {"value": date(2024, 1, 31)}


class TestNoFileChosen:
    @pytest.mark.parametrize("file_type", [str, bytes, DrafterTextFile, Picture])
    def test_optional_receives_none(self, file_type):
        def route(state, value):
            return value

        route.__annotations__["value"] = file_type | None

        bound = bind_one(route, dict(NO_FILE))

        assert bound.diagnostics == ()
        assert bound.kwargs == {"value": None}

    def test_default_is_used(self):
        def route(state, value: str = "nothing uploaded"):
            return value

        bound = bind_one(route, dict(NO_FILE))

        assert route(*bound.args, **bound.kwargs) == "nothing uploaded"

    def test_bare_str_and_bytes_receive_their_empty_value(self):
        def text(state, value: str):
            return value

        def data(state, value: bytes):
            return value

        assert bind_one(text, dict(NO_FILE)).kwargs == {"value": ""}
        assert bind_one(data, dict(NO_FILE)).kwargs == {"value": b""}

    def test_bare_file_object_is_empty(self):
        def route(state, value: DrafterBinaryFile):
            return value

        received = bind_one(route, dict(NO_FILE)).kwargs["value"]

        assert received.content == b""
        assert received.filename == ""

    def test_bare_picture_still_fails(self):
        def route(state, value: Picture):
            return value

        (error,) = errors_of(bind_one(route, dict(NO_FILE)))

        assert "no value was provided" in error.message

    def test_an_empty_file_that_was_chosen_is_not_missing(self):
        """A file with a name and nothing in it is a real, empty file."""

        def route(state, value: str | None = "default"):
            return value

        chosen = dict(NO_FILE, filename="empty.txt")

        assert bind_one(route, chosen).kwargs == {"value": ""}


class TestBlankChoice:
    def test_optional_literal_receives_none(self):
        def route(state, value: Literal["small", "large"] | None):
            return value

        assert bind_one(route, "").kwargs == {"value": None}

    def test_literal_default_is_used(self):
        def route(state, value: Literal["small", "large"] = "small"):
            return value

        bound = bind_one(route, "")

        assert route(*bound.args, **bound.kwargs) == "small"

    def test_blank_that_is_one_of_the_choices_is_kept(self):
        def route(state, value: Literal["", "large"] = "large"):
            return value

        assert bind_one(route, "").kwargs == {"value": ""}


class TestBlankInsideAValue:
    """A blank part of a list or dataclass is not a missing parameter."""

    def test_blank_item_fails_instead_of_using_the_default(self):
        def route(state, value: list[int] = [1, 2]):
            return value

        (error,) = errors_of(bind_one(route, ["3", ""]))

        assert "value[1]" in error.message

    def test_blank_item_does_not_turn_an_optional_list_into_none(self):
        def route(state, value: list[int] | None):
            return value

        assert len(errors_of(bind_one(route, ["3", ""]))) == 1

    def test_blank_date_field_of_a_dataclass_is_still_today(self):
        @dataclass
        class Visit:
            pet: str
            day: date

        def route(state, value: Visit):
            return value

        received = bind_one(route, {"pet": "Ada", "day": ""}).kwargs["value"]

        assert received == Visit("Ada", date.today())


class TestRegistryOnItsOwn:
    """Callers other than the binder get the empty value, as they always did."""

    def convert(self, value: Any, expected_type: Any, keep_missing: bool = False):
        context = ConversionContext(
            param_name="value", expected_type=expected_type, raw_value=value
        )
        return CONVERTER_REGISTRY.convert(context, keep_missing=keep_missing)

    def test_blank_date_converts_to_today(self):
        result = self.convert("", date)

        assert result.ok
        assert result.value == date.today()

    def test_keep_missing_reports_the_missing_value_with_its_empty_form(self):
        result = self.convert("", date, keep_missing=True)

        assert not result.ok
        assert result.error_code == MISSING_VALUE_ERROR_CODE
        assert result.has_empty_value
        assert result.value == date.today()

    def test_blank_int_has_no_empty_form(self):
        result = self.convert("", int)

        assert not result.ok
        assert result.error_code == MISSING_VALUE_ERROR_CODE
        assert not result.has_empty_value
