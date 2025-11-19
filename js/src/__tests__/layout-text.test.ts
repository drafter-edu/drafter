/**
 * Comprehensive tests for layout and text components
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Layout and Text Components", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    describe("Header Component", () => {
        test("renders different header levels", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Header("Level 1 Header", 1),
        Header("Level 2 Header", 2),
        Header("Level 3 Header", 3),
        Header("Level 4 Header", 4),
        Header("Level 5 Header", 5),
        Header("Level 6 Header", 6)
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.querySelector("h1")?.textContent).toContain("Level 1 Header");
            expect(drafterBody.querySelector("h2")?.textContent).toContain("Level 2 Header");
            expect(drafterBody.querySelector("h3")?.textContent).toContain("Level 3 Header");
            expect(drafterBody.querySelector("h4")?.textContent).toContain("Level 4 Header");
            expect(drafterBody.querySelector("h5")?.textContent).toContain("Level 5 Header");
            expect(drafterBody.querySelector("h6")?.textContent).toContain("Level 6 Header");
        });

        test("default header level is 1", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [Header("Default Header")])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.querySelector("h1")?.textContent).toContain("Default Header");
        });
    });

    describe("Div and Span Components", () => {
        test("renders Div container", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Div([
            "Content inside div",
            "More content"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const divs = drafterBody.querySelectorAll("div");
            let foundContent = false;
            divs.forEach(div => {
                if (div.textContent?.includes("Content inside div")) {
                    foundContent = true;
                }
            });
            expect(foundContent).toBe(true);
        });

        test("renders Span container", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Text with ",
        Span(["styled content"]),
        " and more text"
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Text with styled content and more text");
        });

        test("nested Divs work correctly", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Div([
            "Outer div",
            Div([
                "Inner div",
                Div(["Innermost div"])
            ])
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Outer div");
            expect(drafterBody.textContent).toContain("Inner div");
            expect(drafterBody.textContent).toContain("Innermost div");
        });
    });

    describe("Row Component", () => {
        test("renders Row with multiple items", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Row([
            "Item 1",
            "Item 2",
            "Item 3"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Item 1");
            expect(drafterBody.textContent).toContain("Item 2");
            expect(drafterBody.textContent).toContain("Item 3");
        });
    });

    describe("List Components", () => {
        test("renders BulletedList", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Shopping list:",
        BulletedList([
            "Apples",
            "Bananas",
            "Oranges"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const ul = drafterBody.querySelector("ul");
            expect(ul).not.toBeNull();
            expect(drafterBody.textContent).toContain("Apples");
            expect(drafterBody.textContent).toContain("Bananas");
            expect(drafterBody.textContent).toContain("Oranges");
        });

        test("renders NumberedList", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Steps:",
        NumberedList([
            "First step",
            "Second step",
            "Third step"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const ol = drafterBody.querySelector("ol");
            expect(ol).not.toBeNull();
            expect(drafterBody.textContent).toContain("First step");
            expect(drafterBody.textContent).toContain("Second step");
            expect(drafterBody.textContent).toContain("Third step");
        });

        test("handles nested lists", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        BulletedList([
            "Item 1",
            NumberedList([
                "Sub-item 1",
                "Sub-item 2"
            ]),
            "Item 2"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Item 1");
            expect(drafterBody.textContent).toContain("Sub-item 1");
            expect(drafterBody.textContent).toContain("Sub-item 2");
            expect(drafterBody.textContent).toContain("Item 2");
        });

        test("handles empty lists", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Empty bulleted:",
        BulletedList([]),
        "Empty numbered:",
        NumberedList([])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Empty bulleted:");
            expect(drafterBody.textContent).toContain("Empty numbered:");
        });
    });

    describe("LineBreak and HorizontalRule", () => {
        test("renders LineBreak", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Line 1",
        LineBreak(),
        "Line 2",
        LineBreak(),
        "Line 3"
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const brs = drafterBody.querySelectorAll("br");
            expect(brs.length).toBeGreaterThanOrEqual(2);
            expect(drafterBody.textContent).toContain("Line 1");
            expect(drafterBody.textContent).toContain("Line 2");
            expect(drafterBody.textContent).toContain("Line 3");
        });

        test("renders HorizontalRule", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Section 1",
        HorizontalRule(),
        "Section 2",
        HorizontalRule(),
        "Section 3"
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const hrs = drafterBody.querySelectorAll("hr");
            expect(hrs.length).toBeGreaterThanOrEqual(2);
            expect(drafterBody.textContent).toContain("Section 1");
            expect(drafterBody.textContent).toContain("Section 2");
            expect(drafterBody.textContent).toContain("Section 3");
        });
    });

    describe("Text and PreformattedText", () => {
        test("renders Text component", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Text("Regular text content"),
        Text("More text")
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("Regular text content");
            expect(drafterBody.textContent).toContain("More text");
        });

        test("renders PreformattedText with preserved spacing", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Pre("Line 1\\nLine 2\\n  Indented line")
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            const pre = drafterBody.querySelector("pre");
            expect(pre).not.toBeNull();
            expect(drafterBody.textContent).toContain("Line 1");
            expect(drafterBody.textContent).toContain("Line 2");
        });
    });

    describe("Complex Layouts", () => {
        test("handles complex nested layout structure", async () => {
            const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        Header("My App"),
        Div([
            Row([
                Div([
                    Header("Section 1", 2),
                    BulletedList(["Item 1", "Item 2"])
                ]),
                Div([
                    Header("Section 2", 2),
                    NumberedList(["Step 1", "Step 2"])
                ])
            ]),
            HorizontalRule(),
            "Footer content"
        ])
    ])

start_server(0)
`;
            await runStudentCode({ code, presentErrors: false });
            const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
            
            expect(drafterBody.textContent).toContain("My App");
            expect(drafterBody.textContent).toContain("Section 1");
            expect(drafterBody.textContent).toContain("Section 2");
            expect(drafterBody.textContent).toContain("Item 1");
            expect(drafterBody.textContent).toContain("Step 1");
            expect(drafterBody.textContent).toContain("Footer content");
        });
    });
});
