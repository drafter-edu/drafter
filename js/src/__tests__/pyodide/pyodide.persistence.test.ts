/**
 * End-to-end persistence: a Timer created with persistent=True must survive
 * simulated page reloads as the SAME DOM node — parked in the hidden footer
 * area while other pages show, adopted back when its page re-renders, and
 * evicted by RemovePersistent.
 *
 * A Timer (not a Clock) is used because a Clock dispatches its route on every
 * tick, including the immediate tick when it starts, which would re-render
 * the page mid-test; the Timer's finish route never fires within the test.
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { runStudentCode } from "../../pyodide.index";
import { setupPyodideWithLocalDrafter } from "./pyodide-test-harness";

const ROOT_ID = "drafter-root--p";

// The timer's duration is huge so its finish route never fires mid-test.
const persistenceApp = `
from drafter import *

hide_debug_information()

@dataclass
class State:
    visits: int

@route
def index(state: State):
    state.visits += 1
    return Page(state, [
        f"Home Page {state.visits}",
        Timer(600000, finished, persistent=True, id="my-clock"),
        Button("Go", other),
    ])

@route
def other(state: State):
    return Page(state, [
        "Other Page",
        Button("Back", index),
        Button("Cleanup", cleanup),
    ])

@route
def cleanup(state: State):
    return Page(state, [
        "Cleanup Page",
        RemovePersistent("my-clock"),
        Button("Home", index),
    ])

@route
def finished(state: State):
    return index(state)

start_server(State(0))
`;

function shadowOf(): ShadowRoot {
	const root = document.getElementById(ROOT_ID);
	expect(root).not.toBeNull();
	const host = root!.querySelector("#drafter-shadow-host--") as HTMLElement;
	expect(host).not.toBeNull();
	const shadow = host.shadowRoot;
	expect(shadow).not.toBeNull();
	return shadow!;
}

function bodyOf(): HTMLElement {
	const body = shadowOf().querySelector("#drafter-body--") as HTMLElement;
	expect(body).not.toBeNull();
	return body;
}

function parkingOf(): HTMLElement {
	const parking = shadowOf().querySelector(
		"#drafter-persist--",
	) as HTMLElement;
	expect(parking).not.toBeNull();
	return parking;
}

describe("Persistent components across page loads (Pyodide)", () => {
	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
		document.body.innerHTML = `<div id='${ROOT_ID}'></div>`;
		await runStudentCode({
			code: persistenceApp,
			rootElementId: ROOT_ID,
			useShadowDom: true,
			presentErrors: false,
		});
	});

	test("clock is parked, adopted back, and finally evicted", async () => {
		const page = () => within(bodyOf());

		// Initial page: the clock is rendered in the body, nothing parked.
		expect(page().getByText(/Home Page 1/)).not.toBeNull();
		const clock = bodyOf().querySelector("drafter-timer") as HTMLElement;
		expect(clock).not.toBeNull();
		expect(clock.getAttribute("data-drafter-persist-key")).toBe("my-clock");
		expect(parkingOf().childElementCount).toBe(0);
		// Tag the live node so we can prove the same node survives.
		clock.setAttribute("data-test-marker", "original");

		// Navigate away: the clock is parked in the footer, not destroyed.
		await userEvent.click(page().getByRole("button", { name: /go/i }));
		await within(bodyOf()).findByText(/Other Page/);
		expect(bodyOf().querySelector("drafter-timer")).toBeNull();
		expect(parkingOf().childElementCount).toBe(1);
		const parked = parkingOf().firstElementChild as HTMLElement;
		expect(parked.tagName.toLowerCase()).toBe("drafter-timer");
		expect(parked.getAttribute("data-test-marker")).toBe("original");

		// Navigate back: the parked node replaces the freshly-rendered clock.
		await userEvent.click(page().getByRole("button", { name: /back/i }));
		await within(bodyOf()).findByText(/Home Page 2/);
		const adopted = bodyOf().querySelector("drafter-timer") as HTMLElement;
		expect(adopted).not.toBeNull();
		expect(adopted.getAttribute("data-test-marker")).toBe("original");
		expect(parkingOf().childElementCount).toBe(0);
		// Exactly one clock: the fresh render must have been discarded.
		expect(bodyOf().querySelectorAll("drafter-timer")).toHaveLength(1);

		// Park it again, then visit the page with RemovePersistent.
		await userEvent.click(page().getByRole("button", { name: /go/i }));
		await within(bodyOf()).findByText(/Other Page/);
		expect(parkingOf().childElementCount).toBe(1);
		await userEvent.click(page().getByRole("button", { name: /cleanup/i }));
		await within(bodyOf()).findByText(/Cleanup Page/);
		expect(parkingOf().childElementCount).toBe(0);

		// Returning home now renders a brand-new clock (no marker).
		await userEvent.click(page().getByRole("button", { name: /home/i }));
		await within(bodyOf()).findByText(/Home Page 3/);
		const fresh = bodyOf().querySelector("drafter-timer") as HTMLElement;
		expect(fresh).not.toBeNull();
		expect(fresh.getAttribute("data-test-marker")).toBeNull();
	});
});
