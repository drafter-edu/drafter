# Telemetry fixtures

One JSON fixture per `TypedRecord` subtype (see `js/src/debug/telemetry.ts`),
shaped like the payloads the Python side actually emits. Every record's
`metadata`/`correlation` shape mirrors `TelemetryMetadata.to_json()` and
`Correlation.to_json()` in `src/drafter/data/telemetry.py` /
`src/drafter/data/correlation.py`, as filled in by `log_record()` in
`src/drafter/monitor/audit.py` (which always sets `level: "info"` and passes
no `phase`, so `phase` is `null`). The `version` value is
`CURRENT_DRAFTER_VERSION` from `src/drafter/version.py` and timestamps are
`datetime.isoformat()` strings.

Where each payload body was derived from:

| Fixture | Python source of the shape |
|---------|----------------------------|
| `route-added.json` | `RouteAddedEvent.to_json()` in `src/drafter/data/details/routes.py`; emitted by `ClientServer.add_route` with source `"client_server.add_route"` |
| `request-event.json` | `RequestEvent.from_request()/to_json()` in `src/drafter/data/details/request.py`; emitted by `ClientServer.visit` with source `"client_server.visit"` (`kwargs`/`event` are Python `str(dict)` renderings) |
| `request-parse-event.json` | `RequestParseEvent.to_json()` in `src/drafter/data/details/request.py`; emitted by `ClientServer.execute_route` with source `"client_server.execute_route"` |
| `response-event.json` | `ResponseEvent.from_response()/to_json()` in `src/drafter/data/details/request.py`; emitted by `ClientServer.visit` with source `"client_server.visit"` |
| `page-visit-event.json` | **Legacy/dead kind.** No Python emitter exists for `PageVisitEvent` (grep of `src/` finds none), so the interface was removed from the TS union; the fixture is kept to exercise the unknown-kind fallback path in `DebugPanel.handleEvent` |
| `test-case-event.json` / `test-case-event-failed.json` | `TestCaseEvent.to_json()` in `src/drafter/data/details/tests.py`; emitted by `BakeryTests._emit_test_event` in `src/drafter/testing/testing.py` with source `"testing.track_bakery_tests"`; `diff_html` is a `difflib.unified_diff` string with the `"Test Expected"` / `"Actually Returned"` file labels |
| `initial-configuration.json` | `InitialConfigurationEvent.to_json()` in `src/drafter/data/details/config.py`; `config` is `ClientServerConfiguration.to_json()` from `src/drafter/config/client_server.py` (default values); emitted by `ClientServer.do_configuration` with source `"client_server.do_configuration"` |
| `updated-configuration.json` | `UpdatedConfigurationEvent.to_json()` in `src/drafter/data/details/config.py`; emitted by `ClientServer.reconfigure` with source `"client_server.reconfigure"` |
| `updated-state.json` | `UpdatedStateEvent.to_json()` in `src/drafter/data/details/state.py`; `representation` follows `RecursiveTypeDescriber` output in `src/drafter/data/details/recursive_type_describer.py` (a dataclass with `str`/`int` primitives and a homogenous `list[str]`, exactly the dict shapes `_visit_class_instance`, `_visit_primitive`, and `_visit_linear_collection` build); emitted by `ClientServer.handle_state_updates` with source `"client_server.handle_state_updates"` |
| `error-record.json` | `ErrorRecord.to_json()` in `src/drafter/data/telemetry.py` with `ErrorDetails.to_json()` from `src/drafter/data/errors.py`; the record's `kind` is the error's stable id |

Note: Python's `ErrorDetails.to_json()["context"]` is a full
`Correlation.to_json()` (including `causation_id` and `phase`), and the TS
`ErrorDetailsJson["context"]` type declares the same fields.
