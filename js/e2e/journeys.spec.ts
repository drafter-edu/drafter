// Suite B of JS_TESTING_PLAN.md: drive real apps the way a student would.

import { test, expect } from "playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

declare global {
	interface Window {
		bootRuntime: () => Promise<void>;
		runExample: (code: string, presentErrors?: boolean) => Promise<void>;
	}
}

const ALL_FORMS = fs.readFileSync(
	path.resolve(__dirname, "..", "..", "examples", "all_forms.py"),
	"utf-8",
);

test("all_forms.py: every input type round-trips through submit", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, ALL_FORMS);

	const root = page.locator("#drafter-root--");
	await expect(root).toContainText("Please fill out the form below:");

	const name = page.locator('input[name="name_input"]');
	// CheckBox renders a hidden fallback input plus the real checkbox.
	const cool = page.locator('input[type="checkbox"][name="cool_checkbox"]');
	const when = page.locator('input[name="when_input"]');
	const atTime = page.locator('input[name="at_time_input"]');
	const birthday = page.locator('input[name="birthday_input"]');

	// Initial state from start_server(State("Bart", True, ...)).
	await expect(name).toHaveValue("Bart");
	await expect(cool).toBeChecked();
	await expect(birthday).toHaveValue("2010-04-01");

	await name.fill("Ada");
	await cool.uncheck();
	await when.fill("2024-01-15T14:30");
	await atTime.fill("08:45");
	await birthday.fill("2012-12-21");
	await page.getByRole("button", { name: "Submit" }).click();

	// The route writes the submitted values back into state and re-renders
	// the same form, so the new inputs echo what was submitted.
	await expect(name).toHaveValue("Ada");
	await expect(cool).not.toBeChecked();
	await expect(when).toHaveValue("2024-01-15T14:30");
	// Python's time type renders back with seconds.
	await expect(atTime).toHaveValue("08:45:00");
	await expect(birthday).toHaveValue("2012-12-21");
});

const TWO_PAGE_APP = `
from drafter import *
hide_debug_information()

@dataclass
class State:
    visits: int

@route
def index(state: State):
    return Page(state, [
        "Home page",
        f"Visits: {state.visits}",
        Button("Go to second", second),
    ])

@route
def second(state: State):
    state.visits += 1
    return Page(state, [
        "Second page",
        f"Visits: {state.visits}",
        Button("Go home", index),
    ])

start_server(State(0))
`;

test("multi-page app: navigation updates state and pages restore on back/forward", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, TWO_PAGE_APP);

	const root = page.locator("#drafter-root--");
	await expect(root).toContainText("Home page");
	await expect(root).toContainText("Visits: 0");

	await page.getByRole("button", { name: "Go to second" }).click();
	await expect(root).toContainText("Second page");
	await expect(root).toContainText("Visits: 1");

	await page.getByRole("button", { name: "Go home" }).click();
	await expect(root).toContainText("Home page");
	await expect(root).toContainText("Visits: 1");

	// Browser history integration: Back should restore the previous page.
	await page.goBack();
	await expect(root).toContainText("Second page");
	await page.goForward();
	await expect(root).toContainText("Home page");
});
