import { afterEach, describe, expect, test } from "@jest/globals";

import {
	normalizeSystemError,
	reportSystemError,
	setSystemErrorSink,
	type ErrorTelemetryRecord,
} from "../bridge/engine";

afterEach(() => {
	setSystemErrorSink(null);
	document.body.innerHTML = "";
});

describe("system error helpers", () => {
	test("normalizeSystemError wraps non-Error values", () => {
		const error = normalizeSystemError("boom");

		expect(error).toBeInstanceOf(Error);
		expect(error.message).toBe("boom");
	});
});

describe("reportSystemError presentation policy", () => {
	test("unrecoverable errors render into the root", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError({
			id: "runtime.pyodide_setup_failed",
			category: "runtime",
			message: "Error setting up Pyodide",
			error: new Error("boom"),
		});

		const root = document.getElementById("drafter-root--");
		expect(root?.querySelector(".drafter-system-error")).not.toBeNull();
		expect(root?.textContent).toContain("Something Went Wrong");
		expect(root?.textContent).toContain("Error setting up Pyodide");
	});

	test("recoverable errors do not take over the root", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError({
			id: "runtime.student_code_failed",
			category: "runtime",
			message: "Error running student code",
			error: new Error("boom"),
			recoverable: true,
		});

		const root = document.getElementById("drafter-root--");
		expect(root?.querySelector(".drafter-system-error")).toBeNull();
	});

	test("warnings only go to the debug panel sink", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		const received: ErrorTelemetryRecord[] = [];
		setSystemErrorSink((event) => received.push(event));

		reportSystemError({
			id: "runtime.slow_startup",
			category: "runtime",
			message: "Startup took longer than expected",
			severity: "warning",
		});

		const root = document.getElementById("drafter-root--");
		expect(root?.querySelector(".drafter-system-error")).toBeNull();
		expect(received).toHaveLength(1);
		expect(received[0].metadata.level).toBe("warning");
		expect(received[0].error.severity).toBe("warning");
	});

	test("sink receives canonical envelope with stable id and context", () => {
		const received: ErrorTelemetryRecord[] = [];
		setSystemErrorSink((event) => received.push(event));

		reportSystemError({
			id: "runtime.pyodide_setup_failed",
			category: "runtime",
			message: "Error setting up Pyodide",
			error: new Error("boom"),
			context: { phase: "setup", request_id: 3, route: "index" },
		});

		expect(received).toHaveLength(1);
		const event = received[0];
		expect(event.kind).toBe("runtime.pyodide_setup_failed");
		expect(event.metadata.level).toBe("error");
		expect(event.correlation.request_id).toBe(3);
		expect(event.correlation.route).toBe("index");
		const envelope = event.error;
		expect(envelope.id).toBe("runtime.pyodide_setup_failed");
		expect(envelope.category).toBe("runtime");
		expect(envelope.severity).toBe("error");
		expect(envelope.status_code).toBe("error");
		expect(envelope.recoverable).toBe(false);
		expect(envelope.context.phase).toBe("setup");
		expect(envelope.details).toContain("boom");
	});

	test("sink failures do not break error reporting", () => {
		setSystemErrorSink(() => {
			throw new Error("sink exploded");
		});

		const error = reportSystemError({
			id: "runtime.pyodide_setup_failed",
			category: "runtime",
			message: "Error setting up Pyodide",
			error: new Error("boom"),
		});

		expect(error).toBeInstanceOf(Error);
		expect(error.message).toBe("boom");
	});
});
