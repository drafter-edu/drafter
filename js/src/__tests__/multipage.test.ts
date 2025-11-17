/**
 * Tests for multiple pages and routing
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Multi-page Navigation Test 1", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can navigate between multiple pages", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    counter: int

@route
def index(state: State):
    return Page(state, [
        "Home Page",
        f"Counter: {state.counter}",
        Button("Go to About", about),
    ])

@route
def about(state: State):
    return Page(state, [
        "About Page",
        f"Counter: {state.counter}",
        Button("Go to Home", index),
        Button("Increment", increment)
    ])

@route
def increment(state: State):
    state.counter += 1
    return about(state)

start_server(State(0))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
        const app = within(drafterBody as HTMLElement);

        // Check we're on home page
        await app.findByText(/Home Page/);
        await app.findByText(/Counter:\s*0/);

        // Navigate to about page
        const aboutButton = await app.findByRole("button", {
            name: /go to about/i,
        });
        await userEvent.click(aboutButton);

        // Check we're on about page
        await app.findByText(/About Page/);

        // Increment counter
        const incrementButton = await app.findByRole("button", {
            name: /increment/i,
        });
        await userEvent.click(incrementButton);
        await app.findByText(/Counter:\s*1/);

        // Navigate back to home
        const homeButton = await app.findByRole("button", {
            name: /go to home/i,
        });
        await userEvent.click(homeButton);
        await app.findByText(/Home Page/);
        await app.findByText(/Counter:\s*1/);
    });
});

describe("Multi-page Navigation Test 2", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can pass arguments through button navigation", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    message: str

@route
def index(state: State):
    return Page(state, [
        "Home",
        Button("Go to Page A", page_a, [Argument("page_name", "A")]),
        Button("Go to Page B", page_b, [Argument("page_name", "B")]),
    ])

@route
def page_a(state: State, page_name: str):
    state.message = f"You are on page {page_name}"
    return Page(state, [
        state.message,
        Button("Back to Home", index),
    ])

@route
def page_b(state: State, page_name: str):
    state.message = f"You are on page {page_name}"
    return Page(state, [
        state.message,
        Button("Back to Home", index),
    ])

start_server(State("Initial message"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Navigate to page A
        const pageAButton = await app.findByRole("button", {
            name: /go to page a/i,
        });
        await userEvent.click(pageAButton);
        await app.findByText(/You are on page A/);

        // Navigate back to home
        await userEvent.click(
            await app.findByRole("button", { name: /back to home/i })
        );

        // Navigate to page B
        const pageBButton = await app.findByRole("button", {
            name: /go to page b/i,
        });
        await userEvent.click(pageBButton);
        await app.findByText(/You are on page B/);
    });
});

describe("Multi-page Navigation Test 3", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    // Skipping this test due to skulpt environment not being fully reset between tests
    test.skip("handles state changes across page navigation", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    count: int

@route
def index(state: State):
    state.count += 1
    return Page(state, [
        "Home Page",
        f"Visits: {state.count}",
        Button("Go to Other", other_page),
    ])

@route
def other_page(state: State):
    state.count += 1
    return Page(state, [
        "Other Page",
        f"Visits: {state.count}",
        Button("Back to Home", index),
    ])

start_server(State(0))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Initially on home (1 visit)
        await app.findByText(/Visits:\s*1/);

        // Go to other page (2 visits)
        await userEvent.click(
            await app.findByRole("button", { name: /go to other/i })
        );
        await app.findByText(/Visits:\s*2/);

        // Go back to home (3 visits)
        await userEvent.click(
            await app.findByRole("button", { name: /back to home/i })
        );
        await app.findByText(/Visits:\s*3/);
    });
});

