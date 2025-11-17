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

describe("State Types Tests", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("handles State with multiple field types", async () => {
        const code = `
from drafter import *

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
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Name:\s*Alice/);
        await app.findByText(/Age:\s*25/);
        await app.findByText(/Score:\s*95\.5/);
        await app.findByText(/Active:\s*True/);
        await app.findByText(/Tags:\s*python, javascript/);

        const textBox = app.getByRole("textbox", { name: /new_name/i });
        await userEvent.clear(textBox);
        await userEvent.type(textBox, "Bob");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Name:\s*Bob/);
        await app.findByText(/Age:\s*26/);
    });

    test("handles State with nested dataclasses", async () => {
        const code = `
from drafter import *

@dataclass
class Address:
    street: str
    city: str

@dataclass
class State:
    name: str
    address: Address

@route
def index(state: State):
    return Page(state, [
        f"Name: {state.name}",
        f"Street: {state.address.street}",
        f"City: {state.address.city}",
        TextBox("new_city", state.address.city),
        Button("Update City", update),
    ])

@route
def update(state: State, new_city: str):
    state.address.city = new_city
    return index(state)

start_server(State("Alice", Address("123 Main St", "New York")))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Name:\s*Alice/);
        await app.findByText(/Street:\s*123 Main St/);
        await app.findByText(/City:\s*New York/);

        const textBox = app.getByRole("textbox", { name: /new_city/i });
        await userEvent.clear(textBox);
        await userEvent.type(textBox, "Boston");
        await userEvent.click(
            await app.findByRole("button", { name: /update city/i })
        );

        await app.findByText(/City:\s*Boston/);
    });

    test("handles State with list of strings", async () => {
        const code = `
from drafter import *

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
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/apple/);
        await app.findByText(/banana/);

        const textBox = app.getByRole("textbox", { name: /new_item/i });
        await userEvent.type(textBox, "cherry");
        await userEvent.click(await app.findByRole("button", { name: /add/i }));

        await app.findByText(/cherry/);
    });

    test("handles State with dictionary", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    scores: dict[str, int]

@route
def index(state: State):
    score_list = [f"{name}: {score}" for name, score in state.scores.items()]
    return Page(state, [
        "Scores:",
        *score_list,
        TextBox("name"),
        TextBox("score"),
        Button("Add Score", add_score),
    ])

@route
def add_score(state: State, name: str, score: str):
    state.scores[name] = int(score)
    return index(state)

start_server(State({"Alice": 100, "Bob": 95}))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Alice:\s*100/);
        await app.findByText(/Bob:\s*95/);

        const nameBox = app.getByRole("textbox", { name: /^name$/i });
        const scoreBox = app.getByRole("textbox", { name: /^score$/i });

        await userEvent.type(nameBox, "Charlie");
        await userEvent.type(scoreBox, "88");
        await userEvent.click(
            await app.findByRole("button", { name: /add score/i })
        );

        await app.findByText(/Charlie:\s*88/);
    });

    test("handles primitive string state", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        f"Message: {state}",
        TextBox("new_message"),
        Button("Update", update),
    ])

@route
def update(state: str, new_message: str):
    return index(new_message)

start_server("Hello, World!")
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Message:\s*Hello, World!/);

        const textBox = app.getByRole("textbox", { name: /new_message/i });
        await userEvent.type(textBox, "New message");
        await userEvent.click(
            await app.findByRole("button", { name: /update/i })
        );

        await app.findByText(/Message:\s*New message/);
    });

    test("handles primitive integer state", async () => {
        const code = `
from drafter import *

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
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Counter:\s*0/);

        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await app.findByText(/Counter:\s*1/);

        await userEvent.click(
            await app.findByRole("button", { name: /increment/i })
        );
        await app.findByText(/Counter:\s*2/);

        await userEvent.click(
            await app.findByRole("button", { name: /decrement/i })
        );
        await app.findByText(/Counter:\s*1/);
    });
});
