/**
 * Unit tests for the error engine (js/src/bridge/engine.ts):
 * - the canonical envelope emitted to the telemetry sink (buildEnvelope,
 *   via reportSystemError since buildEnvelope is module-private),
 * - normalizeSystemError for every input class,
 * - the presentation policy matrix (resolvePresentation), asserted through
 *   where the error actually surfaces (root render, dialog, or sink only),
 * - the student-facing root rendering (buildStudentLead / buildStudentSteps).
 */
import {
	afterAll,
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	clearDrafterSiteRoot,
	normalizeSystemError,
	reportSystemError,
	setSystemErrorSink,
	type ErrorTelemetryRecord,
} from "../bridge/engine";
import type { SystemErrorReport } from "../debug/telemetry/errors";

// reportSystemError always mirrors to console.error; keep test output clean.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});

beforeEach(() => {
	consoleErrorSpy.mockClear();
});

afterEach(() => {
	// Close any dialog the engine opened (the engine passes the report id as
	// the dialog's symbolicId, so an unclosed dialog would be reused by the
	// next test that reports the same id).
	document
		.querySelectorAll<HTMLButtonElement>(".drafter-dialog-close")
		.forEach((button) => button.click());
	setSystemErrorSink(null);
	document.body.innerHTML = "";
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
});

function captureSink(): ErrorTelemetryRecord[] {
	const received: ErrorTelemetryRecord[] = [];
	setSystemErrorSink((event) => received.push(event));
	return received;
}

function baseReport(overrides: Partial<SystemErrorReport> = {}): SystemErrorReport {
	return {
		id: "runtime.test_error",
		category: "runtime",
		message: "Test failure message",
		...overrides,
	};
}

describe("normalizeSystemError", () => {
	test("returns Error instances unchanged (same reference)", () => {
		const original = new TypeError("bad type");
		expect(normalizeSystemError(original)).toBe(original);
	});

	test.each([
		["string", "boom", "boom"],
		["number", 42, "42"],
		["boolean", false, "false"],
		["null", null, "null"],
		["undefined", undefined, "undefined"],
		// Python-style error objects (e.g. {type, msg}) are NOT specially
		// handled: they stringify like any other object.
		["plain object", { type: "NameError", msg: "x" }, "[object Object]"],
		["array", ["a", "b"], "a,b"],
	])("wraps %s in an Error via String()", (_label, value, expected) => {
		const error = normalizeSystemError(value);
		expect(error).toBeInstanceOf(Error);
		expect(error.message).toBe(expected);
	});

	test("uses a custom toString when the value provides one", () => {
		const error = normalizeSystemError({
			toString: () => "NameError: name 'x' is not defined",
		});
		expect(error.message).toBe("NameError: name 'x' is not defined");
	});
});

