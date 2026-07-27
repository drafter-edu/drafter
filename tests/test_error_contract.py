"""Tests for the canonical error contract in drafter.data.errors."""

import sys
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.data.correlation import Correlation
from drafter.data.errors import (
    CATEGORY_BRIDGE,
    CATEGORY_PAYLOAD,
    CATEGORY_REQUEST,
    CATEGORY_SYSTEM,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    STATUS_BAD_REQUEST,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_OK,
    STATUSES,
    ErrorDetails,
    envelope_from_exception,
)
from drafter.monitor.audit import log_error

# ============================================================================
# STATUS CODES
# ============================================================================


class TestStatusCodes:
    def test_status_set_is_stable(self):
        assert STATUSES == (
            STATUS_OK,
            STATUS_BAD_REQUEST,
            STATUS_NOT_FOUND,
            STATUS_ERROR,
        )

    def test_status_values(self):
        assert STATUS_OK == "ok"
        assert STATUS_BAD_REQUEST == "bad_request"
        assert STATUS_NOT_FOUND == "not_found"
        assert STATUS_ERROR == "error"

    def test_envelope_rejects_unknown_status(self):
        with pytest.raises(ValueError):
            ErrorDetails(
                id="x",
                category=CATEGORY_SYSTEM,
                message="m",
                status_code="teapot",
            )

    def test_envelope_defaults_status_to_error(self):
        envelope = ErrorDetails(id="x", category=CATEGORY_SYSTEM, message="m")
        assert envelope.status_code == STATUS_ERROR

    def test_envelope_accepts_each_known_status(self):
        for status in STATUSES:
            envelope = ErrorDetails(
                id="x",
                category=CATEGORY_SYSTEM,
                message="m",
                status_code=status,
            )
            assert envelope.status_code == status


# ============================================================================
# ENVELOPE
# ============================================================================


class TestErrorEnvelope:
    def test_defaults(self):
        envelope = ErrorDetails(
            id="request.route_not_found",
            category=CATEGORY_REQUEST,
            message="No route found",
        )
        assert envelope.severity == "error"
        assert envelope.status_code == STATUS_ERROR
        assert envelope.recoverable is True
        assert envelope.context.route is None

    def test_rejects_unknown_category(self):
        with pytest.raises(ValueError):
            ErrorDetails(id="x", category="bogus", message="m")

    def test_rejects_unknown_severity(self):
        with pytest.raises(ValueError):
            ErrorDetails(
                id="x", category=CATEGORY_SYSTEM, message="m", severity="fatal"
            )

    def test_to_json_shape(self):
        envelope = ErrorDetails(
            id="bridge.setup_failed",
            category=CATEGORY_BRIDGE,
            message="Setup failed",
            details="stack details",
            context=Correlation(route="index", request_id=3, phase="setup"),
            status_code=STATUS_ERROR,
            recoverable=False,
        )
        data = envelope.to_json()
        assert data == {
            "id": "bridge.setup_failed",
            "category": "bridge",
            "severity": "error",
            "message": "Setup failed",
            "details": "stack details",
            "data": {},
            "friendly_title": "",
            "friendly_message": "",
            "friendly_steps": [],
            "traceback": None,
            "context": {
                "causation_id": None,
                "route": "index",
                "request_id": 3,
                "response_id": None,
                "dom_id": None,
                "phase": "setup",
            },
            "status_code": STATUS_ERROR,
            "recoverable": False,
        }


# ============================================================================
# STRUCTURED DATA
# ============================================================================


