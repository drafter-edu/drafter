import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/tone";
import "../components/melody";
import "../components/microphone";
import "../components/audioRecorder";
import { resetAudioBrokerForTests } from "../components/audioBroker";
import {
	noteToFrequency,
	parseEffectConfigs,
	parseMelodyNotes,
	parseNumberAttribute,
	pitchToFrequency,
} from "../components/audioGraph";

// ---------------------------------------------------------------------------
// Web Audio fakes (jsdom has no AudioContext)
// ---------------------------------------------------------------------------

class FakeAudioParam {
	value = 0;

	setValueAtTime = jest.fn();

	linearRampToValueAtTime = jest.fn();
}

class FakeAudioNode {
	connect = jest.fn();

	disconnect = jest.fn();
}

class FakeOscillator extends FakeAudioNode {
	type = "sine";

	frequency = new FakeAudioParam();

	onended: (() => void) | null = null;

	started: number[] = [];

	stopped: number[] = [];

	start = jest.fn((when: number = 0) => {
		this.started.push(when);
	});

	stop = jest.fn((when: number = 0) => {
		this.stopped.push(when);
	});
}

class FakeGainNode extends FakeAudioNode {
	gain = new FakeAudioParam();
}

class FakeAnalyserNode extends FakeAudioNode {
	fftSize = 2048;

	get frequencyBinCount() {
		return this.fftSize / 2;
	}

	timeDomainValue = 128;

	frequencyPeakIndex = -1;

	getByteTimeDomainData = (data: Uint8Array) => {
		data.fill(this.timeDomainValue);
	};

	getByteFrequencyData = (data: Uint8Array) => {
		data.fill(0);
		if (this.frequencyPeakIndex >= 0) {
			data[this.frequencyPeakIndex] = 255;
		}
	};
}

class FakeAudioContext {
	static instances: FakeAudioContext[] = [];

	state = "running";

	currentTime = 0;

	sampleRate = 48000;

	destination = new FakeAudioNode();

	oscillators: FakeOscillator[] = [];

	analysers: FakeAnalyserNode[] = [];

	constructor() {
		FakeAudioContext.instances.push(this);
	}

	addEventListener = jest.fn();

	resume = jest.fn(() => {
		this.state = "running";
		return Promise.resolve();
	});

	close = jest.fn(() => Promise.resolve());

	createOscillator = () => {
		const oscillator = new FakeOscillator();
		this.oscillators.push(oscillator);
		return oscillator;
	};

	createGain = () => new FakeGainNode();

	createAnalyser = () => {
		const analyser = new FakeAnalyserNode();
		this.analysers.push(analyser);
		return analyser;
	};

	createMediaStreamSource = jest.fn(() => new FakeAudioNode());
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

function flushMicrotasks(times = 3): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
}

function createElement(
	tagName: string,
	attributes: Record<string, string>,
): HTMLElement {
	const element = document.createElement(tagName);
	for (const [name, value] of Object.entries(attributes)) {
		element.setAttribute(name, value);
	}
	document.body.appendChild(element);
	return element;
}

// ---------------------------------------------------------------------------
// Pure helpers
// ---------------------------------------------------------------------------

describe("audioGraph helpers", () => {
	test("noteToFrequency matches equal temperament", () => {
		expect(noteToFrequency("A4")).toBeCloseTo(440, 3);
		expect(noteToFrequency("C4")).toBeCloseTo(261.6256, 3);
		expect(noteToFrequency("F#3")).toBeCloseTo(
			noteToFrequency("Gb3") as number,
			6,
		);
		expect(noteToFrequency("a5")).toBeCloseTo(880, 3);
	});

	test("noteToFrequency rejects invalid names", () => {
		for (const bad of ["H4", "C", "#4", "C#", "C44", "rest", ""]) {
			expect(noteToFrequency(bad)).toBeNull();
		}
	});

	test("pitchToFrequency accepts raw frequencies and note names", () => {
		expect(pitchToFrequency("440")).toBe(440);
		expect(pitchToFrequency("C4")).toBeCloseTo(261.6256, 3);
		expect(pitchToFrequency("banana")).toBeNull();
		expect(pitchToFrequency("-5")).toBeNull();
	});

	test("parseMelodyNotes normalizes pairs and rests, skipping junk", () => {
		const notes = parseMelodyNotes(
			JSON.stringify([
				["C4", 2],
				["rest", 1],
				["X9", 1],
				["E4", -3],
			]),
		);
		expect(notes).toHaveLength(3);
		expect(notes[0]).toMatchObject({ note: "C4", beats: 2 });
		expect(notes[1]).toMatchObject({ note: "rest", frequency: 0 });
		expect(notes[2]).toMatchObject({ note: "E4", beats: 1 });
	});

	test("parseMelodyNotes tolerates malformed JSON", () => {
		expect(parseMelodyNotes("{oops")).toEqual([]);
		expect(parseMelodyNotes(null)).toEqual([]);
	});

	test("parseEffectConfigs keeps only typed objects", () => {
		const configs = parseEffectConfigs(
			JSON.stringify([
				{ type: "echo", delay: 0.2 },
				{ notype: true },
				"junk",
			]),
		);
		expect(configs).toEqual([{ type: "echo", delay: 0.2 }]);
		expect(parseEffectConfigs("{oops")).toEqual([]);
	});

	test("parseNumberAttribute clamps and defaults", () => {
		expect(parseNumberAttribute("0.5", 1, 0, 1)).toBe(0.5);
		expect(parseNumberAttribute("7", 1, 0, 1)).toBe(1);
		expect(parseNumberAttribute("junk", 0.25, 0, 1)).toBe(0.25);
		expect(parseNumberAttribute(null, 0.25, 0, 1)).toBe(0.25);
	});
});

