/**
 * Tests for layout components (lists, headers, tables, etc.)
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Layout Components Tests", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("handles BulletedList component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    items: list[str]

@route
def index(state: State):
    return Page(state, [
        "My Items:",
        BulletedList(state.items),
        TextBox("new_item"),
        Button("Add", add_item),
    ])

@route
def add_item(state: State, new_item: str):
    state.items.append(new_item)
    return index(state)

start_server(State(["apple", "banana", "cherry"]))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Check for list items
        const list = drafterBody?.querySelector("ul");
        expect(list).not.toBeNull();

        await app.findByText(/apple/);
        await app.findByText(/banana/);
        await app.findByText(/cherry/);

        const textBox = app.getByRole("textbox", { name: /new_item/i });
        await userEvent.type(textBox, "date");
        await userEvent.click(await app.findByRole("button", { name: /add/i }));

        await app.findByText(/date/);
    });

    test("handles NumberedList component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    tasks: list[str]

@route
def index(state: State):
    return Page(state, [
        "Todo List:",
        NumberedList(state.tasks),
        TextBox("new_task"),
        Button("Add Task", add_task),
    ])

@route
def add_task(state: State, new_task: str):
    state.tasks.append(new_task)
    return index(state)

start_server(State(["Wash dishes", "Do laundry", "Read book"]))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Check for ordered list
        const list = drafterBody?.querySelector("ol");
        expect(list).not.toBeNull();

        await app.findByText(/Wash dishes/);
        await app.findByText(/Do laundry/);
        await app.findByText(/Read book/);

        const textBox = app.getByRole("textbox", { name: /new_task/i });
        await userEvent.type(textBox, "Go shopping");
        await userEvent.click(
            await app.findByRole("button", { name: /add task/i })
        );

        await app.findByText(/Go shopping/);
    });

    test("handles Header components", async () => {
        const code = `
from drafter import *

@route
def index():
    return Page(None, [
        Header("Main Title"),
        "Some text",
        SubHeader("Subsection"),
        "More text",
    ])

start_server()
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");

        // Check for header elements
        const h1 = drafterBody?.querySelector("h1");
        const h2 = drafterBody?.querySelector("h2");

        expect(h1).not.toBeNull();
        expect(h2).not.toBeNull();
        expect(h1?.textContent).toContain("Main Title");
        expect(h2?.textContent).toContain("Subsection");
    });

    test("handles LineBreak component", async () => {
        const code = `
from drafter import *

@route
def index():
    return Page(None, [
        "Line 1",
        LineBreak(),
        "Line 2",
        LineBreak(),
        "Line 3",
    ])

start_server()
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Line 1/);
        await app.findByText(/Line 2/);
        await app.findByText(/Line 3/);

        // Check for <br> tags
        const lineBreaks = drafterBody?.querySelectorAll("br");
        expect(lineBreaks?.length).toBeGreaterThanOrEqual(2);
    });

    test("handles HorizontalRule component", async () => {
        const code = `
from drafter import *

@route
def index():
    return Page(None, [
        "Section 1",
        HorizontalRule(),
        "Section 2",
        HorizontalRule(),
        "Section 3",
    ])

start_server()
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Section 1/);
        await app.findByText(/Section 2/);
        await app.findByText(/Section 3/);

        // Check for <hr> tags
        const hrs = drafterBody?.querySelectorAll("hr");
        expect(hrs?.length).toBe(2);
    });

    test("handles Table component with simple data", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    data: list[list[str]]

@route
def index(state: State):
    return Page(state, [
        "Data Table:",
        Table(state.data),
        Button("Add Row", add_row),
    ])

@route
def add_row(state: State):
    state.data.append([f"Row {len(state.data) + 1}", f"Value {len(state.data) + 1}"])
    return index(state)

start_server(State([
    ["Name", "Age"],
    ["Alice", "25"],
    ["Bob", "30"]
]))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Check for table element
        const table = drafterBody?.querySelector("table");
        expect(table).not.toBeNull();

        await app.findByText(/Alice/);
        await app.findByText(/Bob/);
        await app.findByText(/25/);
        await app.findByText(/30/);

        await userEvent.click(
            await app.findByRole("button", { name: /add row/i })
        );

        await app.findByText(/Row 3/);
        await app.findByText(/Value 3/);
    });

    test("handles nested lists", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    categories: list[tuple[str, list[str]]]

@route
def index(state: State):
    items = []
    for category, subitems in state.categories:
        items.append(category)
        items.append(BulletedList(subitems))
    return Page(state, [
        "Categories:",
        *items,
    ])

start_server(State([
    ("Fruits", ["apple", "banana"]),
    ("Vegetables", ["carrot", "broccoli"])
]))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Fruits/);
        await app.findByText(/apple/);
        await app.findByText(/banana/);
        await app.findByText(/Vegetables/);
        await app.findByText(/carrot/);
        await app.findByText(/broccoli/);

        // Check for multiple lists
        const lists = drafterBody?.querySelectorAll("ul");
        expect(lists?.length).toBeGreaterThanOrEqual(2);
    });

    test("handles complex layout with multiple components", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    title: str
    items: list[str]
    count: int

@route
def index(state: State):
    return Page(state, [
        Header(state.title),
        HorizontalRule(),
        f"Total items: {state.count}",
        LineBreak(),
        "Current items:",
        NumberedList(state.items),
        HorizontalRule(),
        TextBox("new_item"),
        Button("Add Item", add_item),
    ])

@route
def add_item(state: State, new_item: str):
    state.items.append(new_item)
    state.count = len(state.items)
    return index(state)

start_server(State("My List", ["First", "Second"], 2))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const h1 = drafterBody?.querySelector("h1");
        expect(h1?.textContent).toContain("My List");

        await app.findByText(/Total items:\s*2/);
        await app.findByText(/First/);
        await app.findByText(/Second/);

        const textBox = app.getByRole("textbox", { name: /new_item/i });
        await userEvent.type(textBox, "Third");
        await userEvent.click(
            await app.findByRole("button", { name: /add item/i })
        );

        await app.findByText(/Total items:\s*3/);
        await app.findByText(/Third/);
    });
});
