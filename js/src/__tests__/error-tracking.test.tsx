/**
 * Tests for reporting each error once (drafter-edu/drafter#174).
 *
 * - engine.ts marks every error object it reports, so a reporter higher up
 *   (or the window's error event) recognizes it instead of reporting again;
 * - utils/errors.ts fingerprints envelopes so sinks can count repeats;
 * - the Current tab, the Log tab, and the dev-server log sender collapse
 *   repeats into counters;
 * - the browser tab's title carries the problem counts.
 */
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	installUncaughtErrorListeners,
	isErrorReported,
	markErrorReported,
	reportSystemError,
	setSystemErrorSink,
} from "../bridge/engine";
import type { ErrorTelemetryRecord } from "../debug/telemetry/errors";
import type { ErrorDetailsJson } from "../debug/telemetry/errors";
import { errorFingerprint } from "../debug/utils/errors";
import {
	DevServerErrorReporter,
	MAX_DELIVERIES_PER_PROBLEM,
} from "../debug/error_reporter";
import { DebugPanel } from "../debug/index";
import type { TelemetryRecord } from "../debug/telemetry";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";

const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});
jest.spyOn(console, "warn").mockImplementation(() => {});
jest.spyOn(console, "info").mockImplementation(() => {});

function envelope(
	overrides: Partial<ErrorDetailsJson> = {},
): ErrorDetailsJson {
	return {
		id: "request.route_execution_failed",
		category: "request",
		severity: "error",
		message: "ZeroDivisionError: division by zero",
		details: "",
		traceback:
			'Traceback (most recent call last):\n  File "main.py", line 12, in tick\n    1 / 0\nZeroDivisionError: division by zero',
		context: {
			causation_id: null,
			route: "tick",
			request_id: 7,
			response_id: null,
			dom_id: null,
			phase: null,
		},
		status_code: "error",
		recoverable: true,
		...overrides,
	};
}

function record(env: ErrorDetailsJson): TelemetryRecord {
	return {
		kind: env.id,
		metadata: {
			level: env.severity === "warning" ? "warning" : "error",
		},
		error: env,
	} as unknown as TelemetryRecord;
}

afterEach(() => {
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	document.title = "";
	window.localStorage.clear();
	consoleErrorSpy.mockClear();
});

describe("marking reported errors", () => {
	test("reportSystemError marks the error object it was given", () => {
		const error = new Error("boom");

		reportSystemError({
			id: "runtime.test",
			category: "runtime",
			message: "Test failure",
			error,
			presentation: "log",
		});

		expect(isErrorReported(error)).toBe(true);
	});

	test("a second report of the same error object is not logged again", () => {
		const delivered: ErrorTelemetryRecord[] = [];
		setSystemErrorSink((event) => delivered.push(event));
		const error = new Error("boom");

		reportSystemError({
			id: "runtime.inner",
			category: "runtime",
			message: "Inner",
			error,
			presentation: "log",
		});
		reportSystemError({
			id: "runtime.outer",
			category: "runtime",
			message: "Outer",
			error,
			presentation: "log",
		});

		expect(delivered.map((event) => event.kind)).toEqual(["runtime.inner"]);
		expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
	});

	test("a reported-but-unshown error is still shown when a later report would show it", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		const error = new Error("boom");

		reportSystemError({
			id: "runtime.inner",
			category: "runtime",
			message: "Inner",
			error,
			presentation: "log",
		});
		reportSystemError({
			id: "runtime.outer",
			category: "runtime",
			message: "Outer",
			error,
			severity: "critical",
		});

		expect(
			document.querySelector("#drafter-root-- .drafter-system-error"),
		).not.toBeNull();
	});

	test("different error objects are reported separately", () => {
		const delivered: ErrorTelemetryRecord[] = [];
		setSystemErrorSink((event) => delivered.push(event));

		reportSystemError({
			id: "runtime.a",
			category: "runtime",
			message: "A",
			error: new Error("same text"),
			presentation: "log",
		});
		reportSystemError({
			id: "runtime.b",
			category: "runtime",
			message: "B",
			error: new Error("same text"),
			presentation: "log",
		});

		expect(delivered).toHaveLength(2);
	});

	test("markErrorReported ignores values that are not objects", () => {
		markErrorReported("just text");
		markErrorReported(null);

		expect(isErrorReported("just text")).toBe(false);
		expect(isErrorReported(null)).toBe(false);
	});
});

