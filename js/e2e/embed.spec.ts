// Suite D of JS_TESTING_PLAN.md: multiple embedded instances sharing one
// Pyodide runtime (the docs shared-runtime shape), state fully isolated.

import { test, expect } from "playwright/test";

declare global {
	interface Window {
		bootInstances: () => Promise<void>;
	}
}

test("two shadow-DOM instances share one runtime with isolated state", async ({
	page,
}) => {
	await page.goto("/multi.html");
	await page.evaluate(() => window.bootInstances());

	const rootA = page.locator("#drafter-root--a");
	const rootB = page.locator("#drafter-root--b");

	// Playwright locators pierce open shadow roots.
	await expect(rootA).toContainText("Counter A");
	await expect(rootA).toContainText("Count: 0");
	await expect(rootB).toContainText("Counter B");
	await expect(rootB).toContainText("Count: 0");

	// Clicks in one instance never leak into the other.
	await rootA.getByRole("button", { name: "Increment" }).click();
	await expect(rootA).toContainText("Count: 1");
	await expect(rootB).toContainText("Count: 0");

	await rootA.getByRole("button", { name: "Increment" }).click();
	await rootB.getByRole("button", { name: "Increment" }).click();
	await expect(rootA).toContainText("Count: 2");
	await expect(rootB).toContainText("Count: 1");
});
