/**
 * Tests for the development-server helpers (js/src/debug/dev_server.ts):
 * remembering which documents the dev server served, and the stop request
 * (one POST to the internal stop endpoint, never throwing). The server half
 * is covered by the Python tests for the __drafter_stop_server endpoint.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import {
	isDevServerDocument,
	markDevServerDocument,
	ownerDocumentOf,
	requestDevServerStop,
	STOP_SERVER_PATH,
} from "../debug/dev_server";

afterEach(() => {
	delete (globalThis as { fetch?: unknown }).fetch;
});

function mockFetch(result: Promise<unknown>): jest.Mock {
	const mock = jest.fn(() => result);
	(globalThis as { fetch?: unknown }).fetch = mock;
	return mock;
}

describe("dev server documents", () => {
	test("a fresh document is not a dev server document", () => {
		const doc = document.implementation.createHTMLDocument("site");
		expect(isDevServerDocument(doc)).toBe(false);
	});

	test("marking a document is remembered for that document only", () => {
		const served = document.implementation.createHTMLDocument("served");
		const other = document.implementation.createHTMLDocument("other");
		markDevServerDocument(served);
		expect(isDevServerDocument(served)).toBe(true);
		expect(isDevServerDocument(other)).toBe(false);
	});

	test("ownerDocumentOf resolves documents and shadow roots", () => {
		expect(ownerDocumentOf(document)).toBe(document);
		const host = document.createElement("div");
		document.body.appendChild(host);
		const shadow = host.attachShadow({ mode: "open" });
		expect(ownerDocumentOf(shadow)).toBe(document);
		host.remove();
	});
});

describe("requestDevServerStop", () => {
	test("posts to the stop endpoint and reports acknowledgement", async () => {
		const fetchMock = mockFetch(Promise.resolve({ ok: true, status: 200 }));
		await expect(requestDevServerStop()).resolves.toBe(true);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [
			string,
			{ method: string },
		];
		expect(url).toBe(STOP_SERVER_PATH);
		expect(options.method).toBe("POST");
	});

	test("a rejected request reports failure", async () => {
		mockFetch(Promise.resolve({ ok: false, status: 503 }));
		await expect(requestDevServerStop()).resolves.toBe(false);
	});

	test("a network failure reports failure instead of throwing", async () => {
		mockFetch(Promise.reject(new Error("refused")));
		await expect(requestDevServerStop()).resolves.toBe(false);
	});

	test("no fetch at all reports failure", async () => {
		await expect(requestDevServerStop()).resolves.toBe(false);
	});
});