describe("envelope shape (via the telemetry sink)", () => {
	test("every envelope field for a fully-specified report", () => {
		const received = captureSink();
		const thrown = new RangeError("out of range");

		reportSystemError({
			id: "bridge.render_failed",
			category: "bridge",
			message: "Rendering failed",
			severity: "warning",
			recoverable: true,
			error: thrown,
			context: {
				causation_id: 6,
				route: "index",
				request_id: 7,
				response_id: 8,
				dom_id: "drafter-root--",
				phase: "render",
			},
		});

		expect(received).toHaveLength(1);
		const envelope = received[0].error;
		expect(envelope.id).toBe("bridge.render_failed");
		expect(envelope.category).toBe("bridge");
		expect(envelope.severity).toBe("warning");
		expect(envelope.message).toBe("Rendering failed");
		expect(envelope.details).toBe("RangeError: out of range");
		expect(envelope.traceback).toBe(thrown.stack);
		expect(envelope.context).toEqual({
			causation_id: 6,
			route: "index",
			request_id: 7,
			response_id: 8,
			dom_id: "drafter-root--",
			phase: "render",
		});
		expect(envelope.status_code).toBe("error");
		expect(envelope.recoverable).toBe(true);
	});

	test("defaults: severity 'error', recoverable false, null context fields", () => {
		const received = captureSink();

		reportSystemError(baseReport({ error: new Error("boom") }));

		const envelope = received[0].error;
		expect(envelope.severity).toBe("error");
		expect(envelope.recoverable).toBe(false);
		expect(envelope.status_code).toBe("error");
		expect(envelope.context).toEqual({
			causation_id: null,
			route: null,
			request_id: null,
			response_id: null,
			dom_id: null,
			phase: null,
		});
	});

	test("the envelope always carries a derived friendly tier", () => {
		const received = captureSink();

		reportSystemError(
			baseReport({
				id: "runtime.student_code_failed",
				severity: "info",
				error: new Error("NameError: name 'x' is not defined"),
			}),
		);

		const envelope = received[0].error;
		expect(envelope.friendly_message).toBe(
			"Your code started running but stopped because of an error.",
		);
		expect(envelope.friendly_steps?.[0]).toBe(
			"Check for misspelled variable or function names.",
		);
	});

	test("report-supplied friendly text is copied into the envelope", () => {
		const received = captureSink();

		reportSystemError(
			baseReport({
				severity: "info",
				friendlyMessage: "A plain explanation.",
				friendlySteps: ["First do this.", "Then do that."],
			}),
		);

		const envelope = received[0].error;
		expect(envelope.friendly_message).toBe("A plain explanation.");
		expect(envelope.friendly_steps).toEqual([
			"First do this.",
			"Then do that.",
		]);
	});

	test("missing report.error falls back to the message for details", () => {
		const received = captureSink();

		reportSystemError(
			baseReport({ message: "Something odd", severity: "info" }),
		);

		const envelope = received[0].error;
		// normalizeSystemError(new Error("Something odd")) => name "Error"
		expect(envelope.details).toBe("Error: Something odd");
		expect(envelope.message).toBe("Something odd");
	});

	test("traceback is null when the error has no stack", () => {
		const received = captureSink();
		const bare = new Error("no stack");
		(bare as { stack?: string }).stack = undefined;

		reportSystemError(baseReport({ severity: "info", error: bare }));

		expect(received[0].error.traceback).toBeNull();
	});

	test("partial context: missing keys become null", () => {
		const received = captureSink();

		reportSystemError(
			baseReport({
				severity: "info",
				context: { route: "index", request_id: 3 },
			}),
		);

		expect(received[0].error.context).toEqual({
			causation_id: null,
			route: "index",
			request_id: 3,
			response_id: null,
			dom_id: null,
			phase: null,
		});
	});
});

describe("telemetry record metadata and correlation", () => {
	test("record kind is the envelope id, source and version are fixed", () => {
		const received = captureSink();

		reportSystemError(baseReport({ severity: "info" }));

		const record = received[0];
		expect(record.kind).toBe("runtime.test_error");
		expect(record.metadata.source).toBe("js.bridge.engine");
		expect(record.metadata.version).toBe("0.0.1");
		expect(Number.isNaN(Date.parse(record.metadata.timestamp))).toBe(false);
	});

	test("synthetic metadata ids are negative and strictly decreasing", () => {
		const received = captureSink();

		reportSystemError(baseReport({ id: "runtime.first", severity: "info" }));
		reportSystemError(baseReport({ id: "runtime.second", severity: "info" }));

		expect(received[0].metadata.id).toBeLessThan(0);
		expect(received[1].metadata.id).toBeLessThan(received[0].metadata.id);
	});

	test.each([
		["critical", "error"],
		["error", "error"],
		["warning", "warning"],
		["info", "info"],
	] as const)(
		"severity %s maps to metadata level %s",
		(severity, expectedLevel) => {
			const received = captureSink();

			reportSystemError(
				baseReport({ severity, presentation: "log" }),
			);

			expect(received[0].metadata.level).toBe(expectedLevel);
			expect(received[0].error.severity).toBe(severity);
		},
	);

	test("correlation copies context fields, leaving absent ones undefined", () => {
		const received = captureSink();

		reportSystemError(
			baseReport({
				severity: "info",
				context: { route: "index", dom_id: "root", phase: "setup" },
			}),
		);

		const correlation = received[0].correlation;
		expect(correlation.route).toBe("index");
		expect(correlation.dom_id).toBe("root");
		expect(correlation.request_id).toBeUndefined();
		expect(correlation.response_id).toBeUndefined();
		// The correlation record has no phase field (phase lives only in
		// the envelope context).
		expect(received[0].error.context.phase).toBe("setup");
	});

	test("sink receives the event even for root-rendered errors", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		const received = captureSink();

		reportSystemError(baseReport({ severity: "critical" }));

		expect(received).toHaveLength(1);
		expect(
			document.querySelector(".drafter-system-error"),
		).not.toBeNull();
	});
});

