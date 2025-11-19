/**
 * Comprehensive tests for Button and Link components with various argument patterns
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Buttons and Links with Arguments", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    test("button with single argument", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        f"Count: {state}",
        Button("Add 5", add_value, [Argument("amount", 5)])
    ])

@route
def add_value(state: int, amount: int):
    return index(state + amount)

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Count:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /add 5/i }));
        await app.findByText(/Count:\s*5/);
        await userEvent.click(await app.findByRole("button", { name: /add 5/i }));
        await app.findByText(/Count:\s*10/);
    });

    test("button with multiple arguments", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    x: int
    y: int

@route
def index(state: State):
    return Page(state, [
        f"X: {state.x}, Y: {state.y}",
        Button("Add (3, 7)", add_values, [Argument("dx", 3), Argument("dy", 7)])
    ])

@route
def add_values(state: State, dx: int, dy: int):
    state.x += dx
    state.y += dy
    return index(state)

start_server(State(0, 0))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/X:\s*0,\s*Y:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /add \(3, 7\)/i }));
        await app.findByText(/X:\s*3,\s*Y:\s*7/);
    });

    test("button with string arguments", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Message: {state}",
        Button("Hello", set_message, [Argument("message", "Hello World")]),
        Button("Goodbye", set_message, [Argument("message", "Goodbye!")])
    ])

@route
def set_message(state: str, message: str):
    return index(message)

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Message:\s*$/);
        await userEvent.click(await app.findByRole("button", { name: /^hello$/i }));
        await app.findByText(/Message:\s*Hello World/);
        
        await userEvent.click(await app.findByRole("button", { name: /goodbye/i }));
        await app.findByText(/Message:\s*Goodbye!/);
    });

    test("button with boolean argument", async () => {
        const code = `
from drafter import *

@route
def index(state: bool):
    return Page(state, [
        f"Flag: {state}",
        Button("Set True", set_flag, [Argument("value", True)]),
        Button("Set False", set_flag, [Argument("value", False)])
    ])

@route
def set_flag(state: bool, value: bool):
    return index(value)

start_server(False)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Flag:\s*False/);
        await userEvent.click(await app.findByRole("button", { name: /set true/i }));
        await app.findByText(/Flag:\s*True/);
        await userEvent.click(await app.findByRole("button", { name: /set false/i }));
        await app.findByText(/Flag:\s*False/);
    });

    test("multiple buttons with different arguments", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        f"Value: {state}",
        Button("+1", adjust, [Argument("amount", 1)]),
        Button("+10", adjust, [Argument("amount", 10)]),
        Button("+100", adjust, [Argument("amount", 100)]),
        Button("Reset", reset)
    ])

@route
def adjust(state: int, amount: int):
    return index(state + amount)

@route
def reset(state: int):
    return index(0)

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Value:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /\+1/i }));
        await app.findByText(/Value:\s*1/);
        await userEvent.click(await app.findByRole("button", { name: /\+10/i }));
        await app.findByText(/Value:\s*11/);
        await userEvent.click(await app.findByRole("button", { name: /\+100/i }));
        await app.findByText(/Value:\s*111/);
        await userEvent.click(await app.findByRole("button", { name: /reset/i }));
        await app.findByText(/Value:\s*0/);
    });

    test("button arguments combined with form inputs", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    counter: int
    name: str

@route
def index(state: State):
    return Page(state, [
        f"Counter: {state.counter}",
        f"Name: {state.name}",
        TextBox("name", state.name),
        Button("Add 1", increment, [Argument("amount", 1)]),
        Button("Add 5", increment, [Argument("amount", 5)])
    ])

@route
def increment(state: State, name: str, amount: int):
    state.counter += amount
    state.name = name
    return index(state)

start_server(State(0, ""))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        const textbox = app.getByRole("textbox", { name: /name/i });
        await userEvent.type(textbox, "Alice");
        
        await userEvent.click(await app.findByRole("button", { name: /add 1/i }));
        await app.findByText(/Counter:\s*1/);
        await app.findByText(/Name:\s*Alice/);
        
        await userEvent.click(await app.findByRole("button", { name: /add 5/i }));
        await app.findByText(/Counter:\s*6/);
    });

    test("button with list argument", async () => {
        const code = `
from drafter import *

@route
def index(state: list):
    items_str = ", ".join(str(x) for x in state)
    return Page(state, [
        f"Items: {items_str}",
        Button("Add [1,2,3]", add_items, [Argument("new_items", [1, 2, 3])])
    ])

@route
def add_items(state: list, new_items: list):
    state.extend(new_items)
    return index(state)

start_server([])
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Items:\s*$/);
        await userEvent.click(await app.findByRole("button", { name: /add \[1,2,3\]/i }));
        await app.findByText(/Items:\s*1,\s*2,\s*3/);
    });

    test("buttons with special character arguments", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Symbol: {state}",
        Button("Star", set_symbol, [Argument("symbol", "★")]),
        Button("Heart", set_symbol, [Argument("symbol", "♥")]),
        Button("Arrow", set_symbol, [Argument("symbol", "→")])
    ])

@route
def set_symbol(state: str, symbol: str):
    return index(symbol)

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await userEvent.click(await app.findByRole("button", { name: /star/i }));
        await app.findByText(/Symbol:\s*★/);
        
        await userEvent.click(await app.findByRole("button", { name: /heart/i }));
        await app.findByText(/Symbol:\s*♥/);
        
        await userEvent.click(await app.findByRole("button", { name: /arrow/i }));
        await app.findByText(/Symbol:\s*→/);
    });

    test("using Argument helper with buttons", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        f"Count: {state}",
        Button("Increment", increment, Argument("amount", 1)),
        Button("Decrement", increment, Argument("amount", -1))
    ])

@route
def increment(state: int, amount: int):
    return index(state + amount)

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Count:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /increment/i }));
        await app.findByText(/Count:\s*1/);
        await userEvent.click(await app.findByRole("button", { name: /decrement/i }));
        await app.findByText(/Count:\s*0/);
    });

    test("button referencing route by string name", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        f"Count: {state}",
        Button("Next", "next_page")
    ])

@route
def next_page(state: int):
    return Page(state, [
        "This is the next page",
        Button("Back", "index")
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Count:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /next/i }));
        await app.findByText(/this is the next page/i);
        await userEvent.click(await app.findByRole("button", { name: /back/i }));
        await app.findByText(/Count:\s*0/);
    });
});
