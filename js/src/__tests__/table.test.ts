/**
 * Comprehensive tests for Table component
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Table Component", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    test("renders simple table with rows and columns", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["Name", "Age", "City"],
        ["Alice", 25, "Boston"],
        ["Bob", 30, "New York"],
        ["Charlie", 35, "Chicago"]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        const table = drafterBody.querySelector("table");
        expect(table).not.toBeNull();
        expect(drafterBody.textContent).toContain("Name");
        expect(drafterBody.textContent).toContain("Alice");
        expect(drafterBody.textContent).toContain("Bob");
        expect(drafterBody.textContent).toContain("Charlie");
        expect(drafterBody.textContent).toContain("Boston");
    });

    test("renders table with headers", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    headers = ["Product", "Price", "Stock"]
    rows = [
        ["Apple", "$1.50", "100"],
        ["Banana", "$0.75", "150"],
        ["Orange", "$2.00", "80"]
    ]
    return Page(state, [
        Table([headers] + rows)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        const table = drafterBody.querySelector("table");
        expect(table).not.toBeNull();
        expect(drafterBody.textContent).toContain("Product");
        expect(drafterBody.textContent).toContain("Price");
        expect(drafterBody.textContent).toContain("Stock");
        expect(drafterBody.textContent).toContain("Apple");
        expect(drafterBody.textContent).toContain("$1.50");
    });

    test("handles empty table", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "Empty table:",
        Table([])
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        expect(drafterBody.textContent).toContain("Empty table:");
    });

    test("renders table with numeric data", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["X", "Y", "X+Y"],
        [1, 2, 3],
        [4, 5, 9],
        [10, 20, 30]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        const table = drafterBody.querySelector("table");
        expect(table).not.toBeNull();
        expect(drafterBody.textContent).toContain("X+Y");
        expect(drafterBody.textContent).toContain("30");
    });

    test("renders table with mixed data types", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["String", "Number", "Boolean"],
        ["hello", 42, True],
        ["world", 3.14, False]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        expect(drafterBody.textContent).toContain("hello");
        expect(drafterBody.textContent).toContain("42");
        expect(drafterBody.textContent).toContain("True");
        expect(drafterBody.textContent).toContain("3.14");
        expect(drafterBody.textContent).toContain("False");
    });

    test("renders table with single row", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [["A", "B", "C"]]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        const table = drafterBody.querySelector("table");
        expect(table).not.toBeNull();
        expect(drafterBody.textContent).toContain("A");
        expect(drafterBody.textContent).toContain("B");
        expect(drafterBody.textContent).toContain("C");
    });

    test("renders table with single column", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["Item"],
        ["Row 1"],
        ["Row 2"],
        ["Row 3"]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        expect(drafterBody.textContent).toContain("Item");
        expect(drafterBody.textContent).toContain("Row 1");
        expect(drafterBody.textContent).toContain("Row 2");
        expect(drafterBody.textContent).toContain("Row 3");
    });

    test("dynamic table from state", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    rows: list

@route
def index(state: State):
    return Page(state, [
        Table([["ID", "Value"]] + [[i, f"Item {i}"] for i in state.rows]),
        Button("Add Row", add_row)
    ])

@route
def add_row(state: State):
    state.rows.append(len(state.rows) + 1)
    return index(state)

start_server(State([1, 2, 3]))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);
        
        expect(drafterBody.textContent).toContain("Item 1");
        expect(drafterBody.textContent).toContain("Item 2");
        expect(drafterBody.textContent).toContain("Item 3");
        
        await userEvent.click(await app.findByRole("button", { name: /add row/i }));
        await waitFor(() => {
            expect(drafterBody.textContent).toContain("Item 4");
        });
    });

    test("renders table with special characters", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["Symbol", "Name"],
        ["<", "Less than"],
        [">", "Greater than"],
        ["&", "Ampersand"],
        ["\\"", "Quote"]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        expect(drafterBody.textContent).toContain("Less than");
        expect(drafterBody.textContent).toContain("Greater than");
        expect(drafterBody.textContent).toContain("Ampersand");
    });

    test("renders table with Unicode characters", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [
        ["Language", "Hello"],
        ["English", "Hello"],
        ["Chinese", "你好"],
        ["Arabic", "مرحبا"],
        ["Emoji", "👋"]
    ]
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        expect(drafterBody.textContent).toContain("你好");
        expect(drafterBody.textContent).toContain("مرحبا");
        expect(drafterBody.textContent).toContain("👋");
    });

    test("renders large table", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    data = [["Row", "Value"]]
    for i in range(1, 51):
        data.append([i, i * 2])
    return Page(state, [
        Table(data)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        
        const table = drafterBody.querySelector("table");
        expect(table).not.toBeNull();
        expect(drafterBody.textContent).toContain("Row");
        // Check that we have a reasonable amount of rows rendered
        const rows = table?.querySelectorAll("tr");
        expect(rows && rows.length).toBeGreaterThan(10);
    });
});
