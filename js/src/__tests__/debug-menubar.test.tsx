/**
 * Unit tests for the header dropdown menu bar (js/src/debug/menubar.tsx):
 * open/close behavior, hover-switching, keyboard navigation, outside-click
 * dismissal, disabled items, and setItemEnabled. The concrete menu
 * definitions (Navigate/View/Edit/Save-Load/Help) and their CustomEvent
 * contracts are covered by debug-panel.test.tsx and event-contracts.test.ts.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { HeaderMenuBar } from "../debug/menubar";

afterEach(() => {
	document.body.innerHTML = "";
});

function makeMenuBar(): {
	menuBar: HeaderMenuBar;
	firstAction: ReturnType<typeof jest.fn>;
	secondAction: ReturnType<typeof jest.fn>;
} {
	const firstAction = jest.fn();
	const secondAction = jest.fn();
	const menuBar = new HeaderMenuBar([
		{
			id: "first",
			labelKey: "menu.navigate",
			items: [
				{
					labelKey: "button.home",
					className: "item-one",
					action: firstAction as () => void,
					separatorAfter: true,
				},
				{
					labelKey: "button.reset",
					className: "item-disabled",
					disabled: true,
				},
			],
		},
		{
			id: "second",
			labelKey: "menu.view",
			items: [
				{
					labelKey: "menu.view_source",
					className: "item-two",
					action: secondAction as () => void,
				},
			],
		},
	]);
	document.body.appendChild(menuBar.element);
	return { menuBar, firstAction, secondAction };
}

function menuButton(id: string): HTMLButtonElement {
	return document.querySelector(
		`.drafter-menu-button-${id}`,
	) as HTMLButtonElement;
}

function popup(id: string): HTMLElement {
	return document.querySelector(
		`.drafter-menu-popup-${id}`,
	) as HTMLElement;
}

describe("open/close", () => {
	test("popups start closed; clicking the button toggles its menu", () => {
		makeMenuBar();
		expect(popup("first").hidden).toBe(true);

		menuButton("first").click();
		expect(popup("first").hidden).toBe(false);
		expect(menuButton("first").getAttribute("aria-expanded")).toBe("true");

		menuButton("first").click();
		expect(popup("first").hidden).toBe(true);
		expect(menuButton("first").getAttribute("aria-expanded")).toBe(
			"false",
		);
	});

	test("opening one menu closes the other", () => {
		makeMenuBar();
		menuButton("first").click();
		menuButton("second").click();

		expect(popup("first").hidden).toBe(true);
		expect(popup("second").hidden).toBe(false);
	});

	test("hovering another top-level button switches menus while open", () => {
		makeMenuBar();
		menuButton("first").click();

		menuButton("second").dispatchEvent(
			new MouseEvent("mouseenter", { bubbles: false }),
		);

		expect(popup("first").hidden).toBe(true);
		expect(popup("second").hidden).toBe(false);
	});

	test("hover alone does not open a menu when all are closed", () => {
		makeMenuBar();

		menuButton("second").dispatchEvent(
			new MouseEvent("mouseenter", { bubbles: false }),
		);

		expect(popup("second").hidden).toBe(true);
	});

	test("clicking outside the menu bar closes the open menu", () => {
		makeMenuBar();
		menuButton("first").click();

		document.body.dispatchEvent(
			new MouseEvent("mousedown", { bubbles: true }),
		);

		expect(popup("first").hidden).toBe(true);
	});

	test("selecting an item runs its action and closes the menu", () => {
		const { firstAction } = makeMenuBar();
		menuButton("first").click();

		(document.querySelector(".item-one") as HTMLButtonElement).click();

		expect(firstAction).toHaveBeenCalledTimes(1);
		expect(popup("first").hidden).toBe(true);
	});

	test("disabled items do not run actions or close the menu", () => {
		makeMenuBar();
		menuButton("first").click();

		const disabledItem = document.querySelector(
			".item-disabled",
		) as HTMLButtonElement;
		expect(disabledItem.disabled).toBe(true);
		disabledItem.click();

		expect(popup("first").hidden).toBe(false);
	});

	test("separators render between items", () => {
		makeMenuBar();
		expect(
			popup("first").querySelector(".drafter-menu-separator"),
		).not.toBeNull();
	});
});

describe("keyboard", () => {
	function press(target: HTMLElement, key: string): void {
		target.dispatchEvent(
			new KeyboardEvent("keydown", { key, bubbles: true }),
		);
	}

	test("ArrowDown on a top-level button opens its menu", () => {
		makeMenuBar();

		press(menuButton("first"), "ArrowDown");

		expect(popup("first").hidden).toBe(false);
	});

	test("Escape inside a popup closes it", () => {
		makeMenuBar();
		menuButton("first").click();

		press(
			document.querySelector(".item-one") as HTMLElement,
			"Escape",
		);

		expect(popup("first").hidden).toBe(true);
	});

	test("ArrowRight inside a popup moves to the next menu", () => {
		makeMenuBar();
		menuButton("first").click();

		press(
			document.querySelector(".item-one") as HTMLElement,
			"ArrowRight",
		);

		expect(popup("first").hidden).toBe(true);
		expect(popup("second").hidden).toBe(false);
	});
});

describe("setItemEnabled", () => {
	test("enables a rendered-disabled item so its action runs", () => {
		const menuBar = new HeaderMenuBar([
			{
				id: "only",
				labelKey: "menu.saveload",
				items: [
					{
						labelKey: "menu.quick_save",
						className: "quick-save",
						disabled: true,
						action: () => {
							clicked = true;
						},
					},
				],
			},
		]);
		document.body.appendChild(menuBar.element);
		let clicked = false;
		const item = document.querySelector(
			".quick-save",
		) as HTMLButtonElement;

		item.click();
		expect(clicked).toBe(false);

		menuBar.setItemEnabled("quick-save", true);
		expect(item.disabled).toBe(false);
		item.click();
		expect(clicked).toBe(true);
	});
});
