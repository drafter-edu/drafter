/**
 * Tests for the debug panel's "Stop Server" control (js/src/debug/index.tsx
 * together with js/src/debug/dev_server.ts): the Navigate menu item exists
 * only on documents served by the local development server, the menu path
 * asks for confirmation before POSTing to the stop endpoint, the page-button
 * path (used by the --stop-server system route through the client bridge)
 * skips the confirmation, and the outcome is reported in a dialog.
 *
 * Marking a document as dev-server-served is sticky for that document, and
 * jsdom keeps one document per test file, so the "not served" case runs
 * first and the remaining tests mark the document once.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { DebugPanel } from "../debug/index";
import { markDevServerDocument, STOP_SERVER_PATH } from "../debug/dev_server";
import type { ClientBridgeWrapperInterface } from "../types/client_bridge_wrapper";

const CONTAINER_ID = "drafter-debug-container";

function mountHost(): void {
	document.body.innerHTML = [
		'<div class="drafter-header--"></div>',
		'<div class="drafter-footer--"></div>',
		`<div id="${CONTAINER_ID}"></div>`,
	].join("");
}

function makeBridge(): ClientBridgeWrapperInterface {
	return { goto: jest.fn() } as unknown as ClientBridgeWrapperInterface;
}

function createPanel(): DebugPanel {
	mountHost();
	return new DebugPanel(CONTAINER_ID, makeBridge());
}

function stopMenuItem(): HTMLElement | null {
	return document.querySelector(".drafter-menu-item-stop-server");
}

function dialogs(): HTMLElement[] {
	return Array.from(document.querySelectorAll(".drafter-dialog"));
}

function dialogButton(label: string): HTMLButtonElement {
	const buttons = Array.from(
		document.querySelectorAll<HTMLButtonElement>(".drafter-dialog-button"),
	);
	const match = buttons.find(
		(button) => button.textContent?.trim() === label,
	);
	if (!match) {
		throw new Error(`No dialog button labeled '${label}'`);
	}
	return match;
}

/** Let queued microtasks and the async dialog handlers settle. */
function flush(): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, 0));
}

function mockFetch(result: Promise<unknown>): jest.Mock {
	const mock = jest.fn(() => result);
	(globalThis as { fetch?: unknown }).fetch = mock;
	return mock;
}

afterEach(() => {
	delete (globalThis as { fetch?: unknown }).fetch;
	document.body.innerHTML = "";
});

describe("outside the development server", () => {
	test("the Navigate menu has no Stop Server item", () => {
		createPanel();
		expect(stopMenuItem()).toBeNull();
	});

	test("stopServer only explains that there is nothing to stop", async () => {
		const panel = createPanel();
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));

		const outcome = panel.stopServer(false);
		await flush();

		expect(dialogs()).toHaveLength(1);
		expect(dialogs()[0].textContent).toContain("no server to stop");
		dialogButton("OK").click();
		await expect(outcome).resolves.toBe(false);
		expect(fetchMock).not.toHaveBeenCalled();
	});
});

describe("on the development server", () => {
	test("the Navigate menu offers Stop Server after About", () => {
		markDevServerDocument(document);
		createPanel();
		const item = stopMenuItem();
		expect(item).not.toBeNull();
		expect(item?.textContent).toContain("Stop Server");
		const about = document.querySelector(".drafter-menu-item-about");
		expect(about?.compareDocumentPosition(item as Node)).toBe(
			Node.DOCUMENT_POSITION_FOLLOWING,
		);
	});

	test("the menu item asks for confirmation before stopping", async () => {
		const panel = createPanel();
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));

		const outcome = panel.stopServer();
		await flush();

		expect(dialogs()).toHaveLength(1);
		expect(dialogs()[0].textContent).toContain("Ctrl+C");
		expect(fetchMock).not.toHaveBeenCalled();
		dialogButton("Stop Server").click();
		await flush();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [
			string,
			{ method: string },
		];
		expect(url).toBe(STOP_SERVER_PATH);
		expect(options.method).toBe("POST");
		expect(dialogs()[0].textContent).toContain("The server has stopped");
		dialogButton("OK").click();
		await expect(outcome).resolves.toBe(true);
	});

	test("cancelling the confirmation leaves the server running", async () => {
		const panel = createPanel();
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));

		const outcome = panel.stopServer();
		await flush();
		dialogButton("Cancel").click();

		await expect(outcome).resolves.toBe(false);
		expect(fetchMock).not.toHaveBeenCalled();
		expect(dialogs()).toHaveLength(0);
	});

	test("the page button path stops without a second confirmation", async () => {
		const panel = createPanel();
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));

		const outcome = panel.stopServer(false);
		await flush();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		expect(dialogs()).toHaveLength(1);
		expect(dialogs()[0].textContent).toContain("The server has stopped");
		dialogButton("OK").click();
		await expect(outcome).resolves.toBe(true);
	});

	test("an unreachable server is reported, not thrown", async () => {
		const panel = createPanel();
		mockFetch(Promise.reject(new Error("refused")));

		const outcome = panel.stopServer(false);
		await flush();

		expect(dialogs()[0].textContent).toContain("could not reach the server");
		dialogButton("OK").click();
		await expect(outcome).resolves.toBe(false);
	});

	test("the menu item click runs the confirmation flow", async () => {
		createPanel();
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));

		(stopMenuItem() as HTMLElement).click();
		await flush();

		expect(dialogs()).toHaveLength(1);
		expect(fetchMock).not.toHaveBeenCalled();
		dialogButton("Cancel").click();
		await flush();
		expect(dialogs()).toHaveLength(0);
	});
});
