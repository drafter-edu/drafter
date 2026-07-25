/**
 * Unit tests for the view-settings helpers: the theme switcher
 * (js/src/debug/theme_switch.tsx) and the page-HTML formatter used by the
 * View > View Page HTML dialog (js/src/debug/viewsource.tsx), plus the
 * relative-time formatting and system-status collection backing the
 * Save/Load menu and bug reports (js/src/debug/saveload.tsx).
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import {
	applyTheme,
	AVAILABLE_THEMES,
	getCurrentTheme,
	openThemeSwitcher,
} from "../debug/theme_switch";
import { formatHtml } from "../debug/viewsource";
import {
	collectSystemStatus,
	formatRelativeTime,
} from "../debug/saveload";

const OVERRIDES_KEY = "drafter.debug.configuration-overrides.v1";

afterEach(async () => {
	// Close any open dialogs so their listeners do not leak between tests.
	document
		.querySelectorAll<HTMLButtonElement>(".drafter-dialog-close")
		.forEach((button) => button.click());
	await new Promise((resolve) => setTimeout(resolve, 0));
	document.body.innerHTML = "";
	window.localStorage.clear();
	delete (window as { DRAFTER_MODIFIED_CONFIGURATION?: unknown })
		.DRAFTER_MODIFIED_CONFIGURATION;
});

describe("theme switching", () => {
	test("getCurrentTheme prefers the local override, then embedded config", () => {
		expect(getCurrentTheme()).toBeNull();

		(window as { DRAFTER_MODIFIED_CONFIGURATION?: unknown }).DRAFTER_MODIFIED_CONFIGURATION =
			{ client_server: { theme: "sakura" } };
		expect(getCurrentTheme()).toBe("sakura");

		window.localStorage.setItem(
			OVERRIDES_KEY,
			JSON.stringify({ theme: "mvp" }),
		);
		expect(getCurrentTheme()).toBe("mvp");
	});

	test("applyTheme stores the override (keeping others) and reloads", () => {
		window.localStorage.setItem(
			OVERRIDES_KEY,
			JSON.stringify({ title: "Kept" }),
		);
		const reload = jest.fn();

		applyTheme("skeleton", reload as () => void);

		expect(
			JSON.parse(window.localStorage.getItem(OVERRIDES_KEY) ?? "{}"),
		).toEqual({ title: "Kept", theme: "skeleton" });
		expect(reload).toHaveBeenCalledTimes(1);
	});

	test("the dialog lists every theme and marks the current one", () => {
		window.localStorage.setItem(
			OVERRIDES_KEY,
			JSON.stringify({ theme: "tacit" }),
		);

		openThemeSwitcher();

		const options = document.querySelectorAll(".drafter-theme-option");
		expect(options).toHaveLength(AVAILABLE_THEMES.length);
		const current = document.querySelector(
			".drafter-theme-option.is-current",
		) as HTMLElement;
		expect(current.textContent).toContain("tacit");
	});
});

describe("formatHtml", () => {
	test("indents nested tags and handles void elements", () => {
		const formatted = formatHtml(
			'<div class="page"><p>Hi<br/>there</p><img src="x"></div>',
		);
		expect(formatted).toBe(
			[
				'<div class="page">',
				"  <p>",
				"    Hi",
				"    <br/>",
				"    there",
				"  </p>",
				'  <img src="x">',
				"</div>",
			].join("\n"),
		);
	});

	test("collapses whitespace-only gaps between tags", () => {
		expect(formatHtml("<div>  \n  <span>a</span>  \n</div>")).toBe(
			["<div>", "  <span>", "    a", "  </span>", "</div>"].join("\n"),
		);
	});
});

describe("formatRelativeTime", () => {
	const now = new Date("2026-07-25T12:00:00Z");

	test("buckets ages into just now / minutes / hours / days", () => {
		expect(formatRelativeTime("2026-07-25T11:59:30Z", now)).toBe(
			"just now",
		);
		expect(formatRelativeTime("2026-07-25T11:55:00Z", now)).toBe(
			"5 min ago",
		);
		expect(formatRelativeTime("2026-07-25T09:00:00Z", now)).toBe(
			"3 hr ago",
		);
		expect(formatRelativeTime("2026-07-23T12:00:00Z", now)).toBe(
			"2 days ago",
		);
	});

	test("returns null for unparseable timestamps", () => {
		expect(formatRelativeTime("not a date", now)).toBeNull();
	});
});

describe("collectSystemStatus", () => {
	test("gathers browser facts and Drafter storage keys (names only)", () => {
		window.localStorage.setItem("drafter.debug.something.v1", "abcd");
		window.localStorage.setItem("unrelated", "zzz");

		const status = collectSystemStatus();

		expect(status.userAgent).toBe(navigator.userAgent);
		expect(status.language).toBe(navigator.language);
		expect(status.localStorageKeys).toEqual([
			{ key: "drafter.debug.something.v1", size: 4 },
		]);
		// Values are intentionally NOT collected (saved states may hold
		// personal data).
		expect(JSON.stringify(status)).not.toContain("abcd");
	});
});
