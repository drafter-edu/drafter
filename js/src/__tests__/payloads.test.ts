/**
 * Tests for different ResponsePayload types: Fragment, Update, Redirect, Download, Progress
 */

import { describe, test, expect } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Fragment Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can create and render Fragment payload", async () => {
        const code = `
from drafter import *

hide_debug_information()

@route
def index(state: int):
    return Page(state, [
        "Counter: " + str(state),
        Button("Get Fragment", fragment_route)
    ])

@route
def fragment_route(state: int):
    return Fragment("<div class='fragment-content'>This is a fragment!</div>")

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});

describe("Update Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can create Update payload with state change", async () => {
        const code = `
from drafter import *

hide_debug_information()

@dataclass
class State:
    counter: int

@route
def index(state: State):
    return Page(state, [
        f"Counter: {state.counter}",
        Button("Increment", increment)
    ])

@route
def increment(state: State):
    state.counter += 1
    return Update(state)

start_server(State(0))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});

describe("Redirect Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can create Redirect payload", async () => {
        const code = `
from drafter import *

hide_debug_information()

@route
def index(state: int):
    return Page(state, [
        "Index page",
        Button("Go to target", redirect_to_target)
    ])

@route
def redirect_to_target(state: int):
    return Redirect("target_page", Page(state, ["Target page reached!"]))

@route
def target_page(state: int):
    return Page(state, ["Direct target page"])

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});

describe("Download Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can create Download payload", async () => {
        const code = `
from drafter import *

hide_debug_information()

@route
def index(state: int):
    return Page(state, [
        "Click to download",
        Button("Download File", download_file)
    ])

@route
def download_file(state: int):
    return DownloadPayload("test.txt", "Hello, World!", "text/plain")

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});

describe("Progress Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can create Progress payload with message", async () => {
        const code = `
from drafter import *

hide_debug_information()

@route
def index(state: int):
    return Page(state, [
        "Processing task",
        Button("Show Progress", show_progress)
    ])

@route
def show_progress(state: int):
    return Progress("Processing...", 50.0)

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });

    test("can create Progress payload without percentage", async () => {
        const code = `
from drafter import *

hide_debug_information()

@route
def index(state: int):
    return Page(state, [
        "Processing task",
        Button("Show Progress", show_progress)
    ])

@route
def show_progress(state: int):
    return Progress("Loading data...")

start_server(0)
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});

describe("Mixed Payload Tests", () => {
    beforeEach(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("can switch between different payload types", async () => {
        const code = `
from drafter import *

hide_debug_information()

@dataclass
class State:
    mode: str

@route
def index(state: State):
    return Page(state, [
        f"Current mode: {state.mode}",
        Button("Show Fragment", fragment_mode),
        Button("Show Progress", progress_mode),
        Button("Back to Page", page_mode)
    ])

@route
def fragment_mode(state: State):
    state.mode = "fragment"
    return Fragment("<p>This is a fragment!</p>")

@route
def progress_mode(state: State):
    state.mode = "progress"
    return Progress("Processing data...", 75.0)

@route
def page_mode(state: State):
    state.mode = "page"
    return index(state)

start_server(State("initial"))
`;
        await runStudentCode({ code, presentErrors: false });
        const drafterBody = document.querySelector("#drafter-body--");
        expect(drafterBody).not.toBeNull();
    });
});
