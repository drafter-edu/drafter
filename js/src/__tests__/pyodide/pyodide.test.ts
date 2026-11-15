/**
 * Basic unit tests for TypeScript client functionality
 */

import {
	afterEach,
	beforeAll,
	beforeEach,
	describe,
	test,
	expect,
	jest,
} from "@jest/globals";

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

describe(`Simple Drafter Application`, () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});
	test(`can load application`, () => {
		return runStudentCode({
			code: SIMPLE_STUDENT_CODE,
			presentErrors: false,
		})
			.then((mod) => {
				// If we reach here, the student code ran successfully
				// expect(mod.$d.index).toBeDefined();
				expect(true).toBe(true);
			})
			.catch((err) => {
				// If there was an error, fail the test
				// expect(err).toBeUndefined();
				throw err;
			});
	});

	test(`can interact with application`, async () => {
		await runStudentCode({
			code: SIMPLE_STUDENT_CODE,
			presentErrors: false,
		});
		const drafterBody = await document.querySelector("#drafter-body--");
		expect(drafterBody).not.toBeNull();
		const app = within(drafterBody as HTMLElement);

		// Simulate clicking the "Plus One" button
		const button = await app.findByRole("button", { name: /plus one/i });

		await userEvent.click(button);
		// Check that the counter has been updated
		await app.findByText(/Counter:\s*1/);

		// Update the text box and checkbox
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

const INPUT_STUDENT_CODE = `
from drafter import *

hide_debug_information()

@route
def index(state: str):
    return Page(state, [
        "Nobody has answered yet.",
        Button("Ask", ask),
    ])

@route
def ask(state: str):
    answer = input("What is your name? ")
    return Page(state, [f"The answer was [{answer}]"])

start_server("")
`;

describe("input() in a route", () => {
	let promptSpy: ReturnType<typeof jest.spyOn>;

	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
		promptSpy = jest.spyOn(window, "prompt");
	});

	afterEach(() => {
		promptSpy.mockRestore();
	});

	async function clickAsk(): Promise<ReturnType<typeof within>> {
		await runStudentCode({ code: INPUT_STUDENT_CODE, presentErrors: false });
		const app = within(
			document.querySelector("#drafter-body--") as HTMLElement,
		);
		await userEvent.click(await app.findByRole("button", { name: "Ask" }));
		return app;
	}

	test("shows the question in the prompt box and returns the answer", async () => {
		promptSpy.mockReturnValue("Ada");

		const app = await clickAsk();

		await app.findByText("The answer was [Ada]");
		expect(promptSpy).toHaveBeenCalledTimes(1);
		expect(promptSpy).toHaveBeenCalledWith("What is your name? ");
	});

	test("gives an empty string when the prompt box is cancelled", async () => {
		promptSpy.mockReturnValue(null);

		const app = await clickAsk();

		await app.findByText("The answer was []");
		expect(promptSpy).toHaveBeenCalledWith("What is your name? ");
	});
});
