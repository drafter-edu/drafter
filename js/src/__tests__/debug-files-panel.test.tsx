/**
 * Jest DOM tests for the debug panel's Host File System list
 * (js/src/debug/panels/files.tsx) and the request behind it
 * (requestHostFileListing in js/src/debug/dev_server.ts).
 *
 * The list shows the student's project folder as the local development
 * server reports it through its `__drafter_list_files` route
 * (list_user_files in src/drafter/app/app_server.py). `fetch` is mocked
 * with the JSON shape that route sends. The Client File System half of the
 * panel is covered by debug-panel.test.tsx.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { LIST_FILES_PATH, requestHostFileListing } from "../debug/dev_server";
import { FilesPanel } from "../debug/panels/files";

const CONTAINER_ID = "files-panel-container";

interface Listing {
	entries: Array<{ name: string; is_dir: boolean }>;
	summary: { total_entries: number; requested_path: string };
}

function listing(entries: Array<[string, boolean]>, path = "."): Listing {
	return {
		entries: entries.map(([name, is_dir]) => ({ name, is_dir })),
		summary: { total_entries: entries.length, requested_path: path },
	};
}

/**
 * Install a fetch that answers each folder with its listing, the way the
 * development server does; a folder missing from `folders` gets the 400 the
 * server sends for a path that is not a directory.
 */
function mockServer(folders: Record<string, Listing>): jest.Mock {
	const mock = jest.fn(async (url: unknown) => {
		const query = String(url).split("?path=")[1];
		const path = query === undefined ? "" : decodeURIComponent(query);
		const found = folders[path];
		if (!found) {
			return { ok: false, status: 400, json: async () => ({}) };
		}
		return { ok: true, status: 200, json: async () => found };
	});
	(globalThis as { fetch?: unknown }).fetch = mock;
	return mock;
}

/** Let the listing request and the render that follows it settle. */
async function flush(): Promise<void> {
	for (let i = 0; i < 5; i++) {
		await Promise.resolve();
	}
}

async function mountPanel(showHostFiles: boolean): Promise<FilesPanel> {
	document.body.innerHTML = `<div id="${CONTAINER_ID}"></div>`;
	const panel = new FilesPanel(CONTAINER_ID, 0, document, showHostFiles);
	(document.getElementById(CONTAINER_ID) as HTMLElement).appendChild(
		panel.createStructure() as unknown as Node,
	);
	panel.initialize();
	await flush();
	return panel;
}

function hostItems(): string[] {
	return Array.from(
		document.querySelectorAll(
			".drafter-debug-files-host .drafter-debug-files-list-items > *",
		),
	).map((item) => item.textContent ?? "");
}

function hostItem(label: string): HTMLElement {
	const match = Array.from(
		document.querySelectorAll<HTMLElement>(
			".drafter-debug-files-host .drafter-debug-files-list-items > *",
		),
	).find((item) => item.textContent === label);
	if (!match) {
		throw new Error(`No host entry labeled '${label}'`);
	}
	return match;
}

afterEach(() => {
	delete (globalThis as { fetch?: unknown }).fetch;
	document.body.innerHTML = "";
});

describe("requestHostFileListing", () => {
	test("asks the listing route and sorts folders first", async () => {
		const fetchMock = mockServer({
			"": listing([
				["website.py", false],
				["images", true],
				["data.csv", false],
				["assets", true],
			]),
		});

		const entries = await requestHostFileListing();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		expect(fetchMock.mock.calls[0][0]).toBe(LIST_FILES_PATH);
		expect(entries).toEqual([
			{ name: "assets", is_dir: true },
			{ name: "images", is_dir: true },
			{ name: "data.csv", is_dir: false },
			{ name: "website.py", is_dir: false },
		]);
	});

	test("a subfolder is asked for by its path, safely encoded", async () => {
		const fetchMock = mockServer({
			"my images/cats & dogs": listing([["ada.png", false]]),
		});

		const entries = await requestHostFileListing("my images/cats & dogs");

		expect(fetchMock.mock.calls[0][0]).toBe(
			`${LIST_FILES_PATH}?path=my%20images%2Fcats%20%26%20dogs`,
		);
		expect(entries).toEqual([{ name: "ada.png", is_dir: false }]);
	});

	test("no listing is reported as null, never thrown", async () => {
		// No fetch at all.
		expect(await requestHostFileListing()).toBeNull();
		// The server refuses (the route is off, or the folder is gone).
		mockServer({});
		expect(await requestHostFileListing()).toBeNull();
		// The server is unreachable.
		(globalThis as { fetch?: unknown }).fetch = jest.fn(async () => {
			throw new Error("refused");
		});
		expect(await requestHostFileListing()).toBeNull();
		// The answer is not a listing.
		(globalThis as { fetch?: unknown }).fetch = jest.fn(async () => ({
			ok: true,
			json: async () => ({ error: "Invalid path" }),
		}));
		expect(await requestHostFileListing()).toBeNull();
	});
});

