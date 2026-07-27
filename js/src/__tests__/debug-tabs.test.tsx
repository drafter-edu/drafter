/**
 * Unit tests for the debug panel's TabBar (js/src/debug/tabs.tsx):
 * activation, aria state, keyboard navigation, badges, and localStorage
 * persistence (including the invalid/missing-key fallbacks). The TabBar's
 * integration into DebugPanel is covered by debug-panel.test.tsx.
 */
import { afterEach, describe, expect, test } from "@jest/globals";

import { TabBar } from "../debug/tabs";

const STORAGE_KEY = "drafter.debug.active-tab.v1";

afterEach(() => {
	document.body.innerHTML = "";
	window.localStorage.clear();
});

function makeTabBar(instanceId: number = 0): TabBar {
	const tabBar = new TabBar(instanceId, [
		{
			id: "alpha",
			labelKey: "debug.tab.current",
			content: [(<div class="alpha-content">A</div>) as HTMLElement],
		},
		{
			id: "beta",
			labelKey: "debug.tab.history",
			content: [(<div class="beta-content">B</div>) as HTMLElement],
		},
		{
			id: "gamma",
			labelKey: "debug.tab.tests",
			content: [(<div class="gamma-content">C</div>) as HTMLElement],
		},
	]);
	document.body.appendChild(tabBar.createTabList());
	tabBar.createTabPanels().forEach((panel) =>
		document.body.appendChild(panel),
	);
	return tabBar;
}

function button(id: string): HTMLButtonElement {
	return document.querySelector(
		`[id^='drafter-debug-tab-btn-${id}-']`,
	) as HTMLButtonElement;
}

function panel(id: string): HTMLElement {
	return document.querySelector(
		`[role='tabpanel'][id^='drafter-debug-tab-${id}-']`,
	) as HTMLElement;
}

describe("activation", () => {
	test("first tab is active by default; content stays mounted when hidden", () => {
		makeTabBar();

		expect(button("alpha").getAttribute("aria-selected")).toBe("true");
		expect(panel("alpha").hidden).toBe(false);
		expect(panel("beta").hidden).toBe(true);
		// Hidden !== detached: inactive tab content is still in the DOM so
		// panels keep receiving telemetry updates.
		expect(document.querySelector(".beta-content")).not.toBeNull();
	});

	test("clicking a tab activates it and deactivates the rest", () => {
		const tabBar = makeTabBar();

		button("beta").click();

		expect(tabBar.getActiveTab()).toBe("beta");
		expect(button("alpha").getAttribute("aria-selected")).toBe("false");
		expect(button("beta").getAttribute("aria-selected")).toBe("true");
		expect(panel("alpha").hidden).toBe(true);
		expect(panel("beta").hidden).toBe(false);
		// Roving tabindex: only the active tab is in the tab order.
		expect(button("beta").tabIndex).toBe(0);
		expect(button("alpha").tabIndex).toBe(-1);
	});

	test("activate() ignores unknown tab ids", () => {
		const tabBar = makeTabBar();

		tabBar.activate("nonexistent");

		expect(tabBar.getActiveTab()).toBe("alpha");
		expect(panel("alpha").hidden).toBe(false);
	});
});

describe("persistence", () => {
	test("activation stores the tab id; a new TabBar restores it", () => {
		makeTabBar();
		button("gamma").click();
		expect(window.localStorage.getItem(STORAGE_KEY)).toBe("gamma");
		document.body.innerHTML = "";

		const restored = makeTabBar(1);

		expect(restored.getActiveTab()).toBe("gamma");
		expect(panel("gamma").hidden).toBe(false);
		expect(panel("alpha").hidden).toBe(true);
	});

	test("a stored id no tab uses falls back to the first tab", () => {
		window.localStorage.setItem(STORAGE_KEY, "no-such-tab");

		const tabBar = makeTabBar();

		expect(tabBar.getActiveTab()).toBe("alpha");
		expect(panel("alpha").hidden).toBe(false);
	});
});

describe("keyboard navigation", () => {
	function press(target: HTMLElement, key: string): void {
		target.dispatchEvent(
			new KeyboardEvent("keydown", { key, bubbles: true }),
		);
	}

	test("ArrowRight/ArrowLeft move and wrap; Home/End jump", () => {
		const tabBar = makeTabBar();

		press(button("alpha"), "ArrowRight");
		expect(tabBar.getActiveTab()).toBe("beta");

		press(button("beta"), "ArrowLeft");
		expect(tabBar.getActiveTab()).toBe("alpha");

		// Wraps around both ends.
		press(button("alpha"), "ArrowLeft");
		expect(tabBar.getActiveTab()).toBe("gamma");
		press(button("gamma"), "ArrowRight");
		expect(tabBar.getActiveTab()).toBe("alpha");

		press(button("alpha"), "End");
		expect(tabBar.getActiveTab()).toBe("gamma");
		press(button("gamma"), "Home");
		expect(tabBar.getActiveTab()).toBe("alpha");
	});
});

describe("badges", () => {
	test("setBadge shows a count with a variant; zero hides; 99+ caps", () => {
		const tabBar = makeTabBar();
		const badge = button("alpha").querySelector(
			".drafter-debug-tab-badge",
		) as HTMLElement;
		expect(badge.hidden).toBe(true);

		tabBar.setBadge("alpha", 3, "error");
		expect(badge.hidden).toBe(false);
		expect(badge.textContent).toBe("3");
		expect(badge.classList.contains("is-error")).toBe(true);

		// Variant changes swap the class.
		tabBar.setBadge("alpha", 2, "warn");
		expect(badge.classList.contains("is-warn")).toBe(true);
		expect(badge.classList.contains("is-error")).toBe(false);

		tabBar.setBadge("alpha", 150, "fail");
		expect(badge.textContent).toBe("99+");

		tabBar.setBadge("alpha", 0, "error");
		expect(badge.hidden).toBe(true);
	});

	test("setBadge on an unknown tab is a no-op", () => {
		const tabBar = makeTabBar();
		expect(() => tabBar.setBadge("nonexistent", 5, "error")).not.toThrow();
	});
});