describe("presentation policy matrix", () => {
	// | severity | recoverable | presentation |
	// |----------|-------------|--------------|
	// | critical | any         | root         |
	// | error    | false       | root         |
	// | error    | true        | dialog       |
	// | warning  | any         | log only     |
	// | info     | any         | log only     |
	test.each([
		["critical", false, "root"],
		["critical", true, "root"],
		["error", false, "root"],
		["error", true, "dialog"],
		["warning", false, "log"],
		["warning", true, "log"],
		["info", false, "log"],
		["info", true, "log"],
	] as const)(
		"severity=%s recoverable=%s surfaces via %s",
		(severity, recoverable, surface) => {
			document.body.innerHTML = '<div id="drafter-root--"></div>';
			const received = captureSink();

			reportSystemError(
				baseReport({
					// Unique id per case so dialog symbolicId reuse cannot
					// cross-contaminate table rows.
					id: `runtime.matrix_${severity}_${recoverable}`,
					severity,
					recoverable,
				}),
			);

			const rootError = document.querySelector(".drafter-system-error");
			const dialog = document.querySelector(".drafter-dialog");
			if (surface === "root") {
				expect(rootError).not.toBeNull();
				expect(dialog).toBeNull();
			} else if (surface === "dialog") {
				expect(rootError).toBeNull();
				expect(dialog).not.toBeNull();
			} else {
				expect(rootError).toBeNull();
				expect(dialog).toBeNull();
			}
			// The sink is always notified regardless of presentation mode.
			expect(received).toHaveLength(1);
		},
	);

	test("explicit presentation 'log' suppresses rendering even for critical", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError(
			baseReport({ severity: "critical", presentation: "log" }),
		);

		expect(document.querySelector(".drafter-system-error")).toBeNull();
		expect(document.querySelector(".drafter-dialog")).toBeNull();
	});

	test("explicit presentation 'dialog' overrides the root policy", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError(
			baseReport({
				id: "runtime.explicit_dialog",
				severity: "critical",
				presentation: "dialog",
			}),
		);

		expect(document.querySelector(".drafter-system-error")).toBeNull();
		expect(document.querySelector(".drafter-dialog")).not.toBeNull();
	});

	test("explicit presentation 'root' overrides the log policy for warnings", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError(
			baseReport({ severity: "warning", presentation: "root" }),
		);

		expect(document.querySelector(".drafter-system-error")).not.toBeNull();
	});

	test("presentation 'auto' follows the policy matrix", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError(
			baseReport({ severity: "critical", presentation: "auto" }),
		);

		expect(document.querySelector(".drafter-system-error")).not.toBeNull();
	});

	test("root presentation falls back to a dialog when the root is missing", () => {
		// No #drafter-root-- in the document at all.
		reportSystemError(
			baseReport({ id: "runtime.no_root_fallback", severity: "critical" }),
		);

		expect(document.querySelector(".drafter-dialog")).not.toBeNull();
	});

	test("root render targets a custom rootElementId", () => {
		document.body.innerHTML =
			'<div id="drafter-root--"></div><div id="custom-root"></div>';

		reportSystemError(
			baseReport({ severity: "critical", rootElementId: "custom-root" }),
		);

		expect(
			document
				.getElementById("custom-root")
				?.querySelector(".drafter-system-error"),
		).not.toBeNull();
		expect(
			document
				.getElementById("drafter-root--")
				?.querySelector(".drafter-system-error"),
		).toBeNull();
	});

	test("root render targets an alternate document (embedded instances)", () => {
		const otherDocument = document.implementation.createHTMLDocument("frame");
		const root = otherDocument.createElement("div");
		root.id = "drafter-root--";
		otherDocument.body.appendChild(root);
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		reportSystemError(
			baseReport({ severity: "critical", targetDocument: otherDocument }),
		);

		expect(root.querySelector(".drafter-system-error")).not.toBeNull();
		expect(document.querySelector(".drafter-system-error")).toBeNull();
	});

	test("root render replaces any existing root content", () => {
		document.body.innerHTML =
			'<div id="drafter-root--"><p id="old-content">old</p></div>';

		reportSystemError(baseReport({ severity: "critical" }));

		expect(document.getElementById("old-content")).toBeNull();
		expect(document.querySelector(".drafter-system-error")).not.toBeNull();
	});

	test("reportSystemError returns the normalized error", () => {
		const thrown = new Error("returned");
		const result = reportSystemError(
			baseReport({ severity: "info", error: thrown }),
		);
		expect(result).toBe(thrown);

		const wrapped = reportSystemError(
			baseReport({ severity: "info", error: "stringy" }),
		);
		expect(wrapped).toBeInstanceOf(Error);
		expect(wrapped.message).toBe("stringy");
	});

	test("mirrors every report to console.error", () => {
		reportSystemError(baseReport({ severity: "info" }));

		expect(consoleErrorSpy).toHaveBeenCalledWith(
			"[Drafter System Error] runtime.test_error:",
			"Test failure message",
			undefined,
		);
	});
});

