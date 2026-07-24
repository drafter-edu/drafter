import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	AudioBroker,
	audioBroker,
	MICROPHONE_UNSUPPORTED_ERROR,
	resetAudioBrokerForTests,
} from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio / getUserMedia fakes (jsdom has neither)
// ---------------------------------------------------------------------------

class FakeAudioContext {
	static instances: FakeAudioContext[] = [];

	state = "suspended";

	private listeners = new Map<string, Set<() => void>>();

	constructor() {
		FakeAudioContext.instances.push(this);
	}

	addEventListener = jest.fn((name: string, callback: () => void) => {
		if (!this.listeners.has(name)) {
			this.listeners.set(name, new Set());
		}
		this.listeners.get(name)?.add(callback);
	});

	dispatch(name: string): void {
		for (const callback of this.listeners.get(name) ?? []) {
			callback();
		}
	}

	resume = jest.fn(() => {
		this.state = "running";
		return Promise.resolve();
	});

	close = jest.fn(() => Promise.resolve());
}

function installFakeAudioContext(): void {
	FakeAudioContext.instances = [];
	Object.defineProperty(window, "AudioContext", {
		configurable: true,
		writable: true,
		value: FakeAudioContext,
	});
}

function removeFakeAudioContext(): void {
	delete (window as { AudioContext?: unknown }).AudioContext;
	delete (window as { webkitAudioContext?: unknown }).webkitAudioContext;
}

type TrackState = { readyState: string; stop: jest.Mock };

function makeFakeStream(): { stream: MediaStream; tracks: TrackState[] } {
	const track: TrackState = {
		readyState: "live",
		stop: jest.fn(() => {
			track.readyState = "ended";
		}),
	};
	const tracks = [track];
	const stream = {
		getAudioTracks: () => tracks,
		getTracks: () => tracks,
	} as unknown as MediaStream;
	return { stream, tracks };
}

function flushMicrotasks(times = 3): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
}

describe("audioBroker context and unlock", () => {
	beforeEach(() => {
		resetAudioBrokerForTests();
		installFakeAudioContext();
	});

	afterEach(() => {
		resetAudioBrokerForTests();
		removeFakeAudioContext();
	});

	test("isSupported reflects the presence of an AudioContext constructor", () => {
		expect(audioBroker.isSupported()).toBe(true);
		removeFakeAudioContext();
		expect(audioBroker.isSupported()).toBe(false);
	});

	test("getContext lazily creates a single shared context", () => {
		expect(FakeAudioContext.instances).toHaveLength(0);
		const first = audioBroker.getContext();
		const second = audioBroker.getContext();
		expect(first).not.toBeNull();
		expect(second).toBe(first);
		expect(FakeAudioContext.instances).toHaveLength(1);
	});

	test("getContext returns null without any constructor", () => {
		removeFakeAudioContext();
		expect(audioBroker.getContext()).toBeNull();
	});

	test("getContext falls back to webkitAudioContext", () => {
		delete (window as { AudioContext?: unknown }).AudioContext;
		Object.defineProperty(window, "webkitAudioContext", {
			configurable: true,
			writable: true,
			value: FakeAudioContext,
		});
		expect(audioBroker.isSupported()).toBe(true);
		expect(audioBroker.getContext()).toBeInstanceOf(FakeAudioContext);
	});

	test("isUnlocked tracks the context state", () => {
		expect(audioBroker.isUnlocked()).toBe(false);
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		expect(audioBroker.isUnlocked()).toBe(false);
		context.state = "running";
		expect(audioBroker.isUnlocked()).toBe(true);
	});

	test("requestUnlock resolves false when audio is unsupported", async () => {
		removeFakeAudioContext();
		await expect(audioBroker.requestUnlock()).resolves.toBe(false);
	});

	test("requestUnlock resumes a suspended context", async () => {
		await expect(audioBroker.requestUnlock()).resolves.toBe(true);
		const context = FakeAudioContext.instances[0];
		expect(context.resume).toHaveBeenCalledTimes(1);
		expect(audioBroker.isUnlocked()).toBe(true);
	});

	test("requestUnlock resolves true without resuming when already running", async () => {
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		context.state = "running";
		await expect(audioBroker.requestUnlock()).resolves.toBe(true);
		expect(context.resume).not.toHaveBeenCalled();
	});

	test("requestUnlock resolves false when resume rejects", async () => {
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		context.resume.mockImplementation(() =>
			Promise.reject(new Error("blocked")),
		);
		await expect(audioBroker.requestUnlock()).resolves.toBe(false);
	});

	test("requestUnlock resolves false when resume succeeds but state stays suspended", async () => {
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		context.resume.mockImplementation(() => Promise.resolve());
		await expect(audioBroker.requestUnlock()).resolves.toBe(false);
		expect(audioBroker.isUnlocked()).toBe(false);
	});

	test("onUnlocked fires synchronously when already unlocked", () => {
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		context.state = "running";
		const callback = jest.fn();
		audioBroker.onUnlocked(callback);
		expect(callback).toHaveBeenCalledTimes(1);
	});

	test("onUnlocked subscribers fire exactly once on unlock", async () => {
		const callback = jest.fn();
		audioBroker.onUnlocked(callback);
		expect(callback).not.toHaveBeenCalled();

		await audioBroker.requestUnlock();
		expect(callback).toHaveBeenCalledTimes(1);

		// Callbacks are one-shot: a second unlock does not re-fire them.
		await audioBroker.requestUnlock();
		expect(callback).toHaveBeenCalledTimes(1);
	});

	test("onUnlocked unsubscribe prevents the callback", async () => {
		const callback = jest.fn();
		const unsubscribe = audioBroker.onUnlocked(callback);
		unsubscribe();
		await audioBroker.requestUnlock();
		expect(callback).not.toHaveBeenCalled();
	});

	test("a statechange event notifies subscribers", () => {
		const callback = jest.fn();
		audioBroker.onUnlocked(callback);
		const context = audioBroker.getContext() as unknown as FakeAudioContext;
		context.state = "running";
		context.dispatch("statechange");
		expect(callback).toHaveBeenCalledTimes(1);
	});

	test("a document gesture unlocks pending subscribers", async () => {
		const callback = jest.fn();
		audioBroker.onUnlocked(callback);

		document.dispatchEvent(new Event("pointerdown"));
		await flushMicrotasks();
		expect(callback).toHaveBeenCalledTimes(1);
	});

	test("resetForTests closes the context and forgets it", () => {
		const first = audioBroker.getContext() as unknown as FakeAudioContext;
		audioBroker.resetForTests();
		expect(first.close).toHaveBeenCalledTimes(1);
		const second = audioBroker.getContext();
		expect(second).not.toBe(first);
		expect(FakeAudioContext.instances).toHaveLength(2);
	});
});

