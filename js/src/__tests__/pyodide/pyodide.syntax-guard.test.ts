/**
 * Syntax pre-flight guard: introducing a syntax error while live-editing must
 * NOT take down the running site. The restart path compile-checks the new
 * code before tearing anything down, so broken code leaves the previous
 * version running (with an error dialog), and a first run that cannot
 * compile renders a friendly error page instead of a blank root.
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import { within, screen } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import {
	createDrafterInstance,
	type DrafterInstanceHandle,
} from "../../pyodide.index";
import { setupPyodideWithLocalDrafter } from "./pyodide-test-harness";

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

// Missing closing parenthesis and colon: cannot compile.
const BROKEN_CODE = `
from drafter import *

@route
def index(state
    return Page(state, ["Broken"])

start_server(None)
`;

function drafterBody(): HTMLElement {
	const body = document.querySelector("#drafter-body--") as HTMLElement;
	expect(body).not.toBeNull();
	return body;
}

describe("Syntax error guard (Pyodide)", () => {
	let handle: DrafterInstanceHandle;

	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	test("starts a working site", async () => {
		handle = await createDrafterInstance({
			verbose: false,
			inlineCode: counterApp("Working Site"),
		});
		expect(drafterBody().textContent).toContain("Working Site");
	});

	test("a syntax error on restart keeps the previous site running", async () => {
		await expect(handle.restart(BROKEN_CODE)).rejects.toThrow(
			/SyntaxError/,
		);

		// The previous version must still be on screen...
		expect(drafterBody().textContent).toContain("Working Site");

		// ...and the student must be told what happened (the dialog, and
		// possibly the debug panel's problem indicator, carry the message).
		const notices = await screen.findAllByText(
			/last working version of your site/,
		);
		expect(notices.length).toBeGreaterThan(0);
		await userEvent.click(screen.getByRole("button", { name: /^OK$/ }));

		// The surviving site must still be interactive, not a dead render.
		await userEvent.click(
			within(drafterBody()).getByRole("button", { name: /increment/i }),
		);
		await within(drafterBody()).findByText(/Counter:\s*1/);
	});

	test("fixing the code restarts into the new version", async () => {
		await handle.restart(counterApp("Fixed Site"));
		expect(drafterBody().textContent).toContain("Fixed Site");
		expect(drafterBody().textContent).toContain("Counter: 0");
	});

	test("a syntax error on first run renders a friendly error page", async () => {
		document.body.insertAdjacentHTML(
			"beforeend",
			"<div id='drafter-root--fresh'></div>",
		);
		await expect(
			createDrafterInstance({
				verbose: false,
				inlineCode: BROKEN_CODE,
				rootElementId: "drafter-root--fresh",
				instanceId: "fresh-broken-instance",
			}),
		).rejects.toThrow(/SyntaxError/);

		const root = document.getElementById("drafter-root--fresh");
		expect(root).not.toBeNull();
		expect(root!.querySelector(".drafter-system-error")).not.toBeNull();
		expect(root!.textContent).toContain(
			"could not start your site because the code has a syntax error",
		);
		// The guard points at the offending line.
		expect(root!.textContent).toMatch(/line \d+ of main\.py/);
	});
});