describe("student-facing root rendering", () => {
	function renderToRoot(overrides: Partial<SystemErrorReport>) {
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		reportSystemError(baseReport({ severity: "critical", ...overrides }));
		const container = document.querySelector(".drafter-system-error");
		expect(container).not.toBeNull();
		return container as HTMLElement;
	}

	test("renders the standard structure with the student heading", () => {
		const container = renderToRoot({ message: "It broke" });

		expect(container.querySelector("h1")?.textContent).toBe(
			"Something Went Wrong",
		);
		expect(container.textContent).toContain("What to try next:");
		expect(container.textContent).toContain("Message: It broke");
		expect(container.querySelector("h2")?.textContent).toBe(
			"Technical Details",
		);
	});

	test.each([
		[
			"runtime.pyodide_setup_failed",
			"runtime",
			"Drafter could not finish setting up Python in the browser.",
		],
		[
			"runtime.package_load_failed",
			"runtime",
			"Drafter had trouble loading one of the Python packages your code needs.",
		],
		[
			"runtime.student_code_failed",
			"runtime",
			"Your code started running but stopped because of an error.",
		],
		[
			"runtime.other_problem",
			"runtime",
			"A runtime problem interrupted your program before it could finish.",
		],
		[
			"config.bad_setting",
			"config",
			"Something went wrong while Drafter was running your project.",
		],
	] as const)(
		"lead paragraph for id=%s category=%s",
		(id, category, expectedLead) => {
			const container = renderToRoot({ id, category });
			const lead = container.querySelectorAll("p")[0];
			expect(lead.textContent).toBe(expectedLead);
		},
	);

	test("SyntaxError advice steps when the error is a SyntaxError", () => {
		const container = renderToRoot({
			error: new SyntaxError("invalid syntax"),
		});

		const steps = Array.from(container.querySelectorAll("li")).map(
			(li) => li.textContent,
		);
		expect(steps).toEqual([
			"Open the file and line shown in the traceback or stack details.",
			"Check punctuation first: missing colons, commas, quotes, or parentheses.",
			"Run your code again after fixing one syntax issue at a time.",
		]);
	});

	test("NameError advice steps when a Python NameError appears in the message", () => {
		const container = renderToRoot({
			message: "Error running student code",
			error: new Error("NameError: name 'total' is not defined"),
		});

		const steps = Array.from(container.querySelectorAll("li")).map(
			(li) => li.textContent,
		);
		expect(steps).toEqual([
			"Check for misspelled variable or function names.",
			"Make sure names are defined before they are used.",
			"Check capitalization because names are case-sensitive.",
		]);
	});

	test("SyntaxError advice wins when both SyntaxError and NameError appear", () => {
		const container = renderToRoot({
			error: new Error("SyntaxError before a NameError mention"),
		});

		expect(container.querySelector("li")?.textContent).toContain(
			"traceback or stack details",
		);
	});

	test("report-supplied friendly text overrides the derived lead and steps", () => {
		const container = renderToRoot({
			error: new SyntaxError("invalid syntax"),
			friendlyMessage: "Python could not read one of your lines.",
			friendlySteps: ["Check line 3 of your file."],
		});

		const lead = container.querySelectorAll("p")[0];
		expect(lead.textContent).toBe("Python could not read one of your lines.");
		const steps = Array.from(container.querySelectorAll("li")).map(
			(li) => li.textContent,
		);
		expect(steps).toEqual(["Check line 3 of your file."]);
	});

	test("backtick fragments in steps render as inline code", () => {
		const container = renderToRoot({
			friendlySteps: ["Use the `in` operator before indexing."],
		});

		const item = container.querySelector("li");
		expect(item?.querySelector("code")?.textContent).toBe("in");
		expect(item?.textContent).toBe("Use the in operator before indexing.");
	});

	test("generic steps lead with the suggestion (custom and default)", () => {
		const custom = renderToRoot({
			error: new Error("plain failure"),
			suggestion: "Try turning it off and on again.",
		});
		const customSteps = Array.from(custom.querySelectorAll("li")).map(
			(li) => li.textContent,
		);
		expect(customSteps[0]).toBe("Try turning it off and on again.");
		expect(customSteps[2]).toContain("share the Error ID");

		const fallback = renderToRoot({ error: new Error("plain failure") });
		expect(fallback.querySelector("li")?.textContent).toBe(
			"Please show this to your instructor for more help.",
		);
	});

	test("technical details block lists the envelope fields", () => {
		const container = renderToRoot({
			id: "runtime.details_check",
			message: "Detailed failure",
			error: new TypeError("cannot read"),
			recoverable: false,
		});

		const details = container.querySelector("pre")?.textContent ?? "";
		expect(details).toContain("Error ID: runtime.details_check");
		expect(details).toContain("Category: runtime");
		expect(details).toContain("Severity: critical");
		expect(details).toContain("Recoverable: false");
		expect(details).toContain("Message: Detailed failure");
		expect(details).toContain("TypeError: cannot read");
	});
});

