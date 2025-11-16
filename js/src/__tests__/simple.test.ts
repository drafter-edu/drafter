/**
 * Basic unit tests for TypeScript client functionality
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { builtinRead, setupSkulpt } from "../skulpt-tools.js";
import { runStudentCode } from "../index";
import * as fs from "fs";
import * as path from "path";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

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
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
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
            await app.findByRole("button", { name: /plus one/i })
        );
        await app.findByText(/Message:\s*Updated message/);

        const checkbox = app.getByRole("checkbox", { name: /flag/i });
        await userEvent.click(checkbox);
        await userEvent.click(
            await app.findByRole("button", { name: /plus one/i })
        );
        await app.findByText(/Flag is off/);
    });
});
