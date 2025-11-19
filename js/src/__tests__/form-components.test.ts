/**
 * Comprehensive tests for form components (TextBox, TextArea, SelectBox, CheckBox)
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Form Components", () => {
    beforeEach(() => {
        // Reset the entire document body to ensure clean state
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    describe("TextBox", () => {
        test("renders and accepts text input", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Current: {state}",
        TextBox("user_input", state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, user_input: str):
    return index(user_input)

start_server("Initial")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            await app.findByText(/Current:\s*Initial/);
            
            const textbox = app.getByRole("textbox", { name: /user_input/i });
            await userEvent.clear(textbox);
            await userEvent.type(textbox, "New text");
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Current:\s*New text/);
        });

        test("handles empty string default", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Value: '{state}'",
        TextBox("input"),
        Button("Submit", submit)
    ])

@route
def submit(state: str, input: str):
    return index(input)

start_server("")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            await app.findByText(/Value:\s*''/);
            
            const textbox = app.getByRole("textbox", { name: /input/i });
            await userEvent.type(textbox, "Hello");
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Value:\s*'Hello'/);
        });

        test("preserves textbox value with default parameter", async () => {
            const code = `
from drafter import *

@dataclass
class State:
    text: str

@route
def index(state: State):
    return Page(state, [
        TextBox("text", state.text),
        Button("Submit", submit)
    ])

@route
def submit(state: State, text: str):
    state.text = text
    return index(state)

start_server(State("Preserved"))
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            const textbox = app.getByRole("textbox", { name: /text/i }) as HTMLInputElement;
            expect(textbox.value).toBe("Preserved");
        });
    });

    describe("TextArea", () => {
        test("renders and accepts multi-line text", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Content: {state}",
        TextArea("content", state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, content: str):
    return index(content)

start_server("Line 1")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            const textarea = app.getByRole("textbox", { name: /content/i });
            await userEvent.clear(textarea);
            await userEvent.type(textarea, "Line 1{enter}Line 2{enter}Line 3");
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            // Note: newlines become \n in display
            await waitFor(() => {
                const text = drafterBody.textContent || "";
                expect(text).toContain("Line 1");
            });
        });

        test("handles long text content", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        TextArea("long_text", state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, long_text: str):
    return Page(long_text, [f"Length: {len(long_text)}"])

start_server("")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            const textarea = app.getByRole("textbox", { name: /long_text/i });
            const longText = "A".repeat(100);
            await userEvent.type(textarea, longText);
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Length:\s*100/);
        });
    });

    describe("CheckBox", () => {
        test("renders and toggles boolean value", async () => {
            const code = `
from drafter import *

@route
def index(state: bool):
    return Page(state, [
        f"Checked: {state}",
        CheckBox("enabled", state),
        Button("Submit", submit)
    ])

@route
def submit(state: bool, enabled: bool):
    return index(enabled)

start_server(False)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            await app.findByText(/Checked:\s*False/);
            
            const checkbox = app.getByRole("checkbox", { name: /enabled/i }) as HTMLInputElement;
            expect(checkbox.checked).toBe(false);
            
            await userEvent.click(checkbox);
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Checked:\s*True/);
        });

        test("preserves checked state", async () => {
            const code = `
from drafter import *

@dataclass
class State:
    checked: bool

@route
def index(state: State):
    return Page(state, [
        CheckBox("checked", state.checked),
        Button("Submit", submit)
    ])

@route
def submit(state: State, checked: bool):
    state.checked = checked
    return index(state)

start_server(State(True))
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            const checkbox = app.getByRole("checkbox", { name: /checked/i }) as HTMLInputElement;
            expect(checkbox.checked).toBe(true);
        });
    });

    describe("SelectBox", () => {
        test("renders dropdown with options", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Selected: {state}",
        SelectBox("choice", ["apple", "banana", "cherry"], state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, choice: str):
    return index(choice)

start_server("apple")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            await app.findByText(/Selected:\s*apple/);
            
            const select = app.getByRole("combobox", { name: /choice/i });
            await userEvent.selectOptions(select, "banana");
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Selected:\s*banana/);
        });

        test("handles numeric options", async () => {
            const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Selected: {state}",
        SelectBox("number", ["1", "2", "3", "4", "5"], state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, number: str):
    return index(number)

start_server("1")
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            const select = app.getByRole("combobox", { name: /number/i });
            await userEvent.selectOptions(select, "5");
            await userEvent.click(await app.findByRole("button", { name: /submit/i }));
            
            await app.findByText(/Selected:\s*5/);
        });
    });

    describe("Combined Form Components", () => {
        test("handles multiple form inputs together", async () => {
            const code = `
from drafter import *

@dataclass
class State:
    name: str
    email: str
    subscribe: bool
    preference: str

@route
def index(state: State):
    return Page(state, [
        f"Name: {state.name}",
        f"Email: {state.email}",
        f"Subscribe: {state.subscribe}",
        f"Preference: {state.preference}",
        TextBox("name", state.name),
        TextBox("email", state.email),
        CheckBox("subscribe", state.subscribe),
        SelectBox("preference", ["daily", "weekly", "monthly"], state.preference),
        Button("Update", update)
    ])

@route
def update(state: State, name: str, email: str, subscribe: bool, preference: str):
    state.name = name
    state.email = email
    state.subscribe = subscribe
    state.preference = preference
    return index(state)

start_server(State("John", "john@example.com", False, "daily"))
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            const app = within(drafterBody);

            // Update all fields
            const nameBox = app.getByRole("textbox", { name: /name/i });
            await userEvent.clear(nameBox);
            await userEvent.type(nameBox, "Jane");

            const emailBox = app.getByRole("textbox", { name: /email/i });
            await userEvent.clear(emailBox);
            await userEvent.type(emailBox, "jane@example.com");

            const checkbox = app.getByRole("checkbox", { name: /subscribe/i });
            await userEvent.click(checkbox);

            const select = app.getByRole("combobox", { name: /preference/i });
            await userEvent.selectOptions(select, "weekly");

            await userEvent.click(await app.findByRole("button", { name: /update/i }));

            // Verify all updates
            await app.findByText(/Name:\s*Jane/);
            await app.findByText(/Email:\s*jane@example\.com/);
            await app.findByText(/Subscribe:\s*True/);
            await app.findByText(/Preference:\s*weekly/);
        });
    });
});
