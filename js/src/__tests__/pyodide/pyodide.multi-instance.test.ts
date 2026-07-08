/**
 * Concurrency guard: two Drafter apps on one page, each in its own shadow-DOM
 * root, sharing a single Pyodide runtime. Verifies they render and interact
 * independently — a click in app A must not touch app B, and vice versa.
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { runStudentCode } from "../../pyodide.index";
import { setupPyodideWithLocalDrafter } from "./pyodide-test-harness";

// A minimal counter app. The label is parameterized so the two instances render
// distinguishable content.
const counterApp = (label: string) => `
from drafter import *

hide_debug_information()

@dataclass
class State:
    counter: int

@route
def index(state: State):
    return Page(state, [
        "${label}",
        f"Counter: {state.counter}",
        Button("Increment", increment),
    ])

@route
def increment(state: State):
    state.counter += 1
    return index(state)

start_server(State(0))
`;

/** Resolve the drafter body inside a shadow-DOM instance's root element. */
function bodyOf(rootElementId: string): HTMLElement {
	const root = document.getElementById(rootElementId);
	expect(root).not.toBeNull();
	const host = root!.querySelector("#drafter-shadow-host--") as HTMLElement;
	expect(host).not.toBeNull();
	const shadow = host.shadowRoot;
	expect(shadow).not.toBeNull();
	const body = shadow!.querySelector("#drafter-body--") as HTMLElement;
	expect(body).not.toBeNull();
	return body;
}

describe("Multiple concurrent Drafter instances (Pyodide)", () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
		// Two independent roots on the same page.
		document.body.innerHTML =
			"<div id='drafter-root--a'></div><div id='drafter-root--b'></div>";
	});

	test("both instances render into their own shadow roots", async () => {
		await runStudentCode({
			code: counterApp("App A"),
			rootElementId: "drafter-root--a",
			useShadowDom: true,
			presentErrors: false,
		});
		await runStudentCode({
			code: counterApp("App B"),
			rootElementId: "drafter-root--b",
			useShadowDom: true,
			presentErrors: false,
		});

		const a = within(bodyOf("drafter-root--a"));
		const b = within(bodyOf("drafter-root--b"));

		expect(a.getByText(/App A/)).not.toBeNull();
		expect(b.getByText(/App B/)).not.toBeNull();
		// Each app's content is isolated in its own shadow root, so app A's label
		// must NOT be visible in app B's body.
		expect(b.queryByText(/App A/)).toBeNull();
		expect(a.queryByText(/App B/)).toBeNull();
	});

	test("interacting with one instance does not affect the other", async () => {
		const a = within(bodyOf("drafter-root--a"));
		const b = within(bodyOf("drafter-root--b"));

		// Both start at 0.
		expect(a.getByText(/Counter:\s*0/)).not.toBeNull();
		expect(b.getByText(/Counter:\s*0/)).not.toBeNull();

		// Click Increment twice in app A only.
		await userEvent.click(a.getByRole("button", { name: /increment/i }));
		await within(bodyOf("drafter-root--a")).findByText(/Counter:\s*1/);
		await userEvent.click(
			within(bodyOf("drafter-root--a")).getByRole("button", {
				name: /increment/i,
			}),
		);
		await within(bodyOf("drafter-root--a")).findByText(/Counter:\s*2/);

		// App B must be untouched.
		expect(
			within(bodyOf("drafter-root--b")).getByText(/Counter:\s*0/),
		).not.toBeNull();

		// Now click app B once; app A must keep its count.
		await userEvent.click(
			within(bodyOf("drafter-root--b")).getByRole("button", {
				name: /increment/i,
			}),
		);
		await within(bodyOf("drafter-root--b")).findByText(/Counter:\s*1/);
		expect(
			within(bodyOf("drafter-root--a")).getByText(/Counter:\s*2/),
		).not.toBeNull();
	});
});
