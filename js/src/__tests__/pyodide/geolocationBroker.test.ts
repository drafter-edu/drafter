import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	geolocationBroker,
	resetGeolocationBrokerForTests,
} from "../../components/geolocationBroker";

type SuccessCallback = (position: GeolocationPosition) => void;
type ErrorCallback = (error: GeolocationPositionError) => void;

type GeolocationErrorCode = 1 | 2 | 3;

function makePosition(timestamp: number): GeolocationPosition {
	return {
		coords: {
			latitude: 39.68,
			longitude: -75.75,
			accuracy: 12.4,
			altitude: null,
			altitudeAccuracy: null,
			heading: null,
			speed: null,
			toJSON: () => ({}),
		},
		timestamp,
		toJSON: () => ({}),
	} as GeolocationPosition;
}

function makeGeoError(code: GeolocationErrorCode): GeolocationPositionError {
	return {
		code,
		message: code === 3 ? "Location request timed out" : "Location error",
		PERMISSION_DENIED: 1,
		POSITION_UNAVAILABLE: 2,
		TIMEOUT: 3,
	} as GeolocationPositionError;
}

describe("geolocationBroker", () => {
	let getCurrentPosition: jest.Mock;
	let nowSpy: jest.SpiedFunction<typeof Date.now>;
	let now = 1_000_000;

	beforeEach(() => {
		resetGeolocationBrokerForTests();
		getCurrentPosition = jest.fn();
		Object.defineProperty(window.navigator, "geolocation", {
			configurable: true,
			value: { getCurrentPosition },
		});
		now = 1_000_000;
		nowSpy = jest.spyOn(Date, "now").mockImplementation(() => now);
	});

	afterEach(() => {
		resetGeolocationBrokerForTests();
		nowSpy.mockRestore();
		delete (window.navigator as { geolocation?: unknown }).geolocation;
	});

	function callbacksFor(callIndex = 0): {
		success: SuccessCallback;
		failure: ErrorCallback;
		options: PositionOptions;
	} {
		const call = getCurrentPosition.mock.calls[callIndex] as [
			SuccessCallback,
			ErrorCallback,
			PositionOptions,
		];
		return { success: call[0], failure: call[1], options: call[2] };
	}

	test("deduplicates concurrent compatible requests into one browser request", async () => {
		const first = geolocationBroker.getPosition();
		const second = geolocationBroker.getPosition();

		expect(first).toBe(second);
		expect(getCurrentPosition).toHaveBeenCalledTimes(1);

		const position = makePosition(now - 500);
		callbacksFor().success(position);

		await expect(first).resolves.toBe(position);
		await expect(second).resolves.toBe(position);
	});

	test("uses a fresh cached position without another browser request", async () => {
		const first = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		callbacksFor().success(makePosition(now - 1_000));
		await first;

		const second = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		await second;

		expect(getCurrentPosition).toHaveBeenCalledTimes(1);
	});

	test("treats an expired cached position as stale and reacquires", async () => {
		const first = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		callbacksFor().success(makePosition(now - 8_000));
		await first;

		const second = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(1).success(makePosition(now));
		await second;
	});

	test("evaluates expiration from GeolocationPosition.timestamp", async () => {
		const first = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		callbacksFor().success(makePosition(now - 9_000));
		await first;

		now += 50;
		const second = geolocationBroker.getPosition({ maxAgeMs: 5_000 });
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(1).success(makePosition(now));
		await second;
	});

	test("forceRefresh bypasses settled cache", async () => {
		const first = geolocationBroker.getPosition({ maxAgeMs: 60_000 });
		callbacksFor().success(makePosition(now - 100));
		await first;

		const second = geolocationBroker.getPosition({
			maxAgeMs: 60_000,
			forceRefresh: true,
		});
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(1).success(makePosition(now));
		await second;
	});

	test("forceRefresh joins a compatible request already in flight", async () => {
		const inFlight = geolocationBroker.getPosition({ maxAgeMs: 60_000 });
		const joiner = geolocationBroker.getPosition({
			forceRefresh: true,
			maxAgeMs: 0,
		});

		expect(joiner).toBe(inFlight);
		expect(getCurrentPosition).toHaveBeenCalledTimes(1);

		callbacksFor().success(makePosition(now));
		await Promise.all([inFlight, joiner]);
	});

	test("does not cache failed acquisitions as successful results", async () => {
		const first = geolocationBroker.getPosition();
		callbacksFor().failure(makeGeoError(3));
		await expect(first).rejects.toMatchObject({ code: 3 });

		const second = geolocationBroker.getPosition();
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(1).success(makePosition(now));
		await expect(second).resolves.toMatchObject({ timestamp: now });
	});

	test("allows retry after rejection and shares rejection with concurrent callers", async () => {
		const first = geolocationBroker.getPosition();
		const second = geolocationBroker.getPosition();
		expect(first).toBe(second);

		callbacksFor().failure(makeGeoError(2));
		await expect(first).rejects.toMatchObject({ code: 2 });
		await expect(second).rejects.toMatchObject({ code: 2 });

		const retry = geolocationBroker.getPosition();
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(1).success(makePosition(now));
		await expect(retry).resolves.toMatchObject({ timestamp: now });
	});

	test("older request settlement cannot clear newer in-flight compatible request", async () => {
		const coarse = geolocationBroker.getPosition({
			enableHighAccuracy: false,
		});
		const fine = geolocationBroker.getPosition({
			enableHighAccuracy: true,
		});
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);

		callbacksFor(0).success(makePosition(now - 200));
		await coarse;

		const coarseJoiner = geolocationBroker.getPosition({
			enableHighAccuracy: false,
			forceRefresh: true,
		});
		expect(coarseJoiner).toBe(fine);
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);

		callbacksFor(1).success(makePosition(now));
		await expect(coarseJoiner).resolves.toMatchObject({ timestamp: now });
	});

	test("uses expected browser API options mapping", async () => {
		const request = geolocationBroker.getPosition({
			maxAgeMs: 42_000,
			timeoutMs: 2_500,
			enableHighAccuracy: true,
		});
		expect(callbacksFor().options).toEqual({
			maximumAge: 42_000,
			timeout: 2_500,
			enableHighAccuracy: true,
		});
		callbacksFor().success(makePosition(now));
		await request;
	});

	test("handles unsupported geolocation with a clear error", async () => {
		delete (window.navigator as { geolocation?: unknown }).geolocation;
		await expect(geolocationBroker.getPosition()).rejects.toThrow(
			"Geolocation is not supported by your browser",
		);
	});

	test("applies coarse/fine compatibility rules", async () => {
		const fine = geolocationBroker.getPosition({
			enableHighAccuracy: true,
		});
		const coarseJoin = geolocationBroker.getPosition({
			enableHighAccuracy: false,
			forceRefresh: true,
		});
		expect(coarseJoin).toBe(fine);
		expect(getCurrentPosition).toHaveBeenCalledTimes(1);
		callbacksFor(0).success(makePosition(now));
		await Promise.all([fine, coarseJoin]);

		resetGeolocationBrokerForTests();
		getCurrentPosition.mockReset();

		const coarse = geolocationBroker.getPosition({
			enableHighAccuracy: false,
		});
		const fineNeedsOwn = geolocationBroker.getPosition({
			enableHighAccuracy: true,
		});
		expect(fineNeedsOwn).not.toBe(coarse);
		expect(getCurrentPosition).toHaveBeenCalledTimes(2);
		callbacksFor(0).success(makePosition(now - 1_000));
		callbacksFor(1).success(makePosition(now));
		await Promise.all([coarse, fineNeedsOwn]);
	});
});
