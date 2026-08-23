"""Tests for the central student-friendly error explainer."""

import sys
from unittest.mock import MagicMock

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.data.error_explainer import (
    CATEGORY_EXPLANATIONS,
    GENERIC_MESSAGE,
    GENERIC_STEPS,
    GENERIC_TITLE,
    diagnostics_to_friendly,
    explain,
)
from drafter.data.errors import StudentFacingError
from drafter.router.parameters.diagnostics import (
    ParameterBindingError,
    RouteDiagnostic,
)

# ============================================================================
# EXCEPTION-TYPE TABLE
# ============================================================================


class TestExceptionTypeExplanations:
    def test_name_error_mentions_the_name(self):
        explanation = explain(
            NameError("name 'total' is not defined", name="total"),
            "request.route_execution_failed",
            "request",
        )
        assert explanation.title == "Unknown Name"
        assert "'total'" in explanation.message
        assert any("misspelled" in step for step in explanation.steps)

    def test_key_error_mentions_the_key(self):
        explanation = explain(
            KeyError("score"), "request.route_execution_failed", "request"
        )
        assert explanation.title == "Missing Dictionary Key"
        assert "'score'" in explanation.message
        assert any("dictionary" in step for step in explanation.steps)

    def test_subclass_falls_back_to_nearest_base(self):
        # UnboundLocalError has no entry; it should use the NameError entry.
        explanation = explain(
            UnboundLocalError("local variable 'x' referenced before assignment"),
            "request.route_execution_failed",
            "request",
        )
        assert "name" in explanation.message.lower()

    def test_more_derived_entry_wins_over_base(self):
        # IndentationError is a SyntaxError subclass with its own entry.
        explanation = explain(
            IndentationError("unexpected indent"),
            "runtime.student_code_failed",
            "runtime",
        )
        assert explanation.title == "Indentation Problem"
        assert "indentation" in explanation.message.lower()
        assert any("tabs" in step for step in explanation.steps)

    def test_module_not_found_uses_import_entry_with_name(self):
        explanation = explain(
            ModuleNotFoundError("No module named 'numppy'", name="numppy"),
            "request.route_execution_failed",
            "request",
        )
        assert "'numppy'" in explanation.message

    def test_zero_division(self):
        explanation = explain(
            ZeroDivisionError("division by zero"),
            "request.route_execution_failed",
            "request",
        )
        assert explanation.title == "Division by Zero"
        assert "zero" in explanation.message
        assert explanation.steps


# ============================================================================
# ID AND CATEGORY TABLES
# ============================================================================


class TestIdAndCategoryExplanations:
    def test_route_not_found_without_exception(self):
        explanation = explain(None, "request.route_not_found", "request")
        assert explanation.title == "Page Not Found"
        assert "could not find the page route" in explanation.message
        assert any("Return to Index Page" in step for step in explanation.steps)

    def test_id_entry_wins_over_misleading_internal_exception(self):
        # A route lookup failing internally with KeyError must not produce
        # dictionary advice; the id describes the real, student-level cause.
        explanation = explain(
            KeyError("missing_page"), "request.route_not_found", "request"
        )
        assert explanation.title == "Page Not Found"
        assert "could not find the page route" in explanation.message
        assert not any("dictionary" in step for step in explanation.steps)

    def test_category_entry_with_generic_steps(self):
        class UnknownError(Exception):
            pass

        explanation = explain(
            UnknownError("odd"), "payload.uncurated_failure", "payload"
        )
        assert explanation.title == CATEGORY_EXPLANATIONS["payload"][0]
        assert explanation.message == CATEGORY_EXPLANATIONS["payload"][1]
        assert explanation.steps == GENERIC_STEPS

    def test_full_fallback(self):
        explanation = explain(None, "system.unheard_of", "system")
        assert explanation.title == GENERIC_TITLE
        assert explanation.message == GENERIC_MESSAGE
        assert explanation.steps == GENERIC_STEPS


# ============================================================================
# CARRIED FRIENDLY TEXT (rule 1)
# ============================================================================


class TestCarriedFriendlyText:
    def test_student_facing_error_wins_over_type_table(self):
        error = StudentFacingError(
            "technical",
            friendly="Friendly words.",
            steps=("Do the thing.",),
            title="Custom Title",
        )
        explanation = explain(error, "request.route_execution_failed", "request")
        assert explanation.title == "Custom Title"
        assert explanation.message == "Friendly words."
        assert explanation.steps == ("Do the thing.",)

    def test_partial_carried_text_resolves_independently(self):
        # Only a friendly message: the title and steps should still come
        # from the ValueError type entry, not collapse to generic.
        error = StudentFacingError("technical", friendly="Just a message.")
        explanation = explain(error, "request.route_execution_failed", "request")
        assert explanation.title == "Unusable Value"
        assert explanation.message == "Just a message."
        assert any("failing line" in step for step in explanation.steps)


# ============================================================================
# DIAGNOSTICS (rule 2)
# ============================================================================


def _diagnostic(**overrides) -> RouteDiagnostic:
    values = dict(
        severity="error",
        code="conversion_failed",
        route_name="add_item",
        message="The value 'abc' for 'count' could not be converted to int.",
        parameter="count",
        source="form_field",
        hint="Make sure the field contains a whole number.",
    )
    values.update(overrides)
    return RouteDiagnostic(**values)


class TestDiagnosticsExplanations:
    def test_parameter_binding_error_maps_each_diagnostic_to_a_step(self):
        error = ParameterBindingError(
            [
                _diagnostic(),
                _diagnostic(
                    parameter="name",
                    message="Missing required parameter 'name'.",
                    hint="Add a form field named 'name'.",
                ),
            ]
        )
        explanation = explain(error, "request.argument_parsing_failed", "request")
        # The id table supplies the title; the diagnostics supply the rest.
        assert explanation.title == "Problem With the Route's Arguments"
        assert "'add_item'" in explanation.message
        assert len(explanation.steps) == 2
        assert explanation.steps[0].endswith(
            "Make sure the field contains a whole number."
        )
        assert explanation.steps[1] == (
            "Missing required parameter 'name'. Add a form field named 'name'."
        )

    def test_diagnostics_without_hints(self):
        message, steps = diagnostics_to_friendly([_diagnostic(hint="", route_name="")])
        assert "route function" in message
        assert steps == ("The value 'abc' for 'count' could not be converted to int.",)

    def test_empty_diagnostics_do_not_explain(self):
        assert diagnostics_to_friendly([]) == ("", ())
