/**
 * Comprehensive tests for different State types in Drafter applications
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("State Types", () => {
    beforeEach(() => {
        // Reset the entire document body to ensure clean state
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    test("works with int state", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        f"Counter: {state}",
        Button("Increment", increment)
    ])

@route
def increment(state: int):
    state += 1
    return index(state)

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Counter:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /increment/i }));
        await app.findByText(/Counter:\s*1/);
        await userEvent.click(await app.findByRole("button", { name: /increment/i }));
        await app.findByText(/Counter:\s*2/);
    });

    test("works with str state", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Message: {state}",
        TextBox("new_message", state),
        Button("Update", update)
    ])

@route
def update(state: str, new_message: str):
    return index(new_message)

start_server("Hello World")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Message:\s*Hello World/);
        
        const textbox = app.getByRole("textbox", { name: /new_message/i });
        await userEvent.clear(textbox);
        await userEvent.type(textbox, "Updated!");
        await userEvent.click(await app.findByRole("button", { name: /update/i }));
        await app.findByText(/Message:\s*Updated!/);
    });

    test("works with bool state", async () => {
        const code = `
from drafter import *

@route
def index(state: bool):
    return Page(state, [
        f"State is: {state}",
        Button("Toggle", toggle)
    ])

@route
def toggle(state: bool):
    return index(not state)

start_server(True)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/State is:\s*True/);
        await userEvent.click(await app.findByRole("button", { name: /toggle/i }));
        await app.findByText(/State is:\s*False/);
        await userEvent.click(await app.findByRole("button", { name: /toggle/i }));
        await app.findByText(/State is:\s*True/);
    });

    test("works with float state", async () => {
        const code = `
from drafter import *

@route
def index(state: float):
    return Page(state, [
        f"Value: {state:.2f}",
        Button("Add 0.5", add)
    ])

@route
def add(state: float):
    return index(state + 0.5)

start_server(0.0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Value:\s*0\.00/);
        await userEvent.click(await app.findByRole("button", { name: /add 0.5/i }));
        await app.findByText(/Value:\s*0\.50/);
        await userEvent.click(await app.findByRole("button", { name: /add 0.5/i }));
        await app.findByText(/Value:\s*1\.00/);
    });

    test("works with dataclass state", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    name: str
    age: int
    active: bool

@route
def index(state: State):
    return Page(state, [
        f"Name: {state.name}",
        f"Age: {state.age}",
        f"Active: {state.active}",
        TextBox("new_name", state.name),
        Button("Update", update)
    ])

@route
def update(state: State, new_name: str):
    state.name = new_name
    state.age += 1
    return index(state)

start_server(State("Alice", 25, True))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Name:\s*Alice/);
        await app.findByText(/Age:\s*25/);
        
        const textbox = app.getByRole("textbox", { name: /new_name/i });
        await userEvent.clear(textbox);
        await userEvent.type(textbox, "Bob");
        await userEvent.click(await app.findByRole("button", { name: /update/i }));
        
        await app.findByText(/Name:\s*Bob/);
        await app.findByText(/Age:\s*26/);
    });

    test("works with nested dataclass state", async () => {
        const code = `
from drafter import *

@dataclass
class Address:
    street: str
    city: str

@dataclass
class Person:
    name: str
    address: Address

@route
def index(state: Person):
    return Page(state, [
        f"Name: {state.name}",
        f"Street: {state.address.street}",
        f"City: {state.address.city}",
        Button("Change city", change_city)
    ])

@route
def change_city(state: Person):
    state.address.city = "New York"
    return index(state)

start_server(Person("Alice", Address("123 Main St", "Boston")))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/City:\s*Boston/);
        await userEvent.click(await app.findByRole("button", { name: /change city/i }));
        await app.findByText(/City:\s*New York/);
    });

    test("works with list state", async () => {
        const code = `
from drafter import *

@route
def index(state: list):
    items_text = ", ".join(str(item) for item in state)
    return Page(state, [
        f"Items: {items_text}",
        f"Count: {len(state)}",
        Button("Add item", add_item)
    ])

@route
def add_item(state: list):
    state.append(len(state) + 1)
    return index(state)

start_server([1, 2, 3])
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Items:\s*1,\s*2,\s*3/);
        await app.findByText(/Count:\s*3/);
        await userEvent.click(await app.findByRole("button", { name: /add item/i }));
        await app.findByText(/Count:\s*4/);
    });

    test("works with dict state", async () => {
        const code = `
from drafter import *

@route
def index(state: dict):
    return Page(state, [
        f"Name: {state['name']}",
        f"Score: {state['score']}",
        Button("Increment score", increment)
    ])

@route
def increment(state: dict):
    state['score'] += 10
    return index(state)

start_server({"name": "Player1", "score": 0})
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Score:\s*0/);
        await userEvent.click(await app.findByRole("button", { name: /increment score/i }));
        await app.findByText(/Score:\s*10/);
        await userEvent.click(await app.findByRole("button", { name: /increment score/i }));
        await app.findByText(/Score:\s*20/);
    });

    test("works with None state", async () => {
        const code = `
from drafter import *

@route
def index(state):
    return Page(state, [
        "State is None",
        Button("Go to page 2", page2)
    ])

@route
def page2(state):
    return Page(state, [
        "Still None!",
        Button("Back", index)
    ])

start_server(None)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/State is None/);
        await userEvent.click(await app.findByRole("button", { name: /go to page 2/i }));
        await app.findByText(/Still None!/);
    });
});
