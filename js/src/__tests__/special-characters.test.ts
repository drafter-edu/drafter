/**
 * Comprehensive tests for special characters, Unicode, and HTML escaping in Drafter
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Special Characters and Unicode", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    test("handles Unicode characters in text", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "Unicode: 你好世界 🌍 Привет мир",
        Button("Next", page2)
    ])

@route
def page2(state: str):
    return Page(state, ["Emojis: 😀 🎉 🚀 ❤️ 🌈"])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Unicode: 你好世界 🌍 Привет мир/);
        await userEvent.click(await app.findByRole("button", { name: /next/i }));
        await app.findByText(/Emojis: 😀 🎉 🚀 ❤️ 🌈/);
    });

    test("handles special HTML characters correctly", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "Less than: <",
        "Greater than: >",
        "Ampersand: &",
        "Quote: \\"",
        "Apostrophe: '",
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        // These should be properly escaped in the HTML
        expect(drafterBody.textContent).toContain("Less than: <");
        expect(drafterBody.textContent).toContain("Greater than: >");
        expect(drafterBody.textContent).toContain("Ampersand: &");
        expect(drafterBody.textContent).toContain('Quote: "');
        expect(drafterBody.textContent).toContain("Apostrophe: '");
    });

    test("handles Unicode in state and form inputs", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Current: {state}",
        TextBox("text", state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, text: str):
    return index(text)

start_server("初期値")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Current: 初期値/);
        
        const textbox = app.getByRole("textbox", { name: /text/i });
        await userEvent.clear(textbox);
        await userEvent.type(textbox, "新しい値 🎌");
        await userEvent.click(await app.findByRole("button", { name: /submit/i }));
        
        await app.findByText(/Current: 新しい値 🎌/);
    });

    test("handles multi-line text with special characters", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        TextArea("content", state),
        Button("Submit", submit)
    ])

@route
def submit(state: str, content: str):
    return Page(content, [f"Received: {content}"])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        const textarea = app.getByRole("textbox", { name: /content/i });
        await userEvent.type(textarea, "Line 1: Hello & <world>");
        await userEvent.click(await app.findByRole("button", { name: /submit/i }));
        
        await waitFor(() => {
            expect(drafterBody.textContent).toContain("Line 1: Hello & <world>");
        });
    });

    test("handles strings with quotes in dataclass", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    single: str
    double: str
    mixed: str

@route
def index(state: State):
    return Page(state, [
        f"Single: {state.single}",
        f"Double: {state.double}",
        f"Mixed: {state.mixed}"
    ])

start_server(State("It's working", 'He said "hello"', 'Mix: "quote" and \\'apostrophe\\''))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        expect(drafterBody.textContent).toContain("Single: It's working");
        expect(drafterBody.textContent).toContain('Double: He said "hello"');
        expect(drafterBody.textContent).toContain('Mix: "quote" and \'apostrophe\'');
    });

    test("handles newlines and tabs in strings", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    text_with_newlines = "Line 1\\nLine 2\\nLine 3"
    text_with_tabs = "Col1\\tCol2\\tCol3"
    return Page(state, [
        text_with_newlines,
        text_with_tabs
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        expect(drafterBody.textContent).toContain("Line 1");
        expect(drafterBody.textContent).toContain("Line 2");
        expect(drafterBody.textContent).toContain("Line 3");
        expect(drafterBody.textContent).toContain("Col1");
        expect(drafterBody.textContent).toContain("Col2");
        expect(drafterBody.textContent).toContain("Col3");
    });

    test("handles long strings with special characters", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    long_text = "A" * 100 + " special: < > & \\" ' " + "B" * 100
    return Page(state, [
        long_text,
        Button("Count", count)
    ])

@route
def count(state: str):
    return Page(str(len("A" * 100 + " special: < > & \\" ' " + "B" * 100)), ["Done"])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        expect(drafterBody.textContent).toContain("AAAAA");
        expect(drafterBody.textContent).toContain("special: < > &");
        
        await userEvent.click(await app.findByRole("button", { name: /count/i }));
        await app.findByText(/Done/);
    });

    test("handles URL-like strings", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "URL: https://example.com?param=value&other=123",
        "Email: user@example.com",
        "Path: /home/user/documents/file.txt"
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        expect(drafterBody.textContent).toContain("URL: https://example.com?param=value&other=123");
        expect(drafterBody.textContent).toContain("Email: user@example.com");
        expect(drafterBody.textContent).toContain("Path: /home/user/documents/file.txt");
    });

    test("handles mathematical symbols and operators", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "Math: x² + y³ = z⁴",
        "Operators: ≤ ≥ ≠ ≈ ∞",
        "Greek: α β γ δ Σ π",
        "Arrows: → ← ↑ ↓ ⇒ ⇐"
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        expect(drafterBody.textContent).toContain("Math: x² + y³ = z⁴");
        expect(drafterBody.textContent).toContain("Operators: ≤ ≥ ≠ ≈ ∞");
        expect(drafterBody.textContent).toContain("Greek: α β γ δ Σ π");
        expect(drafterBody.textContent).toContain("Arrows: → ← ↑ ↓ ⇒ ⇐");
    });

    test("handles mixed scripts and directions", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "English, 中文, العربية, עברית",
        "Numbers: 123, ١٢٣, ১২৩",
        "Mixed: Hello 世界 مرحبا"
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;

        expect(drafterBody.textContent).toContain("English, 中文, العربية, עברית");
        expect(drafterBody.textContent).toContain("Numbers: 123, ١٢٣, ১২৩");
        expect(drafterBody.textContent).toContain("Mixed: Hello 世界 مرحبا");
    });
});
