/**
 * Unit tests for the telemetry adapter path: Python-shaped telemetry
 * payloads (fixtures in fixtures/telemetry/, see the README there for how
 * each shape was derived) fed through DebugPanel.handleEvent — the actual
 * dispatch switch that adapts each TypedRecord kind into panel renders.
 *
 * No Pyodide involved: the Python bridge (_handle_debug_events in
 * src/drafter/bridge/client_bridge.py) converts each record to a plain JS
 * object and calls debug_panel.handleEvent(event), which is exactly what
 * these tests do with the fixtures.
 */
import {
	afterAll,
	afterEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import { DebugPanel } from "../debug/index";
import { setSystemErrorSink } from "../bridge/engine";
import type { TelemetryRecord } from "../debug/telemetry";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { RouteAddedEvent } from "../debug/telemetry/routes";
import type {
	RequestEvent,
	RequestParseEvent,
	ResponseEvent,
} from "../debug/telemetry/requests";
import type { TestCaseEvent } from "../debug/telemetry/tests";
import type {
	InitialConfigurationEvent,
	UpdatedConfigurationEvent,
} from "../debug/telemetry/config";
import type { UpdatedStateEvent } from "../debug/telemetry/state";
import type { ErrorTelemetryRecord } from "../debug/telemetry/errors";

import ROUTE_ADDED from "./fixtures/telemetry/route-added.json";
import REQUEST_EVENT from "./fixtures/telemetry/request-event.json";
import REQUEST_PARSE_EVENT from "./fixtures/telemetry/request-parse-event.json";
import RESPONSE_EVENT from "./fixtures/telemetry/response-event.json";
import PAGE_VISIT_EVENT from "./fixtures/telemetry/page-visit-event.json";
import TEST_CASE_EVENT from "./fixtures/telemetry/test-case-event.json";
import TEST_CASE_EVENT_FAILED from "./fixtures/telemetry/test-case-event-failed.json";
import INITIAL_CONFIGURATION from "./fixtures/telemetry/initial-configuration.json";
import UPDATED_CONFIGURATION from "./fixtures/telemetry/updated-configuration.json";
import UPDATED_STATE from "./fixtures/telemetry/updated-state.json";
import ERROR_RECORD from "./fixtures/telemetry/error-record.json";

const CONTAINER_ID = "drafter-debug-container";

// The panel constructor logs via console.error on setup problems and the
// engine sink registration mirrors errors; keep test output clean.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
const consoleWarnSpy = jest
	.spyOn(console, "warn")
	.mockImplementation(() => {});

afterEach(() => {
	// The DebugPanel constructor registers itself as the system error sink.
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	window.localStorage.clear();
	consoleErrorSpy.mockClear();
	consoleWarnSpy.mockClear();
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
	consoleWarnSpy.mockRestore();
});

function createPanel(): DebugPanel {
	// The minimal host DOM the DebugPanel constructor requires: the debug
	// container plus the header/footer bars it decorates.
	document.body.innerHTML = [
		'<div class="drafter-header--"></div>',
		'<div class="drafter-footer--"></div>',
		`<div id="${CONTAINER_ID}"></div>`,
	].join("");
	const bridge = { goto: jest.fn() } as unknown as ClientBridgeWrapperInterface;
	return new DebugPanel(CONTAINER_ID, bridge);
}

function container(): HTMLElement {
	return document.getElementById(CONTAINER_ID) as HTMLElement;
}

describe("RouteAdded", () => {
	test("student route renders into the regular routes list", () => {
		const panel = createPanel();
		const fixture = ROUTE_ADDED as RouteAddedEvent;

		expect(panel.handleEvent(fixture)).toBe(true);

		const regularList = container().querySelector(
			".drafter-debug-regular-routes-list-0, [class*='drafter-debug-regular-routes-list']",
		);
		const entry = regularList?.querySelector(
			".drafter-debug-route-signature",
		);
		expect(entry?.querySelector("strong")?.textContent).toBe("index");
		expect(entry?.querySelector("pre")?.textContent).toBe(
			"index(state: State) -> Page",
		);
	});

	test("system route renders into the system routes list", () => {
		const panel = createPanel();
		const fixture: RouteAddedEvent = {
			...(ROUTE_ADDED as RouteAddedEvent),
			url: "--reset",
			signature: "reset_server(state: State) -> Page",
			is_system_route: true,
		};

		expect(panel.handleEvent(fixture)).toBe(true);

		const systemList = container().querySelector(
			"[class*='drafter-debug-system-routes-list']",
		);
		expect(
			systemList?.querySelector(".drafter-debug-route-signature strong")
				?.textContent,
		).toBe("--reset");
	});

	test("a system 'index' route still renders in the regular list", () => {
		// Current behavior: renderRoute special-cases route == "index" so it
		// never lands in the collapsed system list, even when flagged system.
		const panel = createPanel();
		const fixture: RouteAddedEvent = {
			...(ROUTE_ADDED as RouteAddedEvent),
			is_system_route: true,
		};

		panel.handleEvent(fixture);

		const regularList = container().querySelector(
			"[class*='drafter-debug-regular-routes-list']",
		);
		expect(
			regularList?.querySelector(".drafter-debug-route-signature"),
		).not.toBeNull();
	});
});

describe("RequestEvent / RequestParseEvent / ResponseEvent", () => {
	test("RequestEvent renders a history entry with url, action, and id", () => {
		const panel = createPanel();

		expect(panel.handleEvent(REQUEST_EVENT as RequestEvent)).toBe(true);

		const item = container().querySelector(".history-event") as HTMLElement;
		expect(item).not.toBeNull();
		expect(item.dataset.requestId).toBe("1");
		expect(item.textContent).toContain("Visit:");
		expect(item.textContent).toContain("via");
		expect(item.textContent).toContain("click");
		expect(item.textContent).toContain("(ID: 1)");
		expect(
			item.querySelector(".drafter-history-request-url")?.textContent,
		).toBe("index");
	});

	test("RequestParseEvent attaches the parsed representation to its request", () => {
		const panel = createPanel();
		panel.handleEvent(REQUEST_EVENT as RequestEvent);

		expect(
			panel.handleEvent(REQUEST_PARSE_EVENT as RequestParseEvent),
		).toBe(true);

		const parse = container().querySelector(".request-parse-event code");
		expect(parse?.textContent).toBe(
			"index(state=State(score=0), name='Ada')",
		);
	});

	test("ResponseEvent marks the request and renders status and content", () => {
		const panel = createPanel();
		panel.handleEvent(REQUEST_EVENT as RequestEvent);

		expect(panel.handleEvent(RESPONSE_EVENT as ResponseEvent)).toBe(true);

		const item = container().querySelector(".history-event") as HTMLElement;
		expect(item.classList.contains("has-response")).toBe(true);
		const summary = item.querySelector(
			".drafter-debug-history-event-detail:last-of-type summary",
		);
		expect(summary?.textContent).toContain("ok");
		expect(summary?.textContent).toContain("Request ID: 1");
		expect(summary?.textContent).toContain("Response ID: 2");
		// Green marker: no errors, no warnings.
		expect(summary?.textContent).toContain("🟢");
		expect(item.querySelector("details pre")?.textContent).toContain(
			"Hello, Ada!",
		);
	});

	test("ResponseEvent with errors renders the red marker", () => {
		const panel = createPanel();
		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		const fixture: ResponseEvent = {
			...(RESPONSE_EVENT as ResponseEvent),
			status_code: "error",
			has_errors: true,
		};

		panel.handleEvent(fixture);

		expect(container().textContent).toContain("🔴");
	});

	test("malformed: RequestParseEvent for an unknown request id is ignored", () => {
		// The panel tolerates events referencing requests it never saw (e.g.
		// after a panel restart): the history panel warns, handleEvent reports
		// the event as unhandled, and nothing propagates to the Python
		// bridge's error-reporting path.
		const panel = createPanel();
		const fixture: RequestParseEvent = {
			...(REQUEST_PARSE_EVENT as RequestParseEvent),
			request_id: 999,
		};

		expect(panel.handleEvent(fixture)).toBe(false);

		expect(consoleWarnSpy).toHaveBeenCalledWith(
			expect.stringContaining("request 999 not found for parse event"),
		);
		// The record still reaches the event log.
		expect(
			container().querySelector(".drafter-log-info-item")?.textContent,
		).toContain("RequestParseEvent");
	});

	test("malformed: ResponseEvent for an unknown request id is ignored", () => {
		const panel = createPanel();
		const fixture: ResponseEvent = {
			...(RESPONSE_EVENT as ResponseEvent),
			request_id: 999,
		};

		expect(panel.handleEvent(fixture)).toBe(false);

		expect(consoleWarnSpy).toHaveBeenCalledWith(
			expect.stringContaining(
				"request 999 not found for response ID 2",
			),
		);
		expect(
			container().querySelector(".drafter-log-info-item")?.textContent,
		).toContain("ResponseEvent");
	});
});

describe("PageVisitEvent (removed dead kind)", () => {
	test("a legacy PageVisitEvent record falls through to the log only", () => {
		// PageVisitEvent was removed from the TS discriminated union: no
		// Python code ever emitted it. A record with that kind is now just an
		// unknown record: unhandled by the switch, but still logged.
		const panel = createPanel();

		expect(
			panel.handleEvent(PAGE_VISIT_EVENT as unknown as TelemetryRecord),
		).toBe(false);

		// metadata.level "info" routes it to the log panel's info renderer.
		const logItem = container().querySelector(".drafter-log-info-item");
		expect(logItem?.textContent).toContain("PageVisitEvent");
	});
});

describe("TestCaseEvent", () => {
	test("passing test renders a passed row and updates the summary", () => {
		const panel = createPanel();

		expect(panel.handleEvent(TEST_CASE_EVENT as TestCaseEvent)).toBe(true);

		const testCase = container().querySelector(".test-case");
		expect(testCase?.classList.contains("test-passed")).toBe(true);
		expect(testCase?.querySelector(".test-status")?.textContent).toBe("✅");
		expect(testCase?.querySelector(".test-line")?.textContent).toBe(
			"Line 42",
		);
		expect(testCase?.querySelector(".test-caller")?.textContent).toContain(
			"assert_equal",
		);

		const summary = container().querySelector(".test-summary");
		expect(summary?.textContent).toContain("Total Tests: 1");
		expect(summary?.textContent).toContain("Passed: 1");
		expect(summary?.textContent).toContain("Failed: 0");
	});

	test("failing test renders a failed row with a diff", () => {
		const panel = createPanel();

		expect(
			panel.handleEvent(TEST_CASE_EVENT_FAILED as TestCaseEvent),
		).toBe(true);

		const testCase = container().querySelector(".test-case");
		expect(testCase?.classList.contains("test-failed")).toBe(true);
		expect(testCase?.querySelector(".test-status")?.textContent).toBe("❌");
		// The unified diff from Python is rendered through Diff2Html.
		const diff = testCase?.querySelector(".test-case-diff");
		expect(diff?.innerHTML).not.toBe("");
		expect(diff?.textContent).toContain("Goodbye");

		const summary = container().querySelector(".test-summary");
		expect(summary?.textContent).toContain("Failed: 1");
	});

	test("summary accumulates across multiple test events", () => {
		const panel = createPanel();

		panel.handleEvent(TEST_CASE_EVENT as TestCaseEvent);
		panel.handleEvent(TEST_CASE_EVENT_FAILED as TestCaseEvent);

		const summary = container().querySelector(".test-summary");
		expect(summary?.textContent).toContain("Total Tests: 2");
		expect(summary?.textContent).toContain("Passed: 1");
		expect(summary?.textContent).toContain("Failed: 1");
	});
});

describe("InitialConfiguration / UpdatedConfiguration", () => {
	test("InitialConfiguration renders one item per key, sorted, as Embedded", () => {
		const panel = createPanel();

		expect(
			panel.handleEvent(
				INITIAL_CONFIGURATION as unknown as InitialConfigurationEvent,
			),
		).toBe(true);

		const items = Array.from(
			container().querySelectorAll(".drafter-debug-config-item"),
		) as HTMLElement[];
		const keys = items.map((item) => item.dataset.key);
		const configKeys = Object.keys(
			(INITIAL_CONFIGURATION as unknown as InitialConfigurationEvent)
				.config,
		);
		expect(items).toHaveLength(configKeys.length);
		expect(keys).toEqual([...configKeys].sort((a, b) => a.localeCompare(b)));

		const themeItem = items.find((item) => item.dataset.key === "theme");
		expect(
			themeItem?.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"default"');
		expect(
			themeItem?.querySelector(".drafter-debug-config-source")
				?.textContent,
		).toBe("Embedded");
	});

	test("UpdatedConfiguration updates the item and marks it updated", () => {
		const panel = createPanel();
		panel.handleEvent(
			INITIAL_CONFIGURATION as unknown as InitialConfigurationEvent,
		);

		expect(
			panel.handleEvent(
				UPDATED_CONFIGURATION as UpdatedConfigurationEvent,
			),
		).toBe(true);

		const themeItem = container().querySelector(
			'.drafter-debug-config-item[data-key="theme"]',
		) as HTMLElement;
		expect(
			themeItem.classList.contains("drafter-debug-config-item-updated"),
		).toBe(true);
		expect(
			themeItem.querySelector(".drafter-debug-config-inline-value")
				?.textContent,
		).toBe('"dark"');
	});

	test("UpdatedConfiguration for a brand-new key appends a new item", () => {
		const panel = createPanel();
		const fixture: UpdatedConfigurationEvent = {
			...(UPDATED_CONFIGURATION as UpdatedConfigurationEvent),
			key: "brand_new_key",
			value: 12,
		};

		expect(panel.handleEvent(fixture)).toBe(true);

		const item = container().querySelector(
			'.drafter-debug-config-item[data-key="brand_new_key"]',
		);
		expect(item?.textContent).toContain("12");
	});
});

describe("UpdatedState", () => {
	test("renders a dataclass representation with fields and nested values", () => {
		const panel = createPanel();

		expect(
			panel.handleEvent(UPDATED_STATE as unknown as UpdatedStateEvent),
		).toBe(true);

		const dataclass = container().querySelector(
			".drafter-debug-rep-dataclass",
		);
		expect(dataclass).not.toBeNull();
		expect(
			dataclass?.querySelector(".drafter-debug-rep-dataclass-type")
				?.textContent,
		).toBe("State");
		expect(dataclass?.textContent).toContain("name:");
		expect(dataclass?.textContent).toContain("'Ada'");
		expect(dataclass?.textContent).toContain("score:");
		expect(dataclass?.textContent).toContain("5");

		const list = dataclass?.querySelector(
			".drafter-debug-rep-homogenous-linear-collection",
		);
		expect(list?.textContent).toContain("list[str]");
		expect(list?.textContent).toContain("'apple'");
		expect(list?.textContent).toContain("'bread'");
	});

	test("re-render replaces the previous state", () => {
		const panel = createPanel();
		panel.handleEvent(UPDATED_STATE as unknown as UpdatedStateEvent);

		const primitiveOnly: UpdatedStateEvent = {
			...(UPDATED_STATE as unknown as UpdatedStateEvent),
			representation: {
				kind: "primitive",
				value: "7",
				type: "int",
				id: 9793312,
				complexity: 1,
			},
		};
		panel.handleEvent(primitiveOnly);

		expect(
			container().querySelector(".drafter-debug-rep-dataclass"),
		).toBeNull();
		const primitive = container().querySelector(
			".drafter-debug-rep-primitive",
		);
		expect(primitive?.textContent).toContain("7");
		expect(primitive?.textContent).toContain("int");
	});

	test("unknown representation kinds fall back to the default renderer", () => {
		// Forward-compatibility behavior: renderRepresentation's default case
		// prints the kind/type rather than crashing.
		const panel = createPanel();
		const fixture = {
			...(UPDATED_STATE as unknown as UpdatedStateEvent),
			representation: {
				kind: "hologram",
				type: "Hologram",
				id: 1,
				complexity: 1,
			},
		} as unknown as UpdatedStateEvent;

		expect(panel.handleEvent(fixture)).toBe(true);

		const fallback = container().querySelector(".drafter-debug-rep-default");
		expect(fallback?.textContent).toContain("hologram");
		expect(fallback?.textContent).toContain("Hologram");
	});
});

describe("ErrorRecord and unknown kinds", () => {
	test("Python ErrorRecord is unhandled by the switch but logged as an error", () => {
		// ErrorRecords have kind == the error's stable id, so they always take
		// the default branch (handled=false); the log panel detects the
		// embedded envelope and renders by its severity.
		const panel = createPanel();

		expect(
			panel.handleEvent(
				ERROR_RECORD as unknown as ErrorTelemetryRecord,
			),
		).toBe(false);

		const logError = container().querySelector(".drafter-log-error-item");
		expect(logError?.textContent).toContain(
			"The route 'missing_page' was not found.",
		);
	});

	test("warning-severity envelope routes to the warning log renderer", () => {
		const errorRecord = ERROR_RECORD as unknown as ErrorTelemetryRecord;
		const panel = createPanel();
		const fixture: ErrorTelemetryRecord = {
			...errorRecord,
			error: {
				...errorRecord.error,
				severity: "warning",
				message: "Only a warning",
			},
		};

		panel.handleEvent(fixture);

		expect(
			container().querySelector(".drafter-log-warning-item")?.textContent,
		).toContain("Only a warning");
	});

	test("unknown kind without an envelope falls back to metadata level", () => {
		const panel = createPanel();
		const fixture = {
			kind: "ResetServer",
			metadata: {
				source: "client_server.reset",
				level: "info",
				id: 50,
				version: "2.0.0b10",
				timestamp: "2026-07-23T10:15:35.000000",
			},
			correlation: {},
		} as TelemetryRecord;

		expect(panel.handleEvent(fixture)).toBe(false);

		expect(
			container().querySelector(".drafter-log-info-item")?.textContent,
		).toContain("ResetServer");
	});

	test("malformed: record missing metadata is tolerated and logged as default", () => {
		// Current behavior: the log panel's optional-chained metadata lookup
		// makes a metadata-less record land in the default renderer.
		const panel = createPanel();
		const fixture = { kind: "Bogus" } as TelemetryRecord;

		expect(panel.handleEvent(fixture)).toBe(false);

		expect(
			container().querySelector(".drafter-log-default-item")?.textContent,
		).toContain("Bogus");
	});
});
