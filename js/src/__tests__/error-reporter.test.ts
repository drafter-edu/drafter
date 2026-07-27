/**
 * Tests for the dev-server error reporter (js/src/debug/error_reporter.ts):
 * batching reports into one POST to the internal error-log endpoint,
 * disabling itself (once, quietly) when no dev server answers, and staying
 * silent in production mode. The server half is covered by the Python
 * tests for drafter.app.error_log / the __drafter_error_log endpoint.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import {
	DevServerErrorReporter,
	ERROR_LOG_PATH,
} from "../debug/error_reporter";
import type { ErrorDetailsJson } from "../debug/telemetry/errors";

function envelope(message: string): ErrorDetailsJson {
	return {
		id: "request.route_execution_failed",
		category: "request",
		severity: "error",
		message,
		details: "",
		traceback: null,
		context: {
			causation_id: null,
			route: "index",
			request_id: 3,
			response_id: null,
			dom_id: null,
			phase: null,
		},
		status_code: "error",
		recoverable: true,
	};
}

const consoleInfoSpy = jest
	.spyOn(console, "info")
	.mockImplementation(() => {});

afterEach(() => {
	consoleInfoSpy.mockClear();
	delete (globalThis as { fetch?: unknown }).fetch;
});

function mockFetchOk(): jest.Mock {
	const mock = jest.fn(() => Promise.resolve({ ok: true, status: 200 }));
	(globalThis as { fetch?: unknown }).fetch = mock;
	return mock;
}

function mockFetchFailing(): jest.Mock {
	const mock = jest.fn(() => Promise.reject(new Error("refused")));
	(globalThis as { fetch?: unknown }).fetch = mock;
	return mock;
}

describe("DevServerErrorReporter", () => {
	test("batches queued reports into one POST to the error-log endpoint", async () => {
		const fetchMock = mockFetchOk();
		const reporter = new DevServerErrorReporter();

		reporter.report(envelope("boom"));
		reporter.report(envelope("bang"));
		await reporter.flush();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [
			string,
			{ method: string; body: string },
		];
		expect(url).toBe(ERROR_LOG_PATH);
		expect(options.method).toBe("POST");
		const payload = JSON.parse(options.body);
		expect(payload.kind).toBe("drafter-error-report");
		expect(payload.reports).toHaveLength(2);
		expect(payload.reports[0].message).toBe("boom");
		// The same environment details as the bug report bundle ride along.
		expect(payload.system.userAgent).toBeTruthy();
		expect(payload.url).toBeTruthy();
	});

	test("oversized envelope fields are truncated before delivery", async () => {
		const fetchMock = mockFetchOk();
		const reporter = new DevServerErrorReporter();

		const big = envelope("boom");
		big.traceback = "x".repeat(50_000);
		big.details = "y".repeat(50_000);
		reporter.report(big);
		await reporter.flush();

		const [, options] = fetchMock.mock.calls[0] as [
			string,
			{ body: string },
		];
		const [report] = JSON.parse(options.body).reports;
		expect(report.traceback.length).toBeLessThan(10_000);
		expect(report.traceback).toContain("[truncated]");
		expect(report.details.length).toBeLessThan(10_000);
	});

	test("an empty queue never touches the network", async () => {
		const fetchMock = mockFetchOk();
		const reporter = new DevServerErrorReporter();

		await reporter.flush();

		expect(fetchMock).not.toHaveBeenCalled();
	});

	test("disables itself after the first failed delivery, with one message", async () => {
		const fetchMock = mockFetchFailing();
		const reporter = new DevServerErrorReporter();

		reporter.report(envelope("boom"));
		await reporter.flush();
		reporter.report(envelope("bang"));
		await reporter.flush();

		expect(fetchMock).toHaveBeenCalledTimes(1);
		expect(consoleInfoSpy).toHaveBeenCalledTimes(1);
	});

	test("a non-OK response also disables the reporter", async () => {
		const mock = jest.fn(() =>
			Promise.resolve({ ok: false, status: 404 }),
		);
		(globalThis as { fetch?: unknown }).fetch = mock;
		const reporter = new DevServerErrorReporter();

		reporter.report(envelope("boom"));
		await reporter.flush();
		reporter.report(envelope("bang"));
		await reporter.flush();

		expect(mock).toHaveBeenCalledTimes(1);
	});

	test("production mode suppresses reporting until debug mode returns", async () => {
		const fetchMock = mockFetchOk();
		const reporter = new DevServerErrorReporter();

		reporter.setDebugMode(false);
		reporter.report(envelope("boom"));
		await reporter.flush();
		expect(fetchMock).not.toHaveBeenCalled();

		reporter.setDebugMode(true);
		reporter.report(envelope("bang"));
		await reporter.flush();
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});
});