// ---------------------------------------------------------------------------
// drafter-tone
// ---------------------------------------------------------------------------

describe("drafter-tone", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
	});

	afterEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		removeFakeAudioContext();
	});

	test("renders a play button labeled with the note", () => {
		const element = createElement("drafter-tone", { pitch: "C4" });
		const button = element.querySelector("button");
		expect(button?.textContent).toBe("▶ C4");
	});

	test("clicking play emits start and finish with the frequency", async () => {
		const element = createElement("drafter-tone", {
			pitch: "A4",
			duration: "250",
			waveform: "square",
		});
		const startListener = jest.fn();
		const finishListener = jest.fn();
		element.addEventListener("start", startListener);
		element.addEventListener("finish", finishListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		expect(startListener).toHaveBeenCalledTimes(1);
		const startDetail = (
			startListener.mock.calls[0][0] as CustomEvent
		).detail as Record<string, unknown>;
		expect(startDetail.frequency).toBe(440);
		expect(startDetail.note).toBe("A4");
		expect(startDetail.duration).toBe(250);
		expect(startDetail.waveform).toBe("square");

		const context = FakeAudioContext.instances[0];
		expect(context.oscillators).toHaveLength(1);
		const oscillator = context.oscillators[0];
		expect(oscillator.type).toBe("square");
		expect(oscillator.frequency.value).toBe(440);

		oscillator.onended?.();
		expect(finishListener).toHaveBeenCalledTimes(1);
	});

	test("emits an error event when audio is unsupported", async () => {
		removeFakeAudioContext();
		const element = createElement("drafter-tone", { pitch: "C4" });
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		expect(errorListener).toHaveBeenCalledTimes(1);
		const detail = (errorListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.status).toBe("unavailable");
	});

	test("supports show attribute updates", () => {
		const element = createElement("drafter-tone", { pitch: "C4" });
		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);
	});
});

// ---------------------------------------------------------------------------
// drafter-melody
// ---------------------------------------------------------------------------

describe("drafter-melody", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
	});

	afterEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		removeFakeAudioContext();
		jest.useRealTimers();
	});

	test("plays each note and finishes", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([
				["C4", 1],
				["rest", 1],
				["E4", 2],
			]),
			tempo: "120",
		});
		const noteListener = jest.fn();
		const finishListener = jest.fn();
		element.addEventListener("note", noteListener);
		element.addEventListener("finish", finishListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		// Two sounding notes -> two oscillators; the rest is silent.
		const context = FakeAudioContext.instances[0];
		expect(context.oscillators).toHaveLength(2);

		// 4 beats at 120bpm = 2 seconds total.
		jest.advanceTimersByTime(2100);
		expect(noteListener).toHaveBeenCalledTimes(3);
		const details = noteListener.mock.calls.map(
			(call) => (call[0] as CustomEvent).detail as Record<string, unknown>,
		);
		expect(details[0]).toMatchObject({ note: "C4", index: 0, count: 3 });
		expect(details[1]).toMatchObject({ note: "rest", frequency: 0, index: 1 });
		expect(details[2]).toMatchObject({ note: "E4", index: 2 });
		expect(finishListener).toHaveBeenCalledTimes(1);
		expect(
			(finishListener.mock.calls[0][0] as CustomEvent).detail,
		).toMatchObject({ count: 3 });
	});

	test("controls render pause and restart buttons", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
			controls: "true",
		});
		const buttons = element.querySelectorAll("button");
		expect(buttons).toHaveLength(2);

		buttons[0].click();
		await flushMicrotasks();
		expect(buttons[0].textContent).toBe("⏸");
	});
});

// ---------------------------------------------------------------------------
// drafter-microphone
// ---------------------------------------------------------------------------

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

