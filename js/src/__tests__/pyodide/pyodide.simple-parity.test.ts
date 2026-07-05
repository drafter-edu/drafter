/**
 * Pyodide parity tests derived from simple.test.ts scenarios.
 */

import { describe, test, expect, beforeAll, beforeEach } from "@jest/globals";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { runStudentCode } from "../../pyodide.index";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "./pyodide-test-harness";

const SIMPLE_STUDENT_CODE = `
from drafter import *

hide_debug_information()

@dataclass
class State:
    counter: int
    message: str
    flag: bool

@route
def index(state: State):
    return Page(state, [
        "Hello world!",
        f"Counter: {state.counter}",
        f"Message: {state.message}",
        f"Flag is {'on' if state.flag else 'off'}",
        Button("Plus One", plus_one),
        TextBox("new_message", state.message),
        CheckBox("flag", state.flag),
    ])

@route
def plus_one(state: State, new_message: str, flag: bool):
    state.counter += 1
    state.message = new_message
    state.flag = flag
    return index(state)

start_server(State(0, "Welcome to Drafter!", True))
`;

describe("Simple Drafter Application (Pyodide parity)", () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});

	test("can load application", async () => {
		await runStudentCode({
			code: SIMPLE_STUDENT_CODE,
			presentErrors: false,
		});
		expect(true).toBe(true);
	});

	test("can interact with application", async () => {
		await runStudentCode({
			code: SIMPLE_STUDENT_CODE,
			presentErrors: false,
		});
		const drafterBody = document.querySelector("#drafter-body--");
		expect(drafterBody).not.toBeNull();
		const app = within(drafterBody as HTMLElement);

		const button = await app.findByRole("button", { name: /plus one/i });
		await userEvent.click(button);
		await app.findByText(/Counter:\s*1/);

		const textBox = app.getByRole("textbox", { name: /new_message/i });
		expect(textBox).not.toBeNull();
		await userEvent.clear(textBox);
		await userEvent.type(textBox, "Updated message");
		await userEvent.click(
			await app.findByRole("button", { name: /plus one/i }),
		);
		await app.findByText(/Message:\s*Updated message/);

		const checkbox = app.getByRole("checkbox", { name: /flag/i });
		await userEvent.click(checkbox);
		await userEvent.click(
			await app.findByRole("button", { name: /plus one/i }),
		);
		await app.findByText(/Flag is off/);
	});
});
