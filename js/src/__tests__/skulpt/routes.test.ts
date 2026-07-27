/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../dist/skulpt/skulpt.js";
import "../../../dist/skulpt/skulpt-stdlib.js";
import "../../../dist/skulpt/skulpt-drafter.js";
import "../../../dist/js/drafter.js";
import { runStudentCode, clearDrafterSiteRoot } from "../../skulpt.index.js";
import * as fs from "fs";
import * as path from "path";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

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

describe(`Simple Drafter Application`, () => {
	beforeAll(() => {
		document.body.innerHTML = "<div id='drafter-root--'></div>";
	});
	test(`can load applications`, async () => {
		await runStudentCode({
			code: FIRST_CODE,
			presentErrors: false,
		});
		expect(true).toBe(true);
		await runStudentCode({
			code: SECOND_CODE,
			presentErrors: false,
		});
		expect(true).toBe(true);
	});

	test(`second application run resets system`, async () => {
		await runStudentCode({
			code: FIRST_CODE,
			presentErrors: false,
		});
		const drafterBody = await document.querySelector("#drafter-body--");
		expect(drafterBody).not.toBeNull();
		const app = within(drafterBody as HTMLElement);

		// Simulate clicking the "Second" button
		const button = await app.findByRole("button", { name: /second/i });

		await userEvent.click(button);
		// Check that we are on the second page
		await app.findByText(/the next page/i);

		// Now run the second application
		clearDrafterSiteRoot();
		await runStudentCode({
			code: SECOND_CODE,
			presentErrors: false,
		});
		let drafterBody2 = await document.querySelector("#drafter-body--");
		expect(drafterBody2).not.toBeNull();
		let app2 = within(drafterBody2 as HTMLElement);
		// Page verification rejects the page at render time because its
		// Button points at a route that no longer exists (proving the
		// first app's routes were reset).
		await app2.findByText(/non-existent page `second`/i);

		// Now run the third application
		clearDrafterSiteRoot();
		const module = await runStudentCode({
			code: THIRD_CODE,
			presentErrors: false,
		});
		drafterBody2 = await document.querySelector("#drafter-body--");
		expect(drafterBody2).not.toBeNull();
		app2 = within(drafterBody2 as HTMLElement);

		await app2.findByText(/third app here!/i);

		// Simulate clicking the "Second" button
		const button3 = await app2.findByRole("button", { name: /second/i });

		await userEvent.click(button3);

		// Check that now we are on the second page of the third app
		await app2.findByText(/did we overwrite the original\?/i);
	});
});