describe("drafter-microphone", () => {
	let getUserMedia: jest.Mock;

	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
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
		jest.useRealTimers();
	});

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

	test("renders the prompt state into a decodable hidden field", () => {
		const element = createElement("drafter-microphone", { name: "mic" });
		const input = getHiddenInput(element);
		expect(input.name).toBe("mic");
		expect(input.getAttribute("data-transform")).toBe("json-decode");
		expect(getStoredData(element).status).toBe("prompt");
		expect(element.querySelector("button")?.textContent).toBe(
			"🎤 Enable microphone",
		);
	});

	test("granted flow measures volume and fires loud then quiet", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createElement("drafter-microphone", {
			name: "mic",
			threshold: "0.5",
			cooldown: "0",
		});
		const loudListener = jest.fn();
		const quietListener = jest.fn();
		element.addEventListener("loud", loudListener);
		element.addEventListener("quiet", quietListener);

		element.querySelector("button")?.click();
		await flushMicrotasks(6);

		expect(getStoredData(element).status).toBe("granted");
		const context = FakeAudioContext.instances[0];
		expect(context.analysers).toHaveLength(1);
		const analyser = context.analysers[0];

		// Loud signal: strongly offset samples produce a high RMS.
		analyser.timeDomainValue = 255;
		jest.advanceTimersByTime(60);
		expect(loudListener).toHaveBeenCalledTimes(1);
		const loudDetail = (loudListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(loudDetail.threshold).toBe(0.5);
		expect(loudDetail.volume as number).toBeGreaterThan(0.5);
		const stored = getStoredData(element);
		expect(stored.volume as number).toBeGreaterThan(0.5);
		expect(stored.peak_volume as number).toBeGreaterThan(0.5);

		// Silence again: quiet fires once.
		analyser.timeDomainValue = 128;
		jest.advanceTimersByTime(60);
		expect(quietListener).toHaveBeenCalledTimes(1);
	});

	test("denied permission stores denied and emits events", async () => {
		const error = new Error("Permission denied");
		error.name = "NotAllowedError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createElement("drafter-microphone", { name: "mic" });
		const deniedListener = jest.fn();
		const errorListener = jest.fn();
		element.addEventListener("denied", deniedListener);
		element.addEventListener("error", errorListener);

		element.querySelector("button")?.click();
		await flushMicrotasks(6);

		expect(getStoredData(element).status).toBe("denied");
		expect(deniedListener).toHaveBeenCalledTimes(1);
		expect(errorListener).toHaveBeenCalledTimes(1);
	});

	test("reports unavailable when there is no microphone support", () => {
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		const element = createElement("drafter-microphone", { name: "mic" });
		expect(getStoredData(element).status).toBe("unavailable");
	});
});

// ---------------------------------------------------------------------------
// drafter-audio-recorder
// ---------------------------------------------------------------------------

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

describe("drafter-audio-recorder", () => {
	let getUserMedia: jest.Mock;

	beforeEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
		FakeMediaRecorder.instances = [];
		getUserMedia = jest.fn();
		Object.defineProperty(window.navigator, "mediaDevices", {
			configurable: true,
			value: { getUserMedia },
		});
		Object.defineProperty(window, "MediaRecorder", {
			configurable: true,
			writable: true,
			value: FakeMediaRecorder,
		});
		(globalThis as { MediaRecorder?: unknown }).MediaRecorder =
			FakeMediaRecorder;
	});

	afterEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		removeFakeAudioContext();
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		delete (window as { MediaRecorder?: unknown }).MediaRecorder;
		delete (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
	});

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
		attempts = 50,
	): Promise<void> {
		for (let i = 0; i < attempts; i += 1) {
			if (predicate()) {
				return;
			}
			await new Promise((resolve) => setTimeout(resolve, 10));
		}
		throw new Error("Condition was not met in time");
	}

	test("records and stores a data URL recording", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createElement("drafter-audio-recorder", {
			name: "voice",
		});
		const recordListener = jest.fn();
		element.addEventListener("record", recordListener);

		expect(getStoredData(element).status).toBe("prompt");

		element.querySelector("button")?.click();
		await waitFor(() => getStoredData(element).status === "recording");
		expect(FakeMediaRecorder.instances).toHaveLength(1);

		const stopButton = Array.from(element.querySelectorAll("button")).find(
			(button) => button.textContent?.includes("Stop"),
		);
		stopButton?.click();
		await waitFor(() => getStoredData(element).status === "granted");

		const stored = getStoredData(element);
		expect(String(stored.data_url)).toMatch(/^data:/);
		expect(stored.size).toBeGreaterThan(0);
		expect(recordListener).toHaveBeenCalledTimes(1);
		// The recorder releases the microphone once the take is finished.
		expect(tracks[0].stop).toHaveBeenCalled();
		// A playback preview is offered.
		expect(element.querySelector("audio")).not.toBeNull();
	});

	test("reports unavailable without MediaRecorder support", () => {
		delete (window as { MediaRecorder?: unknown }).MediaRecorder;
		delete (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
		const element = createElement("drafter-audio-recorder", {
			name: "voice",
		});
		expect(getStoredData(element).status).toBe("unavailable");
	});
});
