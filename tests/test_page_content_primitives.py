"""Plain integers, floats, and booleans are valid page content.

Covers the loosening of Page/Fragment content rules: plain values are
accepted by the constructors, the verify pipeline, the validators, the
renderer (top-level and nested in components), the styling helpers, and
the testing asserts. Other types (dicts, dataclasses, nested lists) are
still rejected with the student-facing error.
"""

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from drafter import (
    BulletedList,
    Button,
    Div,
    Fragment,
    Page,
    Text,
    bold,
)
from drafter.components.page_content import (
    normalize_page_content,
    validate_page_content,
)
from drafter.data.errors import StudentFacingError
from drafter.payloads.renderer import render


@dataclass
class Pet:
    name: str


FAKE_REQUEST = SimpleNamespace(url="index", dom_id=None)


class TestConstructorAcceptsPlainValues:
    def test_page_accepts_primitives_in_list(self):
        page = Page(None, ["Score:", 42, 3.14, True])
        assert page.content == ["Score:", 42, 3.14, True]

    def test_page_wraps_single_int(self):
        assert Page(None, 42).content == [42]

    def test_page_wraps_single_float(self):
        assert Page(None, 2.5).content == [2.5]

    def test_page_wraps_single_bool(self):
        assert Page(None, False).content == [False]

    def test_fragment_accepts_primitives(self):
        fragment = Fragment(None, [1, 2.0, True, "x"])
        assert fragment.content == [1, 2.0, True, "x"]

    def test_page_rejects_dict_content(self):
        with pytest.raises(StudentFacingError):
            Page(None, {"score": 42})

    def test_page_rejects_dataclass_item(self):
        with pytest.raises(StudentFacingError):
            Page(None, [Pet("Ada")])

    def test_page_rejects_nested_list_item(self):
        with pytest.raises(StudentFacingError):
            Page(None, [["nested"]])


class TestValidators:
    @pytest.mark.parametrize("value", [42, 3.14, True, False, "text"])
    def test_validate_accepts_plain_values(self, value):
        is_valid, message = validate_page_content(value)
        assert is_valid
        assert message == ""

    def test_validate_accepts_mixed_list(self):
        is_valid, message = validate_page_content(["Score:", 42, True])
        assert is_valid

    def test_validate_rejects_other_types(self):
        is_valid, message = validate_page_content(Pet("Ada"))
        assert not is_valid
        assert "Pet" in message

    def test_validate_rejects_bad_item_in_list(self):
        is_valid, message = validate_page_content([1, Pet("Ada")])
        assert not is_valid
        assert "index 1" in message

    @pytest.mark.parametrize("value", [42, 3.14, True])
    def test_normalize_wraps_plain_values(self, value):
        assert normalize_page_content(value) == [value]


class TestVerifyPipeline:
    def test_page_verify_accepts_primitives(self):
        page = Page(None, ["Score:", 42, 3.14, True])
        assert page.verify(None, None, None, FAKE_REQUEST) is None

    def test_page_verify_rejects_bad_item(self):
        page = Page(None, ["ok"])
        page.content.append(Pet("Ada"))
        failure = page.verify(None, None, None, FAKE_REQUEST)
        assert failure is not None
        assert "Pet" in failure.message


class TestRendering:
    def test_primitives_render_as_text(self):
        rendered = render(Page(None, [42, 3.14, True]).content).flatten()
        assert "42" in rendered
        assert "3.14" in rendered
        assert "True" in rendered

    def test_primitives_render_nested_in_components(self):
        rendered = render(Div(42, True)).flatten()
        assert "42" in rendered
        assert "True" in rendered

    def test_primitives_render_in_lists(self):
        rendered = render(BulletedList([1, 2.5, False])).flatten()
        assert "<li>" in rendered
        assert "1" in rendered
        assert "2.5" in rendered
        assert "False" in rendered

    def test_full_page_render_with_components(self):
        page = Page(None, ["Score:", 42, Button("Play", "index")])
        rendered = page.render(None, None)
        assert "Score:" in rendered
        assert "42" in rendered


class TestTextAndStyling:
    def test_text_stringifies_plain_body(self):
        assert Text(42).body == "42"
        assert Text(True).body == "True"

    def test_text_equality_with_plain_values(self):
        assert Text(5) == 5
        assert Text(5) == "5"
        assert Text("5") == 5

    def test_styling_helper_wraps_plain_value(self):
        result = bold(42)
        assert isinstance(result, Text)
        assert result.body == "42"
