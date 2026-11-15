/**
 * Unit tests for the per-app localStorage keys (js/src/storage_keys.ts).
 *
 * Everything Drafter remembers in the browser for one app (debug save
 * slots, the theme chosen in the theme switcher, the open debug tab) is
 * stored under a key that carries the app's scope: a hash of the page
 * address and of the main file's id. These tests pin what does and does
 * not change that scope. The Python half (the id the page embeds) is
 * covered by tests/test_main_file_id.py; the users of the keys by
 * debug-saveload.test.tsx, debug-tabs.test.tsx and config-overrides.test.ts.
 */
import { describe, expect, test } from "@jest/globals";

import {
	APP_STORAGE_PREFIX,
	appStorageKey,
	appStorageScope,
	hashText,
	mainFileId,
	pageAddress,
} from "../storage_keys";

/** A stand-in for the window an app renders into. */
function appWindow(url: string, fileId?: unknown): Window {
	const parsed = new URL(url);
	return {
		location: { origin: parsed.origin, pathname: parsed.pathname },
		DRAFTER_MAIN_FILE_ID: fileId,
	} as unknown as Window;
}

describe("hashText", () => {
	test("is stable, short, and hexadecimal", () => {
		expect(hashText("http://localhost:8080\nabc")).toBe(
			hashText("http://localhost:8080\nabc"),
		);
		expect(hashText("anything")).toMatch(/^[0-9a-f]{14}$/);
		expect(hashText("")).toMatch(/^[0-9a-f]{14}$/);
	});

	test("different texts get different hashes", () => {
		const hashes = new Set(
			["a", "b", "ab", "ba", "main.py", "Main.py", ""].map(hashText),
		);
		expect(hashes.size).toBe(7);
	});
});

describe("pageAddress", () => {
	test("is the origin and path, without the route or fragment", () => {
		expect(
			pageAddress(
				appWindow("https://ada.github.io/pets/?route=--about#top"),
			),
		).toBe("https://ada.github.io/pets");
	});

	test("the usual spellings of one address agree", () => {
		const spellings = [
			"https://ada.github.io/pets",
			"https://ada.github.io/pets/",
			"https://ada.github.io/pets/index.html",
			"https://ada.github.io/pets/index.htm",
		].map((url) => pageAddress(appWindow(url)));
		expect(new Set(spellings).size).toBe(1);
	});

	test("a window whose location cannot be read gives an empty address", () => {
		const locked = Object.defineProperty({}, "location", {
			get() {
				throw new Error("cross-origin");
			},
		}) as unknown as Window;

		expect(pageAddress(locked)).toBe("");
	});
});

describe("mainFileId", () => {
	test("reads the id the page template embedded", () => {
		expect(mainFileId(appWindow("http://localhost:8080/", "3f9a"))).toBe(
			"3f9a",
		);
	});

	test("is empty when the page carries none (or not a string)", () => {
		expect(mainFileId(appWindow("http://localhost:8080/"))).toBe("");
		expect(mainFileId(appWindow("http://localhost:8080/", 42))).toBe("");
	});
});

describe("appStorageScope", () => {
	test("two programs at one address have different scopes", () => {
		// The development server's usual case: both at localhost:8080.
		const first = appWindow("http://localhost:8080/", "aaaa1111");
		const second = appWindow("http://localhost:8080/", "bbbb2222");

		expect(appStorageScope(first)).not.toBe(appStorageScope(second));
	});

	test("one program at two addresses has different scopes", () => {
		// Two sites published under one github.io origin, both `main.py`.
		const first = appWindow("https://ada.github.io/pets/", "aaaa1111");
		const second = appWindow("https://ada.github.io/shop/", "aaaa1111");

		expect(appStorageScope(first)).not.toBe(appStorageScope(second));
	});

	test("moving between routes keeps the scope", () => {
		const home = appWindow("http://localhost:8080/", "aaaa1111");
		const about = appWindow(
			"http://localhost:8080/?route=--about",
			"aaaa1111",
		);

		expect(appStorageScope(about)).toBe(appStorageScope(home));
	});

	test("defaults to the page's own window", () => {
		expect(appStorageScope()).toBe(appStorageScope(window));
		expect(appStorageKey("debug.active-tab.v1")).toBe(
			appStorageKey("debug.active-tab.v1", window),
		);
	});
});

describe("appStorageKey", () => {
	test("is drafter.app.<scope>.<name>", () => {
		const win = appWindow("http://localhost:8080/", "aaaa1111");

		expect(appStorageKey("debug.active-tab.v1", win)).toBe(
			`${APP_STORAGE_PREFIX}${appStorageScope(win)}.debug.active-tab.v1`,
		);
		// The Browser Storage section offers to delete `drafter.` keys.
		expect(appStorageKey("anything", win).startsWith("drafter.")).toBe(
			true,
		);
	});

	test("neither the address nor the file id appears in the key", () => {
		const win = appWindow(
			"https://ada-lovelace.github.io/pets/",
			"aaaa1111",
		);

		const key = appStorageKey("debug.snapshot.v2.quick", win);

		expect(key).not.toContain("ada-lovelace");
		expect(key).not.toContain("aaaa1111");
	});
});
