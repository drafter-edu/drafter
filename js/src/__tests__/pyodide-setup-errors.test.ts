/**
 * What a student sees when Pyodide itself cannot be set up.
 *
 * A download that never arrives (offline, a blocked CDN, or a stale cached
 * Drafter bundle asking the CDN for a file that no longer exists) used to
 * surface as a bare "TypeError: Failed to fetch dynamically imported
 * module: ..." with generic advice. setupPyodide now explains it as a
 * download problem. The loader is mocked at the `pyodide` package boundary
 * (the shim forwards to `__realLoadPyodide`), so no interpreter is needed.
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

import { setSystemErrorSink, type ErrorTelemetryRecord } from "../bridge/engine";
import { setupPyodide } from "../pyodide.index";

type AnyWindow = Record<string, any>;

const CDN_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.5/full";
const DOWNLOAD_LEAD =
	"Drafter could not download the files it needs to run Python in your browser. This is a connection or browser problem, not a mistake in your code.";
const GENERIC_LEAD =
	"Drafter could not finish setting up Python in the browser.";

// reportSystemError always mirrors to console.error; keep test output clean.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});

let received: ErrorTelemetryRecord[];

function failLoaderWith(error: unknown): void {
	(globalThis as AnyWindow).__realLoadPyodide = jest.fn(() =>
		Promise.reject(error),
	);
}

async function runFailingSetup(pyodideUrl: string): Promise<unknown> {
	try {
		await setupPyodide({ pyodideUrl, systemPackages: [] });
	} catch (error) {
		return error;
	}
	throw new Error("setupPyodide was expected to fail");
}

function renderedLead(): string | null {
	return (
		document.querySelector(".drafter-system-error p")?.textContent ?? null
	);
}

function renderedSteps(): string[] {
	return Array.from(
		document.querySelectorAll(".drafter-system-error li"),
	).map((item) => item.textContent ?? "");
}

beforeEach(() => {
	delete (window as AnyWindow).pyodide;
	document.body.innerHTML = '<div id="drafter-root--"></div>';
	received = [];
	setSystemErrorSink((event) => received.push(event));
});

afterEach(() => {
	delete (globalThis as AnyWindow).__realLoadPyodide;
	delete (window as AnyWindow).pyodide;
	setSystemErrorSink(null);
	document.body.innerHTML = "";
	consoleErrorSpy.mockClear();
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
});

describe("setupPyodide download failures", () => {
	test("a missing runtime file is explained as a download problem", async () => {
		// The exact failure from the stale-bundle bug report.
		const original = new TypeError(
			`Failed to fetch dynamically imported module: ${CDN_URL}/pyodide.asm.js`,
		);
		failLoaderWith(original);

		const thrown = await runFailingSetup(CDN_URL);

		expect(thrown).toBe(original);
		expect(renderedLead()).toBe(DOWNLOAD_LEAD);
		const steps = renderedSteps();
		expect(steps).toHaveLength(3);
		expect(steps[0]).toContain("connected to the internet");
		expect(steps[1]).toContain("hard refresh (Ctrl+Shift+R");
		expect(steps[2]).toContain("may be blocking cdn.jsdelivr.net");
		// The host is rendered as code, never as markup from the error text.
		expect(
			document.querySelector(".drafter-system-error li code")?.textContent,
		).toBe("cdn.jsdelivr.net");
		// The raw error stays available for whoever helps the student.
		expect(
			document.querySelector(".drafter-system-error pre")?.textContent,
		).toContain(original.message);
	});

	test("the debug panel envelope carries the same explanation", async () => {
		failLoaderWith(new TypeError("Failed to fetch"));

		await runFailingSetup(CDN_URL);

		expect(received).toHaveLength(1);
		const envelope = received[0].error;
		expect(envelope.id).toBe("runtime.pyodide_setup_failed");
		expect(envelope.friendly_message).toBe(DOWNLOAD_LEAD);
		expect(envelope.friendly_steps).toHaveLength(3);
		expect(envelope.details).toBe("TypeError: Failed to fetch");
	});

	test.each([
		["Chrome fetch", "Failed to fetch"],
		[
			"Firefox dynamic import",
			`error loading dynamically imported module: ${CDN_URL}/pyodide.asm.mjs`,
		],
		["Firefox fetch", "NetworkError when attempting to fetch resource."],
		["Safari dynamic import", "Importing a module script failed."],
		["Safari fetch", "Load failed"],
		[
			"Pyodide file request",
			`Failed to load '${CDN_URL}/python_stdlib.zip': request failed.`,
		],
		["micropip", "Can't fetch wheel from 'https://files.pythonhosted.org/x.whl'"],
	])("recognizes the %s wording", async (_label, message) => {
		failLoaderWith(new TypeError(message));

		await runFailingSetup(CDN_URL);

		expect(renderedLead()).toBe(DOWNLOAD_LEAD);
	});

	test("names the server from the error over the configured one", async () => {
		failLoaderWith(
			new Error("Can't fetch wheel from 'https://files.pythonhosted.org/x.whl'"),
		);

		await runFailingSetup(CDN_URL);

		expect(renderedSteps()[2]).toContain(
			"may be blocking files.pythonhosted.org",
		);
	});

	test("falls back to the configured Pyodide server", async () => {
		failLoaderWith(new TypeError("Failed to fetch"));

		await runFailingSetup(CDN_URL);

		expect(renderedSteps()[2]).toContain("may be blocking cdn.jsdelivr.net");
	});

	test("names no server when Pyodide is served alongside the site", async () => {
		failLoaderWith(new TypeError("Failed to fetch"));

		await runFailingSetup("/pyodide/");

		expect(renderedSteps()[2]).toContain("may be blocking the download");
		expect(document.querySelector(".drafter-system-error li code")).toBeNull();
	});
});

describe("setupPyodide other failures", () => {
	test("keep the generic setup explanation", async () => {
		failLoaderWith(new Error("wasm instantiation failed!"));

		await runFailingSetup(CDN_URL);

		expect(renderedLead()).toBe(GENERIC_LEAD);
		expect(renderedSteps().join(" ")).not.toContain("hard refresh");
	});
});
