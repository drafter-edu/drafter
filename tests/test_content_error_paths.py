"""Student-friendly errors for failures inside nested page content.

Covers the structured render path (`drafter.data.paths`), the
type-targeted `StudentFacingError` raised for unsupported content values,
the semantic labels components attach to their generated structure
(Table rows/columns, list items), friendly-tier preservation when a
component's `plan()` raises, and the curated explainer entries for
`payload.rendering_failed`.
"""

import pytest

from drafter import BulletedList, Div, Table
from drafter.components.page_content import Component
from drafter.data.error_explainer import explain
from drafter.data.errors import StudentFacingError
from drafter.data.paths import (
    PathItem,
    render_debug_path,
    render_path,
    render_student_path,
)
from drafter.payloads.renderer import RenderError, render


class TestStudentPathPhrasing:
    def test_index_then_component_merges(self):
        path = [PathItem("index", "1"), PathItem("component", "Table")]
        assert render_student_path(path) == "the Table at index 1"

    def test_labels_and_internal_frames(self):
        path = [
            PathItem("index", "1"),
            PathItem("component", "Table"),
            PathItem("tag", "table"),
            PathItem("child", "1"),
            PathItem("tag", "tbody"),
            PathItem("child", "0"),
            PathItem("label", "row index 0"),
            PathItem("child", "1"),
            PathItem("label", "column index 1"),
            PathItem("child", "0"),
        ]
        assert (
            render_student_path(path)
            == "the Table at index 1, row index 0, column index 1"
        )

    def test_trailing_index_is_kept(self):
        path = [PathItem("index", "0"), PathItem("index", "2")]
        assert render_student_path(path) == "the item at index 0, the item at index 2"

    def test_empty_path(self):
        assert render_student_path([]) == ""

    def test_debug_path_shows_everything(self):
        path = [
            PathItem("index", "1"),
            PathItem("component", "Table"),
            PathItem("tag", "table"),
            PathItem("child", "0"),
        ]
        assert render_debug_path(path) == "[1] > Table > table > [0]"

    def test_comparison_render_path_unchanged(self):
        # The testing assertions' phrasing must survive the module move.
        path = [
            PathItem("attributes", "Table"),
            PathItem("key", "rows"),
            PathItem("index", "0"),
        ]
        assert render_path(path) == "Table rows index '0'"


class TestUnsupportedContentErrors:
    def test_dict_in_table_cell_names_row_and_column(self):
        content = ["Header", Table([["ok", {"bad": 1}]])]
        with pytest.raises(StudentFacingError) as excinfo:
            render(content)
        error = excinfo.value
        assert error.friendly_title == "Page Content Problem"
        assert (
            "the Table at index 1, row index 0, column index 1"
            in error.friendly_message
        )
        assert "dictionary" in error.friendly_message
        assert any("Table" in step or "str(" in step for step in error.friendly_steps)
        # Technical message keeps the full internal path for debugging.
        assert "tbody" in str(error)
        assert "Unsupported page content type dict" in str(error)

    def test_tuple_in_bulleted_list_names_item(self):
        content = [BulletedList(["ok", ("bad", "tuple")])]
        with pytest.raises(StudentFacingError) as excinfo:
            render(content)
        error = excinfo.value
        assert "the BulletedList at index 0, item index 1" in error.friendly_message
        assert any("list" in step for step in error.friendly_steps)

    def test_none_suggests_missing_return(self):
        with pytest.raises(StudentFacingError) as excinfo:
            render([None])
        error = excinfo.value
        assert "the item at index 0" in error.friendly_message
        assert "None" in error.friendly_message
        assert any("return" in step for step in error.friendly_steps)

    def test_function_suggests_link(self):
        def my_route():
            pass

        with pytest.raises(StudentFacingError) as excinfo:
            render([Div("ok"), my_route])
        error = excinfo.value
        assert "the function 'my_route'" in error.friendly_message
        assert "the item at index 1" in error.friendly_message
        assert any("Link" in step for step in error.friendly_steps)

    def test_class_suggests_parentheses(self):
        class Pet:
            pass

        with pytest.raises(StudentFacingError) as excinfo:
            render([Pet])
        error = excinfo.value
        assert "the class 'Pet'" in error.friendly_message
        assert any("parentheses" in step for step in error.friendly_steps)

    def test_div_content_index(self):
        with pytest.raises(StudentFacingError) as excinfo:
            render([Div("a", {"bad": 1})])
        error = excinfo.value
        assert "the Div at index 0, the item at index 1" in error.friendly_message

    def test_nested_plain_list_adds_inner_index(self):
        # A list passed as one content argument is one item deeper.
        with pytest.raises(StudentFacingError) as excinfo:
            render([Div(["a", {"bad": 1}])])
        error = excinfo.value
        assert (
            "the Div at index 0, the item at index 0, the item at index 1"
            in error.friendly_message
        )


class TestPlanFailureFriendlyPreservation:
    class Exploding(Component):
        tag = "div"

        def __init__(self):
            self.extra_settings = {}

        def plan(self, context):
            raise StudentFacingError(
                "boom",
                friendly="The gizmo was not configured.",
                steps=("Configure the gizmo.",),
                title="Gizmo Problem",
            )

    def test_friendly_tier_survives_render_error_wrap(self):
        with pytest.raises(RenderError) as excinfo:
            render([self.Exploding()])
        error = excinfo.value
        assert error.friendly_title == "Gizmo Problem"
        assert "The gizmo was not configured." in error.friendly_message
        assert (
            "This happened while showing the Exploding at index 0."
            in error.friendly_message
        )
        assert error.friendly_steps == ("Configure the gizmo.",)
        assert isinstance(error.__cause__, StudentFacingError)

    def test_plain_exception_wrap_has_no_friendly_tier(self):
        class Broken(Component):
            tag = "div"

            def __init__(self):
                self.extra_settings = {}

            def plan(self, context):
                raise ValueError("internal")

        with pytest.raises(RenderError) as excinfo:
            render([Broken()])
        error = excinfo.value
        assert not hasattr(error, "friendly_message")


class TestExplainerEntries:
    def test_rendering_failed_id_has_curated_entry(self):
        explanation = explain(None, "payload.rendering_failed", "payload")
        assert explanation.title == "Page Content Problem"
        assert "could not turn the content" in explanation.message

    def test_carried_friendly_text_beats_id_entry(self):
        error = StudentFacingError(
            "boom",
            friendly="Carried explanation.",
            steps=("Carried step.",),
            title="Carried Title",
        )
        explanation = explain(error, "payload.rendering_failed", "payload")
        assert explanation.title == "Carried Title"
        assert explanation.message == "Carried explanation."


class TestRenderingStillWorks:
    def test_successful_render_unchanged_and_stack_balanced(self):
        renderer = render(["a", Table([["x", "y"]], header=["A", "B"])])
        html = renderer.flatten()
        assert "<td>" in html
        assert "<th>" in html
        assert renderer.component_stack == []

    def test_lists_and_tables_render_content(self):
        renderer = render([BulletedList(["one", "two"]), Div("inner")])
        html = renderer.flatten()
        assert "one" in html and "two" in html and "inner" in html
        assert renderer.component_stack == []
