// Deep links: a site opened with ?route=<name> in its URL starts on that
// route instead of the index. This is the form the deployed 404.html (and the
// dev server) redirect `/--about` into, so it is what makes
// "your address plus --about" work. The bridge reads the real window URL
// inside Pyodide, which jsdom cannot exercise faithfully.

import { test, expect } from "playwright/test";

declare global {
	interface Window {
		bootRuntime: () => Promise<void>;
		runExample: (code: string, presentErrors?: boolean) => Promise<void>;
	}
}

const ABOUT_APP = `
from drafter import *
hide_debug_information()
set_site_information(
    "Ada Lovelace",
    "Tracks a corgi's snacks.",
    "Icons from openmoji.org",
    "See planning.pdf in the repository.",
    ["https://example.com/snack-tracker"],
)

@route
def index(state: str):
    return Page(state, ["Welcome home", Button("About", "--about")])

start_server("ready")
`;

test("opening the site with ?route=--about starts on the About page", async ({
	page,
}) => {
	await page.goto("/harness.html?route=--about");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, ABOUT_APP);

	const root = page.locator("#drafter-root--");
	await expect(root).toContainText("Ada Lovelace");
	await expect(root).toContainText("Tracks a corgi's snacks.");
	await expect(root).not.toContainText("Welcome home");
	// The URL keeps naming the route, like any other history entry.
	expect(new URL(page.url()).searchParams.get("route")).toBe("--about");
});

test("without a route parameter the site still starts on the index", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, ABOUT_APP);

	await expect(page.locator("#drafter-root--")).toContainText("Welcome home");
});
