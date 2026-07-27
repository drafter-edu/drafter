import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/audioRecorder";
import { resetAudioBrokerForTests } from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio / MediaRecorder fakes — mirrors audio.test.ts.
// ---------------------------------------------------------------------------

class FakeAudioNode {
	connect = jest.fn();

	disconnect = jest.fn();
}

class FakeAudioContext {
	static instances: FakeAudioContext[] = [];

	state = "running";

	currentTime = 0;

	sampleRate = 48000;

	destination = new FakeAudioNode();

	constructor() {
		FakeAudioContext.instances.push(this);
	}

	addEventListener = jest.fn();

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
}

class FakeMediaRecorder {
	static instances: FakeMediaRecorder[] = [];

	state = "inactive";

	mimeType = "audio/webm";

	ondataavailable: ((event: { data: Blob }) => void) | null = null;

	onerror: (() => void) | null = null;

	onstop: (() => void) | null = null;

	constructor(public stream: MediaStream) {
		FakeMediaRecorder.instances.push(this);
	}

	start(): void {
		this.state = "recording";
	}

	stop(): void {
		this.state = "inactive";
		this.ondataavailable?.({ data: new Blob(["abc"]) });
		this.onstop?.();
	}
}

function installMediaRecorder(value: unknown): void {
	Object.defineProperty(window, "MediaRecorder", {
		configurable: true,
		writable: true,
		value,
	});
	(globalThis as { MediaRecorder?: unknown }).MediaRecorder = value;
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

function flushMicrotasks(times = 8): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
}