describe("dialog presentation contents", () => {
	test("dialog shows message, suggestion, and technical details", () => {
		reportSystemError(
			baseReport({
				id: "runtime.dialog_contents",
				message: "Recoverable trouble",
				severity: "error",
				recoverable: true,
				suggestion: "Retry the request.",
				error: new Error("transient"),
			}),
		);

		const dialog = document.querySelector(".drafter-dialog");
		expect(dialog).not.toBeNull();
		expect(
			dialog?.querySelector(".drafter-dialog-title")?.textContent,
		).toBe("System Error");
		const content =
			dialog?.querySelector(".drafter-dialog-content")?.textContent ?? "";
		expect(content).toContain("Recoverable trouble");
		expect(content).toContain("What to try:");
		expect(content).toContain("Retry the request.");
		expect(content).toContain("Technical details:");
		expect(content).toContain("Error ID: runtime.dialog_contents");
		expect(content).toContain("Error: transient");
	});

	test("dialog uses the report title when given", () => {
		reportSystemError(
			baseReport({
				id: "runtime.dialog_title",
				severity: "error",
				recoverable: true,
				title: "Custom Title",
			}),
		);

		expect(
			document.querySelector(".drafter-dialog-title")?.textContent,
		).toBe("Custom Title");
	});
});

describe("clearDrafterSiteRoot", () => {
	test("empties the default root element", () => {
		document.body.innerHTML =
			'<div id="drafter-root--"><span>stale</span></div>';

		clearDrafterSiteRoot();

		expect(document.getElementById("drafter-root--")?.innerHTML).toBe("");
	});

	test("empties a custom root in a custom document", () => {
		const otherDocument = document.implementation.createHTMLDocument("x");
		const root = otherDocument.createElement("div");
		root.id = "my-root";
		root.innerHTML = "<b>old</b>";
		otherDocument.body.appendChild(root);

		clearDrafterSiteRoot("my-root", otherDocument);

		expect(root.innerHTML).toBe("");
	});

	test("throws when the root element does not exist", () => {
		expect(() => clearDrafterSiteRoot("nope")).toThrow(
			"Element with ID nope not found",
		);
	});
});
