/**
 * Pyodide parity tests derived from skulpt.test.ts scenarios.
 */

import { describe, test, expect, beforeAll, beforeEach } from "@jest/globals";
import { runStudentCode } from "../pyodide.index";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "./pyodide-test-harness";

describe("TypeScript Client Basic Tests (Pyodide parity)", () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});

	test("basic test infrastructure works", () => {
		expect(true).toBe(true);
	});

	test("pyodide is loaded", () => {
		expect(typeof (window as any).pyodide).toBe("object");
	});

	test("can run pyodide", async () => {
		const pyodide = (window as Record<string, any>).pyodide;
		const message = pyodide.runPython(
			'message = "Hello, Pyodide!"\nmessage',
		);
		expect(message).toBe("Hello, Pyodide!");
	});

	test("can import drafter in pyodide", async () => {
		const pyodide = (window as Record<string, any>).pyodide;
		await expect(
			pyodide.runPythonAsync("import drafter"),
		).resolves.toBeUndefined();
	});

	test("can catch a Pyodide error", async () => {
		const pyodide = (window as Record<string, any>).pyodide;
		await expect(
			pyodide.runPythonAsync('raise ValueError("This is a test error")'),
		).rejects.toThrow("This is a test error");
	});

	test("can run a student code example", async () => {
		const code = `
from drafter import *

@route
def index():
    return Page(None, ["Hello world!"])

start_server()
`;

		await runStudentCode({ code, presentErrors: false });

		const drafterBody = document.querySelector("#drafter-body--");
		expect(drafterBody).not.toBeNull();
		expect(drafterBody?.textContent).toContain("Hello world!");
	});

	test("bad student code throws an error", async () => {
		const code = `
from drafter import *

@route
def index():
    1 + ""  # This will raise a TypeError
    return Page(None, ["Hello world!"])

start_server()
`;

		await runStudentCode({ code, presentErrors: false });

		const drafterBody = document.querySelector("#drafter-body--");
		expect(drafterBody?.textContent).toContain("An error has occurred");
	});
});