describe("drafter-audio-recorder (extended)", () => {
	let getUserMedia: jest.Mock;

	beforeEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
		FakeMediaRecorder.instances = [];
		installMediaRecorder(FakeMediaRecorder);
		getUserMedia = jest.fn();
		Object.defineProperty(window.navigator, "mediaDevices", {
			configurable: true,
			value: { getUserMedia },
		});
	});

	afterEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		removeFakeAudioContext();
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		delete (window as { MediaRecorder?: unknown }).MediaRecorder;
		delete (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
	});

	function createRecorder(
		attributes: Record<string, string> = { name: "voice" },
	): HTMLElement {
		const element = document.createElement("drafter-audio-recorder");
		for (const [name, value] of Object.entries(attributes)) {
			element.setAttribute(name, value);
		}
		document.body.appendChild(element);
		return element;
	}

	function getHiddenInput(element: HTMLElement): HTMLInputElement {
		const input = element.querySelector('input[type="hidden"]');
		if (!(input instanceof HTMLInputElement)) {
			throw new Error("Hidden input was not rendered");
		}
		return input;
	}

	function getStoredData(element: HTMLElement): Record<string, unknown> {
		return JSON.parse(getHiddenInput(element).value);
	}

	async function waitFor(
		predicate: () => boolean,
		attempts = 100,
	): Promise<void> {
		for (let i = 0; i < attempts; i += 1) {
			if (predicate()) {
				return;
			}
			await new Promise((resolve) => setTimeout(resolve, 10));
		}
		throw new Error("Condition was not met in time");
	}

	test("max-duration stops the recording automatically", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createRecorder({
			name: "voice",
			"max-duration": "120",
		});
		const recordListener = jest.fn();
		element.addEventListener("record", recordListener);

		element.querySelector("button")?.click();
		await waitFor(() => getStoredData(element).status === "recording");

		// Nobody presses stop; the max-duration timeout fires instead.
		await waitFor(() => getStoredData(element).status === "granted");
		expect(recordListener).toHaveBeenCalledTimes(1);
		const detail = (recordListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.size).toBeGreaterThan(0);
		expect(typeof detail.duration).toBe("number");
		expect(tracks[0].stop).toHaveBeenCalled();
	});

	test("denied permission stores denied and emits denied and error events", async () => {
		const error = new Error("Permission denied");
		error.name = "NotAllowedError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createRecorder({ name: "voice" });
		const deniedListener = jest.fn();
		const errorListener = jest.fn();
		element.addEventListener("denied", deniedListener);
		element.addEventListener("error", errorListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("denied");
		expect(stored.message).toBe("Microphone access denied");
		expect(deniedListener).toHaveBeenCalledTimes(1);
		expect(errorListener).toHaveBeenCalledTimes(1);
		// The denied rendering explains the problem.
		expect(
			element.querySelector(".drafter-microphone-error-message"),
		).not.toBeNull();
	});

	test("a missing microphone reports a not-found error", async () => {
		const error = new Error("Requested device not found");
		error.name = "NotFoundError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createRecorder({ name: "voice" });

		element.querySelector("button")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("No microphone was found");
	});

	test("a MediaRecorder that cannot be constructed reports an error and releases the mic", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		class ThrowingRecorder {
			constructor() {
				throw new Error("codec unsupported");
			}
		}
		installMediaRecorder(ThrowingRecorder);
		const element = createRecorder({ name: "voice" });
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("codec unsupported");
		expect(errorListener).toHaveBeenCalledTimes(1);
		expect(tracks[0].stop).toHaveBeenCalled();
	});

	test("a recorder error mid-take reports failure and releases the mic", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createRecorder({ name: "voice" });

		element.querySelector("button")?.click();
		await waitFor(() => getStoredData(element).status === "recording");

		FakeMediaRecorder.instances[0].onerror?.();
		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("Recording failed");
		expect(tracks[0].stop).toHaveBeenCalled();
	});

	test("re-record starts a fresh take with a new MediaRecorder", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockImplementation(() => {
			const { stream: freshStream } = makeFakeStream();
			return Promise.resolve(freshStream);
		});
		getUserMedia.mockReturnValueOnce(Promise.resolve(stream));
		const element = createRecorder({ name: "voice" });

		element.querySelector("button")?.click();
		await waitFor(() => getStoredData(element).status === "recording");
		const stopButton = Array.from(element.querySelectorAll("button")).find(
			(button) => button.textContent?.includes("Stop"),
		);
		stopButton?.click();
		await waitFor(() => getStoredData(element).status === "granted");
		expect(FakeMediaRecorder.instances).toHaveLength(1);

		const redoButton = Array.from(element.querySelectorAll("button")).find(
			(button) => button.textContent?.includes("Re-record"),
		);
		expect(redoButton).toBeDefined();
		redoButton!.click();
		await waitFor(() => getStoredData(element).status === "recording");
		expect(FakeMediaRecorder.instances).toHaveLength(2);
	});

	test("the elapsed label counts up while recording", async () => {
		jest.useFakeTimers();
		try {
			const { stream } = makeFakeStream();
			getUserMedia.mockReturnValue(Promise.resolve(stream));
			const element = createRecorder({ name: "voice" });

			element.querySelector("button")?.click();
			await flushMicrotasks();
			expect(getStoredData(element).status).toBe("recording");

			const elapsed = element.querySelector(
				".drafter-recorder-elapsed",
			) as HTMLSpanElement;
			expect(elapsed.textContent).toBe("⏺ 0:00");

			jest.advanceTimersByTime(1100);
			expect(elapsed.textContent).toBe("⏺ 0:01");

			// Tear down while the fake clock is still installed so the
			// pending elapsed/max-duration timers are cleared cleanly.
			element.remove();
		} finally {
			jest.useRealTimers();
		}
	});

	test("disconnecting mid-recording stops the recorder without a record event", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createRecorder({ name: "voice" });
		const recordListener = jest.fn();
		element.addEventListener("record", recordListener);

		element.querySelector("button")?.click();
		await waitFor(() => getStoredData(element).status === "recording");
		const recorder = FakeMediaRecorder.instances[0];
		expect(recorder.state).toBe("recording");

		element.remove();
		expect(recorder.state).toBe("inactive");
		expect(tracks[0].stop).toHaveBeenCalled();

		await flushMicrotasks();
		expect(recordListener).not.toHaveBeenCalled();
	});

	test("name updates rename the hidden field; show toggles visibility", () => {
		const element = createRecorder({ name: "voice" });
		element.setAttribute("name", "take");
		expect(getHiddenInput(element).name).toBe("take");

		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);
		element.setAttribute("show", "true");
		expect(element.hidden).toBe(false);
	});
});