describe("Host File System list", () => {
	test("is not built, and asks nothing, when host files are off", async () => {
		const fetchMock = mockServer({ "": listing([["website.py", false]]) });

		await mountPanel(false);

		expect(document.querySelector(".drafter-debug-files-host")).toBeNull();
		expect(fetchMock).not.toHaveBeenCalled();
	});

	test("fills with the project folder as soon as the panel is ready", async () => {
		mockServer({
			"": listing([
				["website.py", false],
				["images", true],
			]),
		});

		await mountPanel(true);

		expect(hostItems()).toEqual(["images/", "website.py"]);
	});

	test("Refresh shows the folder as it is now, without duplicates", async () => {
		const folders = { "": listing([["website.py", false]]) };
		mockServer(folders);
		await mountPanel(true);
		const refresh = document.querySelector(
			".drafter-debug-refresh-host-btn",
		) as HTMLButtonElement;

		refresh.click();
		await flush();
		expect(hostItems()).toEqual(["website.py"]);

		folders[""] = listing([
			["website.py", false],
			["scores.txt", false],
		]);
		refresh.click();
		await flush();
		expect(hostItems()).toEqual(["scores.txt", "website.py"]);
	});

	test("a folder opens when clicked and ../ goes back up", async () => {
		const fetchMock = mockServer({
			"": listing([
				["images", true],
				["website.py", false],
			]),
			images: listing([
				["pets", true],
				["logo.png", false],
			]),
			"images/pets": listing([["ada.png", false]]),
		});
		await mountPanel(true);

		hostItem("images/").click();
		await flush();
		expect(hostItems()).toEqual(["../", "pets/", "logo.png"]);

		hostItem("pets/").click();
		await flush();
		expect(hostItems()).toEqual(["../", "ada.png"]);
		expect(fetchMock.mock.calls.at(-1)?.[0]).toBe(
			`${LIST_FILES_PATH}?path=images%2Fpets`,
		);

		hostItem("../").click();
		await flush();
		expect(hostItems()).toEqual(["../", "pets/", "logo.png"]);

		hostItem("../").click();
		await flush();
		expect(hostItems()).toEqual(["images/", "website.py"]);
	});

	test("a folder opens from the keyboard too", async () => {
		mockServer({
			"": listing([["images", true]]),
			images: listing([["logo.png", false]]),
		});
		await mountPanel(true);

		hostItem("images/").dispatchEvent(
			new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
		);
		await flush();

		expect(hostItems()).toEqual(["../", "logo.png"]);
	});

	test("an empty folder says so", async () => {
		mockServer({
			"": listing([["empty", true]]),
			empty: listing([]),
		});
		await mountPanel(true);

		hostItem("empty/").click();
		await flush();

		expect(hostItems()).toEqual(["../", "This folder is empty."]);
	});

	test("a server that sends no listing is explained, not left blank", async () => {
		mockServer({});

		await mountPanel(true);

		expect(hostItems()).toHaveLength(1);
		expect(hostItems()[0]).toContain("did not send a list of files");
	});

	test("a folder that vanished can still be left", async () => {
		const folders: Record<string, Listing> = {
			"": listing([["images", true]]),
			images: listing([["logo.png", false]]),
		};
		mockServer(folders);
		await mountPanel(true);
		hostItem("images/").click();
		await flush();

		delete folders.images;
		(
			document.querySelector(
				".drafter-debug-refresh-host-btn",
			) as HTMLButtonElement
		).click();
		await flush();

		expect(hostItems()[0]).toBe("../");
		expect(hostItems()[1]).toContain("did not send a list of files");
		hostItem("../").click();
		await flush();
		expect(hostItems()).toEqual(["images/"]);
	});
});