describe("uncaught error listeners", () => {
	let delivered: ErrorTelemetryRecord[];

	beforeEach(() => {
		delivered = [];
		setSystemErrorSink((event) => delivered.push(event));
		installUncaughtErrorListeners(window);
	});

	function dispatchError(error: unknown, message = "x") {
		window.dispatchEvent(
			new ErrorEvent("error", { error, message, cancelable: true }),
		);
	}

	test("an error nobody reported reaches the panel as a logged problem", () => {
		dispatchError(new Error("from a timer callback"));

		expect(delivered).toHaveLength(1);
		expect(delivered[0].kind).toBe("runtime.uncaught_error");
		expect(delivered[0].error.severity).toBe("error");
		// Logged only: no dialog, no error page.
		expect(document.querySelector(".drafter-dialog")).toBeNull();
	});

	test("an error Drafter already reported and threw onward is skipped", () => {
		const error = reportSystemError({
			id: "runtime.student_code_failed",
			category: "runtime",
			message: "Error running student code",
			error: new Error("ModuleNotFoundError"),
			presentation: "log",
		});
		delivered.length = 0;

		dispatchError(error);

		expect(delivered).toHaveLength(0);
	});

	test("opaque errors from other sites' scripts are ignored", () => {
		dispatchError(null, "Script error.");
		dispatchError(null, "");

		expect(delivered).toHaveLength(0);
	});

	test("an unhandled promise rejection is reported once", () => {
		const reason = new Error("fetch failed");
		const event = new Event("unhandledrejection") as Event & {
			reason?: unknown;
		};
		event.reason = reason;

		window.dispatchEvent(event);
		window.dispatchEvent(event);

		expect(delivered.map((e) => e.kind)).toEqual([
			"runtime.unhandled_rejection",
		]);
	});

	test("installing twice adds no second set of listeners", () => {
		installUncaughtErrorListeners(window);

		dispatchError(new Error("once"));

		expect(delivered).toHaveLength(1);
	});
});

describe("errorFingerprint", () => {
	test("the same failure on two visits to one route fingerprints alike", () => {
		const first = envelope({ context: { ...envelope().context, request_id: 7 } });
		const second = envelope({
			context: { ...envelope().context, request_id: 8 },
		});

		expect(errorFingerprint(first)).toBe(errorFingerprint(second));
	});

	test("a different message, raise site, or route is a different problem", () => {
		const base = envelope();

		expect(errorFingerprint(envelope({ message: "KeyError: 'x'" }))).not.toBe(
			errorFingerprint(base),
		);
		expect(
			errorFingerprint(
				envelope({
					traceback: base.traceback!.replace("line 12", "line 30"),
				}),
			),
		).not.toBe(errorFingerprint(base));
		expect(
			errorFingerprint(
				envelope({ context: { ...base.context, route: "index" } }),
			),
		).not.toBe(errorFingerprint(base));
	});

	test("only the first line of a message counts", () => {
		const a = envelope({ message: "Failed\nwith detail one" });
		const b = envelope({ message: "Failed\nwith detail two" });

		expect(errorFingerprint(a)).toBe(errorFingerprint(b));
	});
});

