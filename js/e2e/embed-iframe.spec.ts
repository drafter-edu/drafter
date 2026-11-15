// Suite D of JS_TESTING_PLAN.md, iframe variant: the DrafterHost embedding
// path the documentation's editable demos use. A shared Pyodide runtime in
// the top-level page runs each embed's Python, rendering into the embed
// iframe's own document (custom elements defined by the bundle the iframe
// itself loads). Complements embed.spec.ts, which covers the same-page
// shadow-DOM instance shape.

import { test, expect } from "playwright/test";

declare global {
	interface Window {
		bootEmbeds: () => Promise<void>;
		restartEmbed: (instanceId: string, code?: string) => Promise<void>;
		detachEmbed: (instanceId: string) => Promise<void>;
		hostHas: (instanceId: string) => boolean;
	}
}

const REPLACEMENT_APP = `
from drafter import *
hide_debug_information()

@route
def index(state):
    return Page(state, ["Replacement app is live"])

start_server()
`;

test("iframe embeds share one runtime with isolated state, restart, and detach", async ({
	page,
}) => {
	await page.goto("/embed-iframes.html");
	await page.evaluate(() => window.bootEmbeds());

	const frameA = page.frameLocator("#frame-a");
	const frameB = page.frameLocator("#frame-b");

	// Both embeds rendered into their own documents from the shared runtime.
	await expect(frameA.locator("#drafter-root--")).toContainText("Counter A");
	await expect(frameA.locator("#drafter-root--")).toContainText("Count: 0");
	await expect(frameB.locator("#drafter-root--")).toContainText("Counter B");
	await expect(frameB.locator("#drafter-root--")).toContainText("Count: 0");

	// Interleaved clicks: state stays per-embed.
	await frameA.getByRole("button", { name: "Increment" }).click();
	await frameB.getByRole("button", { name: "Increment" }).click();
	await frameA.getByRole("button", { name: "Increment" }).click();
	await expect(frameA.locator("#drafter-root--")).toContainText("Count: 2");
	await expect(frameB.locator("#drafter-root--")).toContainText("Count: 1");

	// The host can push new code into a running embed (the docs editor path).
	await page.evaluate(
		(code) => window.restartEmbed("embed-a", code),
		REPLACEMENT_APP,
	);
	await expect(frameA.locator("#drafter-root--")).toContainText(
		"Replacement app is live",
	);
	// The sibling embed is untouched by the restart.
	await expect(frameB.locator("#drafter-root--")).toContainText("Count: 1");

	// Detaching one embed leaves the other fully interactive.
	await page.evaluate(() => window.detachEmbed("embed-a"));
	expect(await page.evaluate(() => window.hostHas("embed-a"))).toBe(false);
	expect(await page.evaluate(() => window.hostHas("embed-b"))).toBe(true);
	await frameB.getByRole("button", { name: "Increment" }).click();
	await expect(frameB.locator("#drafter-root--")).toContainText("Count: 2");
});

// An app that reaches into the page with `js`. The marker text and the
// document title tell which window `js` turned out to be.
const JS_USING_APP = (name: string) => `
from drafter import *
import js
hide_debug_information()

@route
def index(state):
    return Page(state, [
        Text("Marker ${name}", id="own-marker"),
        Button("Look", look),
    ])

@route
def look(state):
    from js import document
    found = document.getElementById("own-marker")
    return Page(state, [
        "Found: " + (str(found.textContent) if found else "nothing"),
        "Title: " + str(js.document.title),
    ])

start_server()
`;

test("each iframe embed's js is its own window, not the hosting page", async ({
	page,
}) => {
	await page.goto("/embed-iframes.html");
	await page.evaluate(() => window.bootEmbeds());
	await page.evaluate(
		(code) => window.restartEmbed("embed-a", code),
		JS_USING_APP("A"),
	);
	await page.evaluate(
		(code) => window.restartEmbed("embed-b", code),
		JS_USING_APP("B"),
	);

	const frameA = page.frameLocator("#frame-a");
	const frameB = page.frameLocator("#frame-b");
	const frameTitle = await page.frame({ url: /embed-frame\.html/ })!.title();
	expect(frameTitle).not.toBe(await page.title());

	// Clicked in the other order than they started, so "whichever ran last"
	// cannot pass for "its own".
	await frameB.getByRole("button", { name: "Look" }).click();
	await frameA.getByRole("button", { name: "Look" }).click();

	// Both a module-level `import js` and a `from js import` inside a route
	// reach the embed's own document.
	await expect(frameA.locator("#drafter-root--")).toContainText(
		"Found: Marker A",
	);
	await expect(frameB.locator("#drafter-root--")).toContainText(
		"Found: Marker B",
	);
	await expect(frameA.locator("#drafter-root--")).toContainText(
		`Title: ${frameTitle}`,
	);
	// The hosting page's own `js` is untouched: Drafter still drew each
	// app in its own frame, and the host page has no marker of its own.
	expect(await page.locator("#own-marker").count()).toBe(0);
});
