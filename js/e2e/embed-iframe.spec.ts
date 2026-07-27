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
