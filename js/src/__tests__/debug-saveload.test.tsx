/**
 * Unit tests for the Save/Load snapshot manager (js/src/debug/saveload.tsx):
 * the localStorage slot store (quick + named slots, most-recent pointer),
 * snapshot validation, the drafter-save-state / drafter-load-state event
 * round-trip, file downloads (mocked Blob URLs — jsdom has none), and the
 * bug-report bundle. The Python half of the round-trip is covered by
 * tests/test_bridge_snapshot.py.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import {
	SaveLoadManager,
	downloadBugReport,
	parseStoredSnapshot,
	type StoredSnapshot,
} from "../debug/saveload";
import type { StateSnapshotEvent } from "../debug/telemetry/snapshot";

const KEY_PREFIX = "drafter.debug.snapshot.v1.";

function snapshotEvent(
	overrides: Partial<StateSnapshotEvent> = {},
): StateSnapshotEvent {
	return {
		kind: "StateSnapshot",
		route: "guess",
		kwargs_json: '{"answer": 4}',
		state_json: '{"score": 7, "name": "Dot"}',
		state_type: "GameState",
		representation: null,
		reason: "save",
		slot: "quick",
		app_title: "My Site",
		version: 1,
		...overrides,
	} as StateSnapshotEvent;
}

function capture(name: string): CustomEvent[] {
	const seen: CustomEvent[] = [];
	window.addEventListener(name, ((event: Event) => {
		seen.push(event as CustomEvent);
	}) as EventListener);
	return seen;
}

afterEach(() => {
	document.body.innerHTML = "";
	window.localStorage.clear();
	jest.restoreAllMocks();
});

describe("slot storage", () => {
	test("a save snapshot lands in its slot and becomes most recent", () => {
		const manager = new SaveLoadManager();

		manager.handleSnapshot(snapshotEvent({ slot: "slot-3" }));

		const stored = parseStoredSnapshot(
			window.localStorage.getItem(`${KEY_PREFIX}slot-3`),
		) as StoredSnapshot;
		expect(stored.route).toBe("guess");
		expect(stored.kwargs_json).toBe('{"answer": 4}');
		expect(stored.state_json).toBe('{"score": 7, "name": "Dot"}');
		expect(stored.state_type).toBe("GameState");
		expect(stored.kind).toBe("drafter-state-snapshot");
		expect(window.localStorage.getItem(`${KEY_PREFIX}most-recent`)).toBe(
			"slot-3",
		);
		expect(manager.getSlot("slot-3")).not.toBeNull();
		expect(manager.getMostRecentSlot()).toBe("slot-3");
	});

	test("requestSave dispatches drafter-save-state with reason and slot", () => {
		const manager = new SaveLoadManager();
		const seen = capture("drafter-save-state");

		manager.requestSave("save", "slot-7");

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toEqual({ reason: "save", slot: "slot-7" });
	});

	test("getMostRecentSlot is null when the pointed-at slot is gone", () => {
		const manager = new SaveLoadManager();
		window.localStorage.setItem(`${KEY_PREFIX}most-recent`, "slot-9");

		expect(manager.getMostRecentSlot()).toBeNull();
	});
});

describe("loading", () => {
	test("loadSlot dispatches drafter-load-state with the stored invocation", () => {
		const manager = new SaveLoadManager();
		manager.handleSnapshot(snapshotEvent({ slot: "quick" }));
		const seen = capture("drafter-load-state");

		expect(manager.loadSlot("quick")).toBe(true);

		expect(seen).toHaveLength(1);
		expect(seen[0].detail).toEqual({
			state_json: '{"score": 7, "name": "Dot"}',
			route: "guess",
			kwargs_json: '{"answer": 4}',
		});
	});

	test("loadMostRecent follows the pointer", () => {
		const manager = new SaveLoadManager();
		manager.handleSnapshot(snapshotEvent({ slot: "slot-2", route: "a" }));
		manager.handleSnapshot(snapshotEvent({ slot: "slot-5", route: "b" }));
		const seen = capture("drafter-load-state");

		expect(manager.loadMostRecent()).toBe(true);

		expect(seen).toHaveLength(1);
		expect((seen[0].detail as { route: string }).route).toBe("b");
	});

	test("loadSlot on an empty slot dispatches nothing", () => {
		const manager = new SaveLoadManager();
		const seen = capture("drafter-load-state");

		expect(manager.loadSlot("slot-1")).toBe(false);

		expect(seen).toHaveLength(0);
	});
});

describe("validation", () => {
	test("rejects wrong kind, missing state data, and malformed JSON", () => {
		expect(parseStoredSnapshot(null)).toBeNull();
		expect(parseStoredSnapshot("not json at all")).toBeNull();
		expect(
			parseStoredSnapshot(
				JSON.stringify({ kind: "something-else", state_json: "{}" }),
			),
		).toBeNull();
		expect(
			parseStoredSnapshot(
				JSON.stringify({
					kind: "drafter-state-snapshot",
					version: 1,
					route: "guess",
					state_json: "",
				}),
			),
		).toBeNull();
	});

	test("accepts a well-formed stored snapshot", () => {
		const stored = parseStoredSnapshot(
			JSON.stringify({
				kind: "drafter-state-snapshot",
				version: 1,
				created: "2026-07-25T00:00:00Z",
				route: "guess",
				kwargs_json: "{}",
				state_json: '{"score": 1}',
				state_type: "GameState",
				app_title: "",
			}),
		);
		expect(stored).not.toBeNull();
		expect(stored?.route).toBe("guess");
	});
});

describe("downloads", () => {
	// jsdom's URL.createObjectURL/revokeObjectURL are writable but not
	// configurable, so mocks are installed and restored by assignment.
	const urlStatics = URL as unknown as {
		createObjectURL?: unknown;
		revokeObjectURL?: unknown;
	};
	const originalCreate = urlStatics.createObjectURL;
	const originalRevoke = urlStatics.revokeObjectURL;

	function mockBlobUrls(): { anchors: HTMLAnchorElement[] } {
		const anchors: HTMLAnchorElement[] = [];
		urlStatics.createObjectURL = jest.fn(() => "blob:mock-url");
		urlStatics.revokeObjectURL = jest.fn();
		jest.spyOn(
			HTMLAnchorElement.prototype,
			"click",
		).mockImplementation(function (this: HTMLAnchorElement) {
			anchors.push(this);
		});
		return { anchors };
	}

	afterEach(() => {
		urlStatics.createObjectURL = originalCreate;
		urlStatics.revokeObjectURL = originalRevoke;
	});

	test("a download-reason snapshot triggers a file download, not storage", () => {
		const { anchors } = mockBlobUrls();
		const manager = new SaveLoadManager();

		manager.handleSnapshot(snapshotEvent({ reason: "download" }));

		expect(anchors).toHaveLength(1);
		expect(anchors[0].download).toContain("drafter-snapshot-guess");
		expect(window.localStorage.getItem(`${KEY_PREFIX}quick`)).toBeNull();
	});

	test("downloadBugReport bundles events and environment context", () => {
		const { anchors } = mockBlobUrls();

		downloadBugReport([{ kind: "RouteAdded" }]);

		expect(anchors).toHaveLength(1);
		expect(anchors[0].download).toContain("drafter-bug-report");
	});

	test("downloads degrade to a console warning without Blob URL support", () => {
		const warnSpy = jest
			.spyOn(console, "warn")
			.mockImplementation(() => {});
		urlStatics.createObjectURL = undefined;
		const manager = new SaveLoadManager();

		manager.handleSnapshot(snapshotEvent({ reason: "download" }));

		expect(warnSpy).toHaveBeenCalled();
	});
});