describe("repeats in the debug panel", () => {
	const CONTAINER_ID = "drafter-debug-tracking";

	function createPanel(): DebugPanel {
		// The same host DOM the bridge provides: a header and footer frame
		// plus the panel's container.
		document.body.innerHTML = [
			'<div class="drafter-header--"></div>',
			'<div class="drafter-footer--"></div>',
			`<div id="${CONTAINER_ID}"></div>`,
		].join("");
		document.title = "Corgi Cafe";
		return new DebugPanel(CONTAINER_ID, {
			goto: jest.fn(),
		} as unknown as ClientBridgeWrapperInterface);
	}
	function problems(): HTMLElement[] {
		return Array.from(
			document.querySelectorAll(".drafter-debug-current-problem"),
		) as HTMLElement[];
	}

	test("a repeated problem raises a counter instead of adding a line", () => {
		const panel = createPanel();

		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope()));

		expect(problems()).toHaveLength(1);
		expect(
			problems()[0].querySelector(".drafter-debug-problem-count")?.textContent,
		).toBe("×3");
	});

	test("the badge and footer count problems, not repeats", () => {
		const panel = createPanel();

		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope({ message: "KeyError: 'x'" })));

		const badge = document.querySelector(
			".drafter-debug-tab-badge.is-error",
		) as HTMLElement;
		expect(badge.textContent).toBe("2");
		expect(
			document.querySelector(".drafter-footer-status")?.textContent,
		).toContain("2");
	});

	test("the Log tab folds a repeated line into one with a count", () => {
		const panel = createPanel();

		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope({ message: "KeyError: 'x'" })));

		const lines = Array.from(
			document.querySelectorAll(".drafter-log-error-item"),
		);
		expect(lines).toHaveLength(2);
		expect(
			lines[0].querySelector(".drafter-debug-problem-count")?.textContent,
		).toBe(" ×2");
		expect(lines[1].querySelector(".drafter-debug-problem-count")).toBeNull();
	});

	test("the browser tab title carries the counts and returns to normal", () => {
		const panel = createPanel();

		panel.handleEvent(record(envelope()));
		panel.handleEvent(record(envelope({ severity: "warning", id: "w" })));
		expect(document.title).toBe("(1 error, 1 warning) Corgi Cafe");

		// A new visit starts a fresh slate for request-scoped problems.
		panel.handleEvent({
			kind: "RequestEvent",
			metadata: { level: "info" },
			url: "index",
			action: "link",
			event: "{}",
			kwargs: "{}",
			kwargs_json: "{}",
			request_id: 99,
		} as unknown as TelemetryRecord);
		expect(document.title).toBe("Corgi Cafe");
	});
});

describe("the dev-server log sender counts repeats", () => {
	let fetchMock: jest.Mock<typeof fetch>;

	beforeEach(() => {
		fetchMock = jest.fn(async () => new Response("", { status: 200 }));
		(globalThis as { fetch: typeof fetch }).fetch =
			fetchMock as unknown as typeof fetch;
	});

	function sentReports(call = 0): Array<{ id: string; repeat_count: number }> {
		const body = JSON.parse(
			(fetchMock.mock.calls[call][1] as RequestInit).body as string,
		);
		return body.reports;
	}

	test("repeats within one batch become one report with a count", async () => {
		const reporter = new DevServerErrorReporter("/log");

		reporter.report(envelope());
		reporter.report(envelope());
		reporter.report(envelope({ message: "KeyError: 'x'" }));
		await reporter.flush();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		expect(sentReports().map((r) => [r.id, r.repeat_count])).toEqual([
			["request.route_execution_failed", 2],
			["request.route_execution_failed", 1],
		]);
	});

	test("a problem is written only a few times per session", async () => {
		const reporter = new DevServerErrorReporter("/log");

		for (let i = 0; i < MAX_DELIVERIES_PER_PROBLEM + 2; i++) {
			reporter.report(envelope());
			await reporter.flush();
		}

		expect(fetchMock).toHaveBeenCalledTimes(MAX_DELIVERIES_PER_PROBLEM);
	});
});
