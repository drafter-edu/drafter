import { test, expect } from "playwright/test";

declare global {
	interface Window {
		bootRuntime: () => Promise<void>;
		runExample: (code: string, presentErrors?: boolean) => Promise<void>;
	}
}

const COUNTER_APP = `
from drafter import *
hide_debug_information()

@dataclass
class State:
    count: int

@route
def index(state: State):
    return Page(state, [
        f"Count: {state.count}",
        Button("Increment", increment),
    ])

@route
def increment(state: State):
    state.count += 1
    return index(state)

start_server(State(0))
`;

test("boots Pyodide in the browser and runs an interactive counter app", async ({
	page,
}) => {
	const consoleErrors: string[] = [];
	page.on("console", (message) => {
		if (message.type() === "error") {
			consoleErrors.push(message.text());
		}
	});
	page.on("response", (response) => {
		if (response.status() >= 400) {
			consoleErrors.push(`${response.status()} ${response.url()}`);
		}
	});

	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, COUNTER_APP);

	const root = page.locator("#drafter-root--");
	await expect(root).toContainText("Count: 0");

	await page.getByRole("button", { name: "Increment" }).click();
	await expect(root).toContainText("Count: 1");
	await page.getByRole("button", { name: "Increment" }).click();
	await expect(root).toContainText("Count: 2");

	expect(consoleErrors).toEqual([]);
});

test("SharedArrayBuffer is available (COOP/COEP isolation for interrupts)", async ({
	page,
}) => {
	await page.goto("/harness.html");
	const isolated = await page.evaluate(() => ({
		crossOriginIsolated: window.crossOriginIsolated,
		hasSharedArrayBuffer: typeof SharedArrayBuffer !== "undefined",
	}));
	expect(isolated.crossOriginIsolated).toBe(true);
	expect(isolated.hasSharedArrayBuffer).toBe(true);
});