class TestStructuredData:
    def test_data_defaults_to_empty_dict(self):
        envelope = ErrorDetails(id="x", category=CATEGORY_SYSTEM, message="m")
        assert envelope.data == {}
        assert envelope.to_json()["data"] == {}

    def test_data_is_sanitized_on_construction(self):
        class Odd:
            def __repr__(self):
                return "<odd thing>"

        envelope = ErrorDetails(
            id="x",
            category=CATEGORY_SYSTEM,
            message="m",
            data={"nested": {"values": [1, "two", Odd()]}, "flag": True},
        )
        assert envelope.data == {
            "nested": {"values": [1, "two", "<odd thing>"]},
            "flag": True,
        }

    def test_data_converts_objects_with_to_json(self):
        from drafter.data.request import Request

        request = Request("click", "guess", {"pick": "5"}, {})
        envelope = ErrorDetails(
            id="x",
            category=CATEGORY_SYSTEM,
            message="m",
            data={"request": request},
        )
        described = envelope.data["request"]
        assert described["url"] == "guess"
        assert described["kwargs"] == {"pick": "5"}

    def test_data_converts_dataclasses(self):
        from dataclasses import dataclass as plain_dataclass

        @plain_dataclass
        class State:
            score: int
            name: str

        envelope = ErrorDetails(
            id="x",
            category=CATEGORY_SYSTEM,
            message="m",
            data={"updated_state": State(score=3, name="Ada")},
        )
        assert envelope.data["updated_state"] == {"score": 3, "name": "Ada"}


# ============================================================================
# FRIENDLY TIER
# ============================================================================


class TestFriendlyTier:
    def test_defaults_to_empty(self):
        envelope = ErrorDetails(id="x", category=CATEGORY_SYSTEM, message="m")
        assert envelope.friendly_message == ""
        assert envelope.friendly_steps == ()

    def test_steps_coerced_to_tuple(self):
        envelope = ErrorDetails(
            id="x",
            category=CATEGORY_SYSTEM,
            message="m",
            friendly_steps=["one", "two"],
        )
        assert envelope.friendly_steps == ("one", "two")
        assert envelope.to_json()["friendly_steps"] == ["one", "two"]

    def test_envelope_from_exception_derives_friendly_text(self):
        envelope = envelope_from_exception(
            NameError("name 'total' is not defined", name="total"),
            "request.route_execution_failed",
            CATEGORY_REQUEST,
        )
        assert envelope.friendly_title == "Unknown Name"
        assert "'total'" in envelope.friendly_message
        assert envelope.friendly_steps
        assert any("misspelled" in step for step in envelope.friendly_steps)

    def test_envelope_from_exception_explicit_friendly_text_wins(self):
        envelope = envelope_from_exception(
            NameError("nope"),
            "request.route_execution_failed",
            CATEGORY_REQUEST,
            friendly_message="Custom explanation.",
            friendly_steps=("Custom step.",),
        )
        assert envelope.friendly_message == "Custom explanation."
        assert envelope.friendly_steps == ("Custom step.",)

    def test_student_facing_error_carries_friendly_text(self):
        from drafter.data.errors import StudentFacingError

        error = StudentFacingError(
            "Header level must be between 1 and 6, not 9",
            friendly="The Header component only supports levels 1 through 6.",
            steps=["Change the level argument to a number from 1 to 6."],
        )
        assert str(error) == "Header level must be between 1 and 6, not 9"
        envelope = envelope_from_exception(
            error, "request.route_execution_failed", CATEGORY_REQUEST
        )
        assert (
            envelope.friendly_message
            == "The Header component only supports levels 1 through 6."
        )
        assert envelope.friendly_steps == (
            "Change the level argument to a number from 1 to 6.",
        )


# ============================================================================
# CONVERSION HELPERS
# ============================================================================


class TestConversions:
    def test_envelope_from_exception(self):
        try:
            raise ValueError("bad input")
        except ValueError as e:
            envelope = envelope_from_exception(
                e,
                "request.argument_parsing_failed",
                CATEGORY_REQUEST,
                details="while parsing",
            )
        assert envelope.message == "bad input"
        assert envelope.category == CATEGORY_REQUEST
        assert envelope.details == "while parsing"
        assert envelope.traceback and "ValueError" in envelope.traceback
        assert envelope.status_code == STATUS_ERROR

    def test_envelope_from_exception_custom_message(self):
        envelope = envelope_from_exception(
            RuntimeError("internal"),
            "system.response_creation_failed",
            CATEGORY_SYSTEM,
            message="Something went wrong",
        )
        assert envelope.message == "Something went wrong"

    def test_envelope_supports_non_default_severities(self):
        warning = ErrorDetails(
            id="x.warning",
            category=CATEGORY_SYSTEM,
            message="hmm",
            severity=SEVERITY_WARNING,
        )
        info = ErrorDetails(
            id="x.info",
            category=CATEGORY_SYSTEM,
            message="fyi",
            severity=SEVERITY_INFO,
        )
        assert warning.severity == "warning"
        assert info.severity == "info"