describe("audioBroker microphone sharing", () => {
	let getUserMedia: jest.Mock;

	beforeEach(() => {
		resetAudioBrokerForTests();
		installFakeAudioContext();
		getUserMedia = jest.fn();
		Object.defineProperty(window.navigator, "mediaDevices", {
			configurable: true,
			value: { getUserMedia },
		});
	});

	afterEach(() => {
		resetAudioBrokerForTests();
		removeFakeAudioContext();
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
	});

	test("rejects with a clear error when getUserMedia is unavailable", async () => {
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		await expect(audioBroker.getMicrophone()).rejects.toThrow(
			MICROPHONE_UNSUPPORTED_ERROR,
		);
	});

	test("concurrent getMicrophone callers share one getUserMedia request", async () => {
		const { stream } = makeFakeStream();
		let resolveRequest!: (stream: MediaStream) => void;
		getUserMedia.mockReturnValue(
			new Promise<MediaStream>((resolve) => {
				resolveRequest = resolve;
			}),
		);

		const first = audioBroker.acquireMicrophone();
		const second = audioBroker.getMicrophone();
		expect(getUserMedia).toHaveBeenCalledTimes(1);
		expect(getUserMedia).toHaveBeenCalledWith({ audio: true });

		resolveRequest(stream);
		await expect(first).resolves.toBe(stream);
		await expect(second).resolves.toBe(stream);
		audioBroker.releaseMicrophone();
	});

	test("a live acquired stream is reused without a second prompt", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));

		await audioBroker.acquireMicrophone();
		expect(audioBroker.peekMicrophone()).toBe(stream);

		await expect(audioBroker.getMicrophone()).resolves.toBe(stream);
		expect(getUserMedia).toHaveBeenCalledTimes(1);
		audioBroker.releaseMicrophone();
	});

	test("an uncounted getMicrophone with no consumers stops the tracks immediately", async () => {
		// Documents actual behavior: getMicrophone without acquireMicrophone
		// resolves with the stream, but since no consumer is registered the
		// tracks are stopped right away (recording indicator turns off).
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));

		await expect(audioBroker.getMicrophone()).resolves.toBe(stream);
		expect(tracks[0].stop).toHaveBeenCalledTimes(1);
		expect(audioBroker.peekMicrophone()).toBeNull();
	});

	test("permission denial rejects all sharers and allows retry", async () => {
		const denial = new Error("Permission denied");
		denial.name = "NotAllowedError";
		getUserMedia.mockReturnValueOnce(Promise.reject(denial));

		const first = audioBroker.getMicrophone();
		const second = audioBroker.getMicrophone();
		await expect(first).rejects.toThrow("Permission denied");
		await expect(second).rejects.toThrow("Permission denied");

		// The failed in-flight request is cleared, so a retry re-prompts.
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		await expect(audioBroker.acquireMicrophone()).resolves.toBe(stream);
		expect(getUserMedia).toHaveBeenCalledTimes(2);
		audioBroker.releaseMicrophone();
	});

	test("the microphone stays live until every acquirer releases", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));

		await audioBroker.acquireMicrophone();
		await audioBroker.acquireMicrophone();
		expect(getUserMedia).toHaveBeenCalledTimes(1);

		audioBroker.releaseMicrophone();
		expect(tracks[0].stop).not.toHaveBeenCalled();
		expect(audioBroker.peekMicrophone()).toBe(stream);

		audioBroker.releaseMicrophone();
		expect(tracks[0].stop).toHaveBeenCalledTimes(1);
		expect(audioBroker.peekMicrophone()).toBeNull();
	});

	test("a failed acquire releases its consumer slot", async () => {
		getUserMedia.mockReturnValueOnce(
			Promise.reject(new Error("Permission denied")),
		);
		await expect(audioBroker.acquireMicrophone()).rejects.toThrow(
			"Permission denied",
		);

		// If the failed acquire leaked its consumer count, this uncounted
		// getMicrophone would keep the tracks alive; instead they stop.
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		await audioBroker.getMicrophone();
		expect(tracks[0].stop).toHaveBeenCalledTimes(1);
	});

	test("releaseMicrophone never drives the consumer count negative", async () => {
		audioBroker.releaseMicrophone();
		audioBroker.releaseMicrophone();

		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		await audioBroker.acquireMicrophone();

		// One acquire after spurious releases: the stream must stay live.
		expect(tracks[0].stop).not.toHaveBeenCalled();
		expect(audioBroker.peekMicrophone()).toBe(stream);
		audioBroker.releaseMicrophone();
		expect(tracks[0].stop).toHaveBeenCalledTimes(1);
	});

	test("a dead stream is not reused: the next request re-prompts", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValueOnce(Promise.resolve(stream));
		await audioBroker.acquireMicrophone();

		// The track dies out from under us (device unplugged, revoked, ...).
		tracks[0].readyState = "ended";
		expect(audioBroker.peekMicrophone()).toBeNull();

		const fresh = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(fresh.stream));
		await expect(audioBroker.getMicrophone()).resolves.toBe(fresh.stream);
		expect(getUserMedia).toHaveBeenCalledTimes(2);
		audioBroker.releaseMicrophone();
	});

	test("resetForTests clears microphone state", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		await audioBroker.acquireMicrophone();
		expect(audioBroker.peekMicrophone()).toBe(stream);

		audioBroker.resetForTests();
		expect(audioBroker.peekMicrophone()).toBeNull();

		// Consumer count was cleared too: a fresh uncounted request stops
		// its tracks immediately, as with a pristine broker.
		const fresh = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(fresh.stream));
		await audioBroker.getMicrophone();
		expect(fresh.tracks[0].stop).toHaveBeenCalledTimes(1);
	});

	test("isMicrophoneSupported requires a callable getUserMedia", () => {
		expect(audioBroker.isMicrophoneSupported()).toBe(true);
		Object.defineProperty(window.navigator, "mediaDevices", {
			configurable: true,
			value: { getUserMedia: "not a function" },
		});
		expect(audioBroker.isMicrophoneSupported()).toBe(false);
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		expect(audioBroker.isMicrophoneSupported()).toBe(false);
	});
});

describe("AudioBroker instances", () => {
	beforeEach(() => {
		installFakeAudioContext();
	});

	afterEach(() => {
		removeFakeAudioContext();
	});

	test("separate broker instances own separate contexts", () => {
		const one = new AudioBroker();
		const two = new AudioBroker();
		expect(one.getContext()).not.toBe(two.getContext());
		one.resetForTests();
		two.resetForTests();
	});
});
