/**
 * Tests for the Phase-4 debug panel additions driven through DebugPanel:
 * the Current tab's CurrentPanel (route, page content, per-navigation
 * problems, state diff), the error/warning badges and footer status area,
 * the Tests tab fail badge, and the Environment tab's real Packages and
 * Storage panels.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { DebugPanel } from "../debug/index";
import { setSystemErrorSink } from "../bridge/engine";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";
import type { RequestEvent, ResponseEvent } from "../debug/telemetry/requests";
import type { UpdatedStateEvent } from "../debug/telemetry/state";
import type { TestCaseEvent } from "../debug/telemetry/tests";
import type { TelemetryRecord } from "../debug/telemetry";

import REQUEST_EVENT from "./fixtures/telemetry/request-event.json";
import RESPONSE_EVENT from "./fixtures/telemetry/response-event.json";
import UPDATED_STATE from "./fixtures/telemetry/updated-state.json";

const CONTAINER_ID = "drafter-debug-container";

const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
const consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => {});

afterEach(() => {
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	window.localStorage.clear();
	delete (window as { pyodide?: unknown }).pyodide;
	consoleErrorSpy.mockClear();
	consoleLogSpy.mockClear();
});

function createPanel(): DebugPanel {
	document.body.innerHTML = [
		'<div class="drafter-header--"></div>',
		'<div class="drafter-footer--"></div>',
		`<div id="${CONTAINER_ID}"></div>`,
	].join("");
	return new DebugPanel(
		CONTAINER_ID,
		{ goto: jest.fn() } as unknown as ClientBridgeWrapperInterface,
	);
}

function errorRecord(
	severity: "error" | "warning",
	message: string,
	// Request-scoped by default; pass null for a global (startup) problem
	// that is not tied to any page.
	requestId: number | null = 7,
): TelemetryRecord {
	return {
		kind: "some.failure",
		metadata: { level: severity === "error" ? "error" : "warning" },
		error: {
			id: "some.failure",
			category: "bridge",
			severity,
			message,
			details: "extra context",
			traceback: null,
			context: {
				causation_id: null,
				route: null,
				request_id: requestId,
				response_id: null,
				dom_id: null,
				phase: null,
			},
			status_code: "error",
			recoverable: true,
		},
	} as unknown as TelemetryRecord;
}

function query(selector: string): HTMLElement {
	return document.querySelector(selector) as HTMLElement;
}

describe("CurrentPanel", () => {
	test("request/response events fill the route and page content", () => {
		const panel = createPanel();

		const request: RequestEvent = {
			...(REQUEST_EVENT as RequestEvent),
			url: "guess",
		};
		panel.handleEvent(request);
		panel.handleEvent(RESPONSE_EVENT as ResponseEvent);

		expect(query(".drafter-debug-current-route").textContent).toBe(
			"guess",
		);
		expect(
			query(".drafter-debug-current-page-content").textContent,
		).toContain("Hello, Ada!");
	});

	test("setRoute mirrors the committed route into the Current tab", () => {
		const panel = createPanel();

		panel.setRoute("give_up");

		expect(query(".drafter-debug-current-route").textContent).toBe(
			"give_up",
		);
	});

	test("problems accumulate and reset on the next navigation", () => {
		const panel = createPanel();
		panel.handleEvent(errorRecord("error", "Route crashed"));
		panel.handleEvent(errorRecord("warning", "Type looks off"));

		let problems = document.querySelectorAll(
			".drafter-debug-current-problem",
		);
		expect(problems).toHaveLength(2);
		expect(problems[0].textContent).toContain("Route crashed");
		expect(
			query(".drafter-debug-current-problems").querySelector(
				".drafter-debug-current-no-problems",
			),
		).toBeNull();

		// A new visit wipes the slate.
		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		problems = document.querySelectorAll(
			".drafter-debug-current-problem",
		);
		expect(problems).toHaveLength(0);
		expect(
			query(".drafter-debug-current-problems").querySelector(
				".drafter-debug-current-no-problems",
			),
		).not.toBeNull();
	});

	test("problems without a request correlation survive navigations", () => {
		const panel = createPanel();
		// A startup warning (e.g. a route-signature problem replayed into the
		// panel before the first visit) carries no request id.
		panel.handleEvent(errorRecord("warning", "State type looks off", null));
		panel.handleEvent(errorRecord("error", "Route crashed", 7));

		expect(
			document.querySelectorAll(".drafter-debug-current-problem"),
		).toHaveLength(2);

		// The navigation wipes only the page-scoped problem.
		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		const problems = document.querySelectorAll(
			".drafter-debug-current-problem",
		);
		expect(problems).toHaveLength(1);
		expect(problems[0].textContent).toContain("State type looks off");
		expect(
			query(".drafter-debug-current-problems").querySelector(
				".drafter-debug-current-no-problems",
			),
		).toBeNull();
	});
});

describe("problem badges and footer status", () => {
	function currentBadge(): HTMLElement {
		return query(
			"[id^='drafter-debug-tab-btn-current-'] .drafter-debug-tab-badge",
		);
	}

	test("errors and warnings drive the Current tab badge and footer", () => {
		const panel = createPanel();
		expect(currentBadge().hidden).toBe(true);
		expect(query(".drafter-footer-status").hidden).toBe(true);

		panel.handleEvent(errorRecord("warning", "hmm"));
		expect(currentBadge().hidden).toBe(false);
		expect(currentBadge().textContent).toBe("1");
		expect(currentBadge().classList.contains("is-warn")).toBe(true);

		panel.handleEvent(errorRecord("error", "boom"));
		expect(currentBadge().textContent).toBe("2");
		expect(currentBadge().classList.contains("is-error")).toBe(true);

		const status = query(".drafter-footer-status");
		expect(status.hidden).toBe(false);
		expect(status.textContent).toContain("❌ 1");
		expect(status.textContent).toContain("⚠️ 1");

		// Navigation resets the per-page indicators.
		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		expect(currentBadge().hidden).toBe(true);
		expect(query(".drafter-footer-status").hidden).toBe(true);
	});

	test("global problems keep the badge and footer counts after navigation", () => {
		const panel = createPanel();
		panel.handleEvent(errorRecord("warning", "startup warning", null));
		expect(currentBadge().textContent).toBe("1");

		panel.handleEvent(REQUEST_EVENT as RequestEvent);
		expect(currentBadge().hidden).toBe(false);
		expect(currentBadge().textContent).toBe("1");
		expect(currentBadge().classList.contains("is-warn")).toBe(true);
		expect(query(".drafter-footer-status").textContent).toContain("⚠️ 1");
	});

	test("clicking the footer status activates the Current tab", () => {
		const panel = createPanel();
		panel.handleEvent(errorRecord("error", "boom"));
		// Move away from the Current tab first.
		(
			query("[id^='drafter-debug-tab-btn-history-']") as HTMLButtonElement
		).click();

		(query(".drafter-footer-status") as HTMLButtonElement).click();

		expect(
			query("[id^='drafter-debug-tab-btn-current-']").getAttribute(
				"aria-selected",
			),
		).toBe("true");
	});

	test("failing tests drive the Tests tab badge", () => {
		const panel = createPanel();
		const testCase = {
			kind: "TestCaseEvent",
			passed: false,
			line: 12,
			caller: "assert_equal",
			message: "Values differ",
			diff_html:
				"--- expected\n+++ actual\n@@ -1 +1 @@\n-a\n+b\n",
		} as unknown as TestCaseEvent;

		panel.handleEvent(testCase);

		const badge = query(
			"[id^='drafter-debug-tab-btn-tests-'] .drafter-debug-tab-badge",
		);
		expect(badge.hidden).toBe(false);
		expect(badge.textContent).toBe("1");
		expect(badge.classList.contains("is-fail")).toBe(true);
	});
});

describe("state diff", () => {
	function stateEvent(score: string): UpdatedStateEvent {
		const base = UPDATED_STATE as unknown as UpdatedStateEvent;
		const representation = JSON.parse(
			JSON.stringify(base.representation),
		) as { fields: Array<{ name: string; value: { value: string } }> };
		const scoreField = representation.fields.find(
			(field) => field.name === "score",
		);
		scoreField!.value.value = score;
		return { ...base, representation } as UpdatedStateEvent;
	}

	test("with two states, the diff renders via diff2html", () => {
		const panel = createPanel();
		panel.handleEvent(stateEvent("5"));
		panel.handleEvent(stateEvent("6"));

		(
			query(
				".drafter-debug-current-diff-button",
			) as HTMLButtonElement
		).click();

		const diff = query(".drafter-debug-current-diff");
		expect(diff.querySelector(".d2h-wrapper")).not.toBeNull();
		expect(diff.textContent).toContain("5");
		expect(diff.textContent).toContain("6");
	});

	test("with fewer than two states, friendly messages appear instead", () => {
		const panel = createPanel();
		const button = query(
			".drafter-debug-current-diff-button",
		) as HTMLButtonElement;

		button.click();
		expect(
			query(".drafter-debug-current-diff").textContent,
		).toContain("No state has been recorded yet.");

		panel.handleEvent(stateEvent("5"));
		button.click();
		expect(
			query(".drafter-debug-current-diff").textContent,
		).toContain("nothing to compare");

		panel.handleEvent(stateEvent("5"));
		button.click();
		expect(
			query(".drafter-debug-current-diff").textContent,
		).toContain("did not change");
	});
});

describe("PackagesPanel", () => {
	test("lists pyodide's loaded packages when available", () => {
		(window as { pyodide?: unknown }).pyodide = {
			loadedPackages: { numpy: "default channel", pillow: "pypi" },
		};
		createPanel();

		const table = query(".drafter-debug-packages-table");
		expect(table).not.toBeNull();
		expect(table.textContent).toContain("numpy");
		expect(table.textContent).toContain("pypi");
	});

	test("degrades gracefully without a pyodide runtime", () => {
		createPanel();

		expect(query(".drafter-debug-packages-empty").textContent).toContain(
			"not available",
		);
	});
});

describe("StoragePanel", () => {
	test("lists keys and deletes drafter-owned ones", () => {
		window.localStorage.setItem("drafter.debug.something.v1", "abc");
		window.localStorage.setItem("someone-elses-key", "xyz");
		createPanel();
		// Re-render after the constructor-time render (the tab remembers the
		// active-tab key the TabBar just wrote).
		(
			query(".drafter-debug-storage-refresh") as HTMLButtonElement
		).click();

		const table = query(".drafter-debug-storage-table");
		expect(table.textContent).toContain("drafter.debug.something.v1");
		expect(table.textContent).toContain("someone-elses-key");

		// Only the drafter.* row has a delete button.
		const rows = Array.from(table.querySelectorAll("tbody tr"));
		const drafterRow = rows.find((row) =>
			row.textContent?.includes("drafter.debug.something.v1"),
		) as HTMLElement;
		const foreignRow = rows.find((row) =>
			row.textContent?.includes("someone-elses-key"),
		) as HTMLElement;
		expect(
			foreignRow.querySelector(".drafter-debug-storage-delete"),
		).toBeNull();

		(
			drafterRow.querySelector(
				".drafter-debug-storage-delete",
			) as HTMLButtonElement
		).click();

		expect(
			window.localStorage.getItem("drafter.debug.something.v1"),
		).toBeNull();
		expect(window.localStorage.getItem("someone-elses-key")).toBe("xyz");
	});
});