# ============================================================================
# SERVER INTEGRATION (raised ErrorEnvelope)
# ============================================================================


class TestRaisedEnvelope:
    def test_envelope_is_raisable(self):
        envelope = ErrorDetails(
            id="request.route_not_found",
            category=CATEGORY_REQUEST,
            message="not found",
            status_code=STATUS_NOT_FOUND,
        )
        with pytest.raises(ErrorDetails) as exc_info:
            raise envelope
        assert exc_info.value is envelope


# ============================================================================
# BRIDGE INTEGRATION
# ============================================================================


class TestBridgeEnvelope:
    def test_bridge_category_is_supported(self):
        envelope = ErrorDetails(
            id="bridge.channel_execution_failed",
            category=CATEGORY_BRIDGE,
            message="channel failed",
            status_code=STATUS_ERROR,
            context=Correlation(
                request_id=7, dom_id="btn-1", phase="channel_execution"
            ),
        )
        assert envelope.category == CATEGORY_BRIDGE
        assert envelope.status_code == STATUS_ERROR


# ============================================================================
# PHASE 2: SERVER LIFECYCLE
# ============================================================================


@pytest.fixture
def started_server():
    from drafter.client_server.client_server import ClientServer

    server = ClientServer("test_server")
    server.do_configuration()
    server.do_start()
    return server


