/**
 * Comprehensive tests for multiple pages and navigation in Drafter applications
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Multiple Pages and Navigation", () => {
    beforeEach(() => {
        // Reset the entire document body to ensure clean state
        document.body.innerHTML = "";
        const root = document.createElement("div");
        root.id = "drafter-root--";
        document.body.appendChild(root);
    });

    test("can navigate between multiple pages", async () => {
        const code = `
from drafter import *

@route
def index(state: int):
    return Page(state, [
        "This is the home page",
        Button("Go to page 2", page2)
    ])

@route
def page2(state: int):
    return Page(state, [
        "This is page 2",
        Button("Go to page 3", page3)
    ])

@route
def page3(state: int):
    return Page(state, [
        "This is page 3",
        Button("Back to home", index)
    ])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        // Start on home page
        await app.findByText(/this is the home page/i);

        // Navigate to page 2
        await userEvent.click(await app.findByRole("button", { name: /go to page 2/i }));
        await app.findByText(/this is page 2/i);

        // Navigate to page 3
        await userEvent.click(await app.findByRole("button", { name: /go to page 3/i }));
        await app.findByText(/this is page 3/i);

        // Navigate back to home
        await userEvent.click(await app.findByRole("button", { name: /back to home/i }));
        await app.findByText(/this is the home page/i);
    });

    test("supports passing state between pages", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    counter: int
    message: str

@route
def index(state: State):
    return Page(state, [
        f"Counter: {state.counter}",
        f"Message: {state.message}",
        Button("Increment", increment)
    ])

@route
def increment(state: State):
    state.counter += 1
    return Page(state, [
        f"Incremented! Counter: {state.counter}",
        Button("Back", index)
    ])

start_server(State(0, "Hello"))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        // Check initial state
        await app.findByText(/Counter:\s*0/);
        await app.findByText(/Message:\s*Hello/);

        // Navigate to increment page
        await userEvent.click(await app.findByRole("button", { name: /increment/i }));
        await app.findByText(/Incremented! Counter:\s*1/);

        // Navigate back
        await userEvent.click(await app.findByRole("button", { name: /back/i }));
        await app.findByText(/Counter:\s*1/);
    });

    test("handles deeply nested page navigation", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "Level 1",
        Button("Go deeper", level2)
    ])

@route
def level2(state: str):
    return Page(state, [
        "Level 2",
        Button("Go deeper", level3)
    ])

@route
def level3(state: str):
    return Page(state, [
        "Level 3",
        Button("Go deeper", level4)
    ])

@route
def level4(state: str):
    return Page(state, [
        "Level 4 - deepest",
        Button("Back to level 1", index)
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/Level 1/);
        await userEvent.click(await app.findByRole("button", { name: /go deeper/i }));
        await app.findByText(/Level 2/);
        await userEvent.click(await app.findByRole("button", { name: /go deeper/i }));
        await app.findByText(/Level 3/);
        await userEvent.click(await app.findByRole("button", { name: /go deeper/i }));
        await app.findByText(/Level 4 - deepest/);
        await userEvent.click(await app.findByRole("button", { name: /back to level 1/i }));
        await app.findByText(/Level 1/);
    });

    test("supports multiple buttons on same page", async () => {
        const code = `
from drafter import *

@route
def index(state: str):
    return Page(state, [
        "Choose a page",
        Button("Option A", page_a),
        Button("Option B", page_b),
        Button("Option C", page_c)
    ])

@route
def page_a(state: str):
    return Page(state, [
        "You chose A",
        Button("Home", index)
    ])

@route
def page_b(state: str):
    return Page(state, [
        "You chose B",
        Button("Home", index)
    ])

@route
def page_c(state: str):
    return Page(state, [
        "You chose C",
        Button("Home", index)
    ])

start_server("")
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        await app.findByText(/choose a page/i);
        
        // Test each option
        await userEvent.click(await app.findByRole("button", { name: /option a/i }));
        await app.findByText(/you chose a/i);
        await userEvent.click(await app.findByRole("button", { name: /home/i }));

        await userEvent.click(await app.findByRole("button", { name: /option b/i }));
        await app.findByText(/you chose b/i);
        await userEvent.click(await app.findByRole("button", { name: /home/i }));

        await userEvent.click(await app.findByRole("button", { name: /option c/i }));
        await app.findByText(/you chose c/i);
    });

    test("page navigation with conditional rendering", async () => {
        // First, ensure we have a clean slate by running a simple app
        const setupCode = `
from drafter import *

@route
def setup_index(state: int):
    return Page(state, ["Setup"])

start_server(0)
`;
        await runStudentCode({ code: setupCode, presentErrors: false });
        
        // Now run the actual test
        const code = `
from drafter import *

@dataclass
class State:
    logged_in: bool

@route
def index(state: State):
    if state.logged_in:
        return Page(state, [
            "Welcome! You are logged in.",
            Button("Logout", logout)
        ])
    else:
        return Page(state, [
            "Please log in.",
            Button("Login", login)
        ])

@route
def login(state: State):
    state.logged_in = True
    return index(state)

@route
def logout(state: State):
    state.logged_in = False
    return index(state)

start_server(State(False))
`;
        await runStudentCode({ code, presentErrors: false });
        
        const drafterBody = document.querySelector("#drafter-body--") as HTMLElement;
        const app = within(drafterBody);

        // Start logged out
        await app.findByText(/please log in/i);
        
        // Login
        await userEvent.click(await app.findByRole("button", { name: /login/i }));
        await app.findByText(/welcome! you are logged in/i);

        // Logout
        await userEvent.click(await app.findByRole("button", { name: /logout/i }));
        await app.findByText(/please log in/i);
    });
});
