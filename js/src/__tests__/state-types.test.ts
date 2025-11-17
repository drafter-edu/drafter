/**
 * Tests for different State types and structures
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

const MULTI_FIELD_STATE_CODE = `
from drafter import *

# Reset server to clear any previous routes
reset_server()

@dataclass
class State:
    name: str
    age: int
    score: float
    active: bool
    tags: list[str]

@route
def index(state: State):
    return Page(state, [
        f"Name: {state.name}",
        f"Age: {state.age}",
        f"Score: {state.score}",
        f"Active: {state.active}",
        f"Tags: {', '.join(state.tags)}",
        TextBox("new_name", state.name),
        Button("Update", update),
    ])

@route
def update(state: State, new_name: str):
    state.name = new_name
    state.age += 1
    return index(state)

start_server(State("Alice", 25, 95.5, True, ["python", "javascript"]))
`;

describe("State Types - Multi-field State", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can load State with multiple field types", async () => {
        await runStudentCode({ code: MULTI_FIELD_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Name:\s*Alice/);
        await app.findByText(/Age:\s*25/);
        await app.findByText(/Score:\s*95\.5/);
        await app.findByText(/Active:\s*True/);
        await app.findByText(/Tags:\s*python, javascript/);
    });

    test("can update State with multiple field types", async () => {
        await runStudentCode({ code: MULTI_FIELD_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const textBox = app.getByRole("textbox", { name: /new_name/i });
        await userEvent.clear(textBox);
        await userEvent.type(textBox, "Bob");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Name:\s*Bob/);
        await app.findByText(/Age:\s*26/);
    });
});

const LIST_STATE_CODE = `
from drafter import *

# Reset server to clear any previous routes
reset_server()

@dataclass
class State:
    items: list[str]

@route
def index(state: State):
    return Page(state, [
        "Items:",
        *state.items,
        TextBox("new_item"),
        Button("Add", add_item),
    ])

@route
def add_item(state: State, new_item: str):
    state.items.append(new_item)
    return index(state)

start_server(State(["apple", "banana"]))
`;

describe("State Types - List State", () => {
    beforeEach(() => {
        // Completely recreate the DOM and reset server
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can load State with list of strings", async () => {
        await runStudentCode({ code: LIST_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/apple/);
        await app.findByText(/banana/);
    });

    test("can add items to list State", async () => {
        await runStudentCode({ code: LIST_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const textBox = app.getByRole("textbox", { name: /new_item/i });
        await userEvent.type(textBox, "cherry");
        await userEvent.click(await app.findByRole("button", { name: /add/i }));

        await app.findByText(/cherry/);
    });
});

const PRIMITIVE_INT_STATE_CODE = `
from drafter import *

# Reset server to clear any previous routes
reset_server()

@route
def index(state: int):
    return Page(state, [
        f"Counter: {state}",
        Button("Increment", increment),
        Button("Decrement", decrement),
    ])

@route
def increment(state: int):
    return index(state + 1)

@route
def decrement(state: int):
    return index(state - 1)

start_server(0)
`;

describe("State Types - Primitive Integer", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can load primitive integer state", async () => {
        await runStudentCode({ code: PRIMITIVE_INT_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Counter:\s*0/);
    });

    test("can increment primitive integer state", async () => {
        await runStudentCode({ code: PRIMITIVE_INT_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await app.findByText(/Counter:\s*1/);

        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await app.findByText(/Counter:\s*2/);
    });

    test("can decrement primitive integer state", async () => {
        await runStudentCode({ code: PRIMITIVE_INT_STATE_CODE, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await userEvent.click(
            await app.findByRole("button", { name: /decrement/i })
        );
        await app.findByText(/Counter:\s*1/);
    });
});