class TestVisitLifecycle:
    """Every raised ErrorEnvelope path emits canonical telemetry and response errors."""

    def _visit(self, server, url, handler=None, kwargs=None):
        from drafter.data.request import Request

        if handler is not None:
            server.add_route(url, handler)
        request = Request("click", url, kwargs or {}, {}, "")
        return request, server.do_visit(request)

    def test_route_not_found_envelope(self, started_server):
        request, response = self._visit(started_server, "nonexistent")
        assert response.status_code == STATUS_NOT_FOUND
        envelope = response.errors[0]
        assert envelope.id == "request.route_not_found"
        assert envelope.category == CATEGORY_REQUEST
        assert envelope.status_code == STATUS_NOT_FOUND
        assert envelope.context.request_id == request.id
        assert envelope.context.route == "nonexistent"
        assert envelope.context.phase == "visit"

    def test_route_execution_failed_envelope(self, started_server):
        def failing_handler():
            raise ValueError("boom")

        request, response = self._visit(started_server, "fail", failing_handler)
        assert response.status_code == STATUS_ERROR
        envelope = response.errors[0]
        assert envelope.id == "request.route_execution_failed"
        assert envelope.category == CATEGORY_REQUEST
        assert envelope.traceback and "ValueError" in envelope.traceback

    def test_invalid_payload_envelope(self, started_server):
        def invalid_handler():
            return "not a payload"

        request, response = self._visit(started_server, "invalid", invalid_handler)
        assert response.status_code == STATUS_ERROR
        envelope = response.errors[0]
        assert envelope.id == "payload.verification_failed"
        assert envelope.category == CATEGORY_PAYLOAD
        assert envelope.status_code == STATUS_ERROR

    def test_bad_link_keeps_friendly_text_and_traceback(self, started_server):
        from drafter.components.links import Link
        from drafter.payloads.kinds.page import Page

        def bad_link_handler():
            return Page(None, [Link("Next", "missing_page")])

        request, response = self._visit(started_server, "bad_link", bad_link_handler)
        assert response.status_code == STATUS_ERROR
        envelope = response.errors[0]
        assert envelope.id == "payload.verification_failed"
        assert envelope.category == CATEGORY_PAYLOAD
        # The link-specific StudentFacingError explanation survives, rather
        # than falling back to generic payload-category guidance.
        assert "missing_page" in envelope.friendly_message
        assert any("@route" in step for step in envelope.friendly_steps)
        assert envelope.traceback and "StudentFacingError" in envelope.traceback

    def test_duplicate_names_keep_friendly_text_without_traceback_advice(
        self, started_server
    ):
        from drafter.components.forms import TextBox
        from drafter.payloads.kinds.page import Page

        def duplicate_handler():
            return Page(None, [TextBox("answer"), TextBox("answer")])

        request, response = self._visit(
            started_server, "duplicates", duplicate_handler
        )
        assert response.status_code == STATUS_ERROR
        envelope = response.errors[0]
        assert envelope.id == "payload.verification_failed"
        # The tailored duplicate-name explanation survives instead of the
        # generic payload-category guidance.
        assert "answer" in envelope.friendly_message
        assert any("unique name" in step for step in envelope.friendly_steps)
        # No exception was involved, so there is no traceback — and the
        # steps must not tell the student to go read one.
        assert envelope.traceback is None
        assert not any("traceback" in step.lower() for step in envelope.friendly_steps)

    def test_returning_none_keeps_friendly_text_without_traceback_advice(
        self, started_server
    ):
        def none_handler():
            return None

        request, response = self._visit(started_server, "forgot_return", none_handler)
        assert response.status_code == STATUS_ERROR
        envelope = response.errors[0]
        assert envelope.id == "payload.verification_failed"
        assert "returning a Page" in envelope.friendly_message
        assert any("return" in step for step in envelope.friendly_steps)
        assert envelope.traceback is None
        assert not any("traceback" in step.lower() for step in envelope.friendly_steps)

    def test_route_not_found_carries_request_data_but_no_call(self, started_server):
        request, response = self._visit(started_server, "nowhere")
        envelope = response.errors[0]
        assert "route_call" not in envelope.data
        assert envelope.data["request"]["url"] == "nowhere"
        assert envelope.data["request"]["id"] == request.id

    def test_route_execution_failure_carries_exact_route_call(self, started_server):
        def guess(pick: int):
            raise ValueError("boom")

        request, response = self._visit(started_server, "guess", guess, {"pick": "5"})
        envelope = response.errors[0]
        assert envelope.id == "request.route_execution_failed"
        assert envelope.data["route_call_exact"] is True
        assert envelope.data["route_call"].startswith("guess(")
        assert "5" in envelope.data["route_call"]
        assert envelope.data["request"]["kwargs"] == {"pick": "5"}

    def test_argument_parsing_failure_carries_approximate_route_call(
        self, started_server
    ):
        def typed(pick: int):
            return None

        request, response = self._visit(
            started_server,
            "typed",
            typed,
            {"pick": "abc", "--submit-button": "typed_btn"},
        )
        envelope = response.errors[0]
        assert envelope.id == "request.argument_parsing_failed"
        assert envelope.data["route_call_exact"] is False
        assert envelope.data["route_call"].startswith("typed(")
        assert "abc" in envelope.data["route_call"]
        # Framework bookkeeping entries never appear in the generated call.
        assert "--submit-button" not in envelope.data["route_call"]

    def test_make_error_response_uses_given_envelope(self, started_server):
        """Direct calls carry the provided envelope through to response errors."""
        from drafter.data.request import Request

        request = Request("click", "somewhere", {}, {}, "")
        error = ErrorDetails(
            id="system.explicit_error",
            category=CATEGORY_SYSTEM,
            message="plain envelope error",
            status_code=STATUS_ERROR,
            context=Correlation(
                route="somewhere", request_id=request.id, phase="visit"
            ),
        )
        response = started_server.make_error_response(request, error)
        envelope = response.errors[0]
        assert envelope.id == "system.explicit_error"
        assert envelope.context.request_id == request.id


