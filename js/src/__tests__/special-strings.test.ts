/**
 * Tests for special string values and edge cases
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Special String Values Tests", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("handles unicode characters", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: {state.message}",
        TextBox("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return index(state)

start_server(State("Hello 👋 World 🌍"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Message:\s*Hello 👋 World 🌍/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        expect(textBox).toHaveValue("Hello 👋 World 🌍");

        await userEvent.clear(textBox);
        await userEvent.type(textBox, "Café ☕ Niño 你好");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Message:\s*Café ☕ Niño 你好/);
    });

    test("handles quotes and apostrophes", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: {state.message}",
        TextBox("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return index(state)

start_server(State("It's a \"wonderful\" day!"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Message:\s*It's a "wonderful" day!/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        expect(textBox).toHaveValue('It\'s a "wonderful" day!');

        await userEvent.clear(textBox);
        await userEvent.type(textBox, 'She said "Hello" and I said \'Hi\'');
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Message:\s*She said "Hello" and I said 'Hi'/);
    });

    test("handles HTML-unsafe characters", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: {state.message}",
        TextBox("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return index(state)

start_server(State("<script>alert('test')</script>"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // The text should be escaped and not executed as HTML
        await app.findByText(/Message:\s*<script>alert\('test'\)<\/script>/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        expect(textBox).toHaveValue("<script>alert('test')</script>");

        await userEvent.clear(textBox);
        await userEvent.type(textBox, "<div>Test & More</div>");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Message:\s*<div>Test & More<\/div>/);
    });

    test("handles empty and whitespace strings", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: [{state.message}]",
        TextBox("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return index(state)

start_server(State(""))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Message:\s*\[\]/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        expect(textBox).toHaveValue("");

        await userEvent.type(textBox, "   spaces   ");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Message:\s*\[\s*spaces\s*\]/);
    });

    test("handles newlines and special escape characters", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: {state.message}",
        TextArea("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return result(state)

@route
def result(state: State):
    return Page(state, [
        "Your message:",
        state.message,
        Button("Back", index),
    ])

start_server(State("Line 1\\nLine 2\\nLine 3"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const textarea = app.getByRole("textbox", { name: /new_message/i });
        expect(textarea).toHaveValue("Line 1\nLine 2\nLine 3");

        await userEvent.clear(textarea);
        await userEvent.type(textarea, "First{Enter}Second{Enter}Third");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        const resultText = await app.findByText(/First/);
        expect(resultText.textContent).toContain("First");
    });

    test("handles very long strings", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Length: {len(state.message)}",
        TextBox("new_message", state.message),
        Button("Update", update),
    ])

@route
def update(state: State, new_message: str):
    state.message = new_message
    return index(state)

start_server(State("A" * 100))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Length:\s*100/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        expect(textBox).toHaveValue("A".repeat(100));

        await userEvent.clear(textBox);
        await userEvent.type(textBox, "B".repeat(50));
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Length:\s*50/);
    });

    test("handles special characters in button arguments", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Message: {state.message}",
        Button("Set Quote", set_message, [Argument("msg", "It's a \\"test\\"")]),
        Button("Set HTML", set_message, [Argument("msg", "<b>Bold</b>")]),
        Button("Set Unicode", set_message, [Argument("msg", "Hello 世界")]),
    ])

@route
def set_message(state: State, msg: str):
    state.message = msg
    return index(state)

start_server(State("Initial"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Message:\s*Initial/);

        await userEvent.click(
            await app.findByRole("button", { name: /set quote/i })
        );
        await app.findByText(/Message:\s*It's a "test"/);

        await userEvent.click(
            await app.findByRole("button", { name: /set html/i })
        );
        await app.findByText(/Message:\s*<b>Bold<\/b>/);

        await userEvent.click(
            await app.findByRole("button", { name: /set unicode/i })
        );
        await app.findByText(/Message:\s*Hello 世界/);
    });
});
