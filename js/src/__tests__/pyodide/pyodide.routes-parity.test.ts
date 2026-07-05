/**
 * Pyodide parity tests derived from routes.test.ts scenarios.
 */

import { describe, test, expect, beforeAll, beforeEach } from "@jest/globals";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { runStudentCode } from "../../pyodide.index";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "./pyodide-test-harness";

const FIRST_CODE = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Hello world!",
        Button("Second", second)
    ])

@route
def second(state: int):
    return Page(state, [
        "The next page",
        Button("Back", index)
    ])

start_server(0)
`;

const SECOND_CODE = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "This button should not work!",
        Button("Second", "second")
    ])

start_server(0)
`;

const THIRD_CODE = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Third app here!",
        Button("Second", second)
    ])

@route
def second(state: int):
    return Page(state, [
        "Did we overwrite the original?",
        Button("Back", index)
    ])

start_server(0)
`;

describe("Pyodide Routes Parity", () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});

	test("can load applications", async () => {
		await runStudentCode({
			code: FIRST_CODE,
			presentErrors: false,
		});
		expect(true).toBe(true);

		await resetPyodideDrafterRuntime();
		await runStudentCode({
			code: SECOND_CODE,
			presentErrors: false,
		});
		expect(true).toBe(true);
	});

	test("second application run resets system", async () => {
		await runStudentCode({
			code: FIRST_CODE,
			presentErrors: false,
		});
		const drafterBody = document.querySelector("#drafter-body--");
		expect(drafterBody).not.toBeNull();
		const app = within(drafterBody as HTMLElement);

		const button = await app.findByRole("button", { name: /second/i });
		await userEvent.click(button);
		await app.findByText(/the next page/i);

		await resetPyodideDrafterRuntime();
		await runStudentCode({
			code: SECOND_CODE,
			presentErrors: false,
		});
		let drafterBody2 = document.querySelector("#drafter-body--");
		expect(drafterBody2).not.toBeNull();
		let app2 = within(drafterBody2 as HTMLElement);
		const button2 = await app2.findByRole("button", { name: /second/i });
		await userEvent.click(button2);
		await app2.findByText(/no route found for URL: second/i);

		await resetPyodideDrafterRuntime();
		await runStudentCode({
			code: THIRD_CODE,
			presentErrors: false,
		});
		drafterBody2 = document.querySelector("#drafter-body--");
		expect(drafterBody2).not.toBeNull();
		app2 = within(drafterBody2 as HTMLElement);

		await app2.findByText(/third app here!/i);
		const button3 = await app2.findByRole("button", { name: /second/i });
		await userEvent.click(button3);
		await app2.findByText(/did we overwrite the original\?/i);
	});
});