class TestRequestScopedWarnings:
    """Warnings generated during a visit appear in telemetry and response."""

    def test_request_scoped_warning_attached_to_response(self, started_server):
        from drafter.data.details.request import ResponseEvent
        from drafter.data.request import Request
        from drafter.payloads.kinds.page import Page

        request = Request("click", "warned", {}, {}, "")

        def warned_handler():
            log_error(
                ErrorDetails(
                    id="test.request_scoped_warning",
                    category=CATEGORY_REQUEST,
                    message="Something non-fatal happened",
                    severity=SEVERITY_WARNING,
                    details="details",
                    context=Correlation(request_id=request.id),
                ),
                "tests.warned_handler",
            )
            return Page(None, ["ok"])

        started_server.add_route("warned", warned_handler)
        response = started_server.do_visit(request)

        assert response.status_code == STATUS_OK
        assert len(response.warnings) == 1
        assert response.warnings[0].message == "Something non-fatal happened"
        event = ResponseEvent.from_response(response, "", 0.0)
        assert event.has_warnings is True
        assert event.has_errors is False

    def test_unrelated_warning_not_attached(self, started_server):
        from drafter.data.request import Request
        from drafter.payloads.kinds.page import Page

        def handler():
            # Warning correlated with a different request id.
            log_error(
                ErrorDetails(
                    id="test.unrelated_warning",
                    category=CATEGORY_REQUEST,
                    message="Not for this request",
                    severity=SEVERITY_WARNING,
                    details="details",
                    context=Correlation(request_id=999999),
                ),
                "tests.handler",
            )
            return Page(None, ["ok"])

        started_server.add_route("quiet", handler)
        request = Request("click", "quiet", {}, {}, "")
        response = started_server.do_visit(request)

        assert response.warnings == []

    def test_warning_attached_to_error_response(self, started_server):
        from drafter.data.request import Request

        request = Request("click", "warn_then_fail", {}, {}, "")

        def handler():
            log_error(
                ErrorDetails(
                    id="test.warning_before_failure",
                    category=CATEGORY_REQUEST,
                    message="Warned before failing",
                    severity=SEVERITY_WARNING,
                    details="details",
                    context=Correlation(request_id=request.id),
                ),
                "tests.handler",
            )
            raise ValueError("boom")

        started_server.add_route("warn_then_fail", handler)
        response = started_server.do_visit(request)

        assert response.status_code == STATUS_ERROR
        assert len(response.errors) == 1
        assert len(response.warnings) == 1

    def test_warning_subscription_cleaned_up(self, started_server):
        from drafter.client_server.commands import get_main_event_bus
        from drafter.data.request import Request
        from drafter.payloads.kinds.page import Page

        bus = get_main_event_bus()
        before = len(bus.subscribers)
        started_server.add_route("plain", lambda: Page(None, ["ok"]))
        started_server.do_visit(Request("click", "plain", {}, {}, ""))
        assert len(bus.subscribers) == before


class TestCanonicalTelemetry:
    """Telemetry events for visit failures carry the envelope."""

    def test_visit_failure_telemetry_includes_envelope(self, started_server):
        from drafter.client_server.commands import get_main_event_bus
        from drafter.data.request import Request

        captured = []
        subscription = get_main_event_bus().subscribe(
            "request.route_not_found", lambda event: captured.append(event)
        )
        try:
            started_server.do_visit(Request("click", "missing", {}, {}, ""))
        finally:
            get_main_event_bus().unsubscribe(subscription)

        assert len(captured) == 1
        event = captured[0]
        assert event.metadata.level == "error"
        assert event.error is not None
        assert event.error.id == "request.route_not_found"
        data_json = event.error.to_json()
        assert data_json["category"] == "request"
        assert data_json["status_code"] == STATUS_NOT_FOUND


class TestEnvelopeLogging:
    """Canonical envelope logging emits ErrorRecord payloads."""

    def test_log_error_emits_error_record(self, started_server):
        from drafter.client_server.commands import get_main_event_bus

        captured = []
        subscription = get_main_event_bus().subscribe(
            "site.processing_failed", lambda event: captured.append(event)
        )
        try:
            result = log_error(
                ErrorDetails(
                    id="site.processing_failed",
                    category=CATEGORY_SYSTEM,
                    message="Something failed",
                    details="details",
                ),
                "tests.envelope",
            )
        finally:
            get_main_event_bus().unsubscribe(subscription)

        assert isinstance(result, ErrorDetails)
        assert result.id == "site.processing_failed"
        assert result.category == CATEGORY_SYSTEM
        assert len(captured) == 1
        assert captured[0].kind == "site.processing_failed"
        assert captured[0].metadata.level == "error"
        assert captured[0].metadata.source == "tests.envelope"
        assert captured[0].error.category == CATEGORY_SYSTEM
