import {
	afterAll,
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/sound";
import {
	audioBroker,
	resetAudioBrokerForTests,
} from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio fakes (jsdom has no AudioContext) — mirrors audio.test.ts, with
// the media-element-specific nodes drafter-sound needs.
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

class FakeGainNode extends FakeAudioNode {
	gain = new FakeAudioParam();
}

class FakeStereoPannerNode extends FakeAudioNode {
	pan = new FakeAudioParam();
}

class FakeAnalyserNode extends FakeAudioNode {
	fftSize = 2048;

	get frequencyBinCount() {
		return this.fftSize / 2;
	}

	getByteTimeDomainData = (data: Uint8Array) => {
		data.fill(128);
	};

	getByteFrequencyData = (data: Uint8Array) => {
		data.fill(0);
	};
}

class FakeAudioContext {
	static instances: FakeAudioContext[] = [];

	state = "running";

	currentTime = 0;

	sampleRate = 48000;

	destination = new FakeAudioNode();

	gains: FakeGainNode[] = [];

	panners: FakeStereoPannerNode[] = [];

	analysers: FakeAnalyserNode[] = [];

	mediaElementSources: FakeAudioNode[] = [];

	constructor() {
		FakeAudioContext.instances.push(this);
	}

	addEventListener = jest.fn();

	resume = jest.fn(() => {
		this.state = "running";
		return Promise.resolve();
	});

	close = jest.fn(() => Promise.resolve());

	createGain = () => {
		const node = new FakeGainNode();
		this.gains.push(node);
		return node;
	};

	createStereoPanner = () => {
		const node = new FakeStereoPannerNode();
		this.panners.push(node);
		return node;
	};

	createAnalyser = () => {
		const node = new FakeAnalyserNode();
		this.analysers.push(node);
		return node;
	};

	createMediaElementSource = jest.fn(() => {
		const node = new FakeAudioNode();
		this.mediaElementSources.push(node);
		return node;
	});
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

// jsdom's HTMLMediaElement.play/pause are unimplemented stubs that log
// errors; replace them for the whole file and restore afterwards.
const originalPlay = HTMLMediaElement.prototype.play;
const originalPause = HTMLMediaElement.prototype.pause;
const playMock = jest.fn<() => Promise<void>>(() => Promise.resolve());
const pauseMock = jest.fn<() => void>();

describe("drafter-sound", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		installFakeAudioContext();
		playMock.mockClear();
		playMock.mockImplementation(() => Promise.resolve());
		pauseMock.mockClear();
		HTMLMediaElement.prototype.play =
			playMock as unknown as typeof HTMLMediaElement.prototype.play;
		HTMLMediaElement.prototype.pause =
			pauseMock as unknown as typeof HTMLMediaElement.prototype.pause;
	});

	afterEach(() => {
		document.body.innerHTML = "";
		resetAudioBrokerForTests();
		removeFakeAudioContext();
	});

	afterAll(() => {
		HTMLMediaElement.prototype.play = originalPlay;
		HTMLMediaElement.prototype.pause = originalPause;
	});

	function getAudio(element: HTMLElement): HTMLAudioElement {
		const audio = element.querySelector("audio");
		if (!(audio instanceof HTMLAudioElement)) {
			throw new Error("Audio element was not rendered");
		}
		return audio;
	}

	function getEnableButton(element: HTMLElement): HTMLButtonElement {
		const button = element.querySelector("button");
		if (!(button instanceof HTMLButtonElement)) {
			throw new Error("Enable-sound button was not rendered");
		}
		return button;
	}

	test("renders an audio element with src, controls, and a hidden enable prompt", () => {
		const element = createElement("drafter-sound", {
			src: "song.mp3",
			controls: "true",
		});
		const audio = getAudio(element);
		expect(audio.src).toContain("song.mp3");
		expect(audio.controls).toBe(true);
		const button = getEnableButton(element);
		expect(button.hidden).toBe(true);
		expect(button.textContent).toBe("🔊 Enable sound");
	});

	test("visualize attribute adds a canvas", () => {
		const plain = createElement("drafter-sound", { src: "a.mp3" });
		expect(plain.querySelector("canvas")).toBeNull();
		const visualized = createElement("drafter-sound", {
			src: "a.mp3",
			visualize: "waveform",
		});
		expect(visualized.querySelector("canvas")).not.toBeNull();
	});

	test("applies volume, speed, and loop natively before any graph exists", () => {
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			volume: "0.5",
			speed: "2",
			loop: "true",
		});
		const audio = getAudio(element);
		expect(audio.volume).toBe(0.5);
		expect(audio.playbackRate).toBe(2);
		expect(audio.defaultPlaybackRate).toBe(2);
		expect(audio.loop).toBe(true);
	});

	test("native play builds the graph, routes volume/pan, and dispatches play", () => {
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			volume: "0.25",
			pan: "-0.5",
		});
		const playListener = jest.fn();
		element.addEventListener("play", playListener);
		const audio = getAudio(element);

		audio.dispatchEvent(new Event("play"));

		expect(playListener).toHaveBeenCalledTimes(1);
		expect(
			(playListener.mock.calls[0][0] as CustomEvent).detail,
		).toMatchObject({ src: "a.mp3" });

		const context = FakeAudioContext.instances[0];
		expect(context.createMediaElementSource).toHaveBeenCalledTimes(1);
		// Once the graph exists the element's own volume is pinned to unity
		// and loudness moves to the gain node; pan goes to the panner.
		expect(audio.volume).toBe(1);
		expect(context.gains.at(-1)!.gain.value).toBe(0.25);
		expect(context.panners[0].pan.value).toBe(-0.5);
	});

	test("volume changes update the gain node once the graph exists", () => {
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			volume: "1",
		});
		const audio = getAudio(element);
		audio.dispatchEvent(new Event("play"));
		const context = FakeAudioContext.instances[0];
		const gain = context.gains.at(-1)!;

		element.setAttribute("volume", "0.3");

		expect(gain.gain.value).toBe(0.3);
		expect(audio.volume).toBe(1);
	});

	test("src and controls attribute changes update the audio element in place", () => {
		const element = createElement("drafter-sound", { src: "a.mp3" });
		const audio = getAudio(element);
		expect(audio.controls).toBe(false);

		element.setAttribute("src", "b.mp3");
		expect(audio.src).toContain("b.mp3");

		element.setAttribute("controls", "true");
		expect(audio.controls).toBe(true);

		element.setAttribute("controls", "false");
		expect(audio.controls).toBe(false);
		// The same audio element persists across these updates.
		expect(getAudio(element)).toBe(audio);
	});

	test("effects changes rebuild the chain without a second media source", () => {
		const element = createElement("drafter-sound", { src: "a.mp3" });
		const audio = getAudio(element);
		audio.dispatchEvent(new Event("play"));
		const context = FakeAudioContext.instances[0];
		const source = context.mediaElementSources[0];
		const gainsBefore = context.gains.length;

		element.setAttribute("effects", "[]");

		// A MediaElementSourceNode can only be created once per element, so
		// only the downstream chain is rebuilt.
		expect(context.createMediaElementSource).toHaveBeenCalledTimes(1);
		expect(context.gains.length).toBeGreaterThan(gainsBefore);
		expect(source.disconnect).toHaveBeenCalled();
	});

	test("ended dispatches finish without a duration when it is unknown", () => {
		const element = createElement("drafter-sound", { src: "a.mp3" });
		const finishListener = jest.fn();
		element.addEventListener("finish", finishListener);

		getAudio(element).dispatchEvent(new Event("ended"));

		expect(finishListener).toHaveBeenCalledTimes(1);
		const detail = (finishListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.src).toBe("a.mp3");
		// jsdom reports NaN for duration, so the payload omits it.
		expect("duration" in detail).toBe(false);
	});

	test("audio errors dispatch an error event naming the source", () => {
		const element = createElement("drafter-sound", { src: "a.mp3" });
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		getAudio(element).dispatchEvent(new Event("error"));

		expect(errorListener).toHaveBeenCalledTimes(1);
		const detail = (errorListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.status).toBe("error");
		expect(String(detail.message)).toContain("a.mp3");
	});

	test("auto-play with a locked context reveals the enable prompt, which starts playback", async () => {
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			"auto-play": "true",
		});
		const button = getEnableButton(element);
		expect(button.hidden).toBe(true);
		expect(playMock).not.toHaveBeenCalled();

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		expect(button.hidden).toBe(false);
		expect(playMock).not.toHaveBeenCalled();

		button.click();
		await flushMicrotasks();

		expect(button.hidden).toBe(true);
		// NOTE: both the broker's onUnlocked subscription (from
		// autoPlayWhenUnlocked) and the enable button's own click handler
		// call startPlayback, so play() can legitimately run twice here.
		// Harmless (playing an already-playing element), but a quirk of the
		// production code worth knowing about.
		expect(playMock.mock.calls.length).toBeGreaterThanOrEqual(1);
	});

	test("auto-play starts on page load when the context is already unlocked", async () => {
		await audioBroker.requestUnlock();
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			"auto-play": "true",
		});
		const button = getEnableButton(element);

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		await flushMicrotasks();

		expect(playMock).toHaveBeenCalledTimes(1);
		expect(button.hidden).toBe(true);
	});

	test("a blocked play() reveals the enable-sound prompt", async () => {
		playMock.mockImplementation(() =>
			Promise.reject(new Error("blocked")),
		);
		await audioBroker.requestUnlock();
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			"auto-play": "true",
		});

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		await flushMicrotasks();

		expect(getEnableButton(element).hidden).toBe(false);
	});

	test("playing with a visualizer routes through an analyser node", () => {
		const element = createElement("drafter-sound", {
			src: "a.mp3",
			visualize: "bars",
		});
		getAudio(element).dispatchEvent(new Event("play"));

		const context = FakeAudioContext.instances[0];
		expect(context.analysers).toHaveLength(1);
		expect(context.analysers[0].fftSize).toBe(2048);
	});

	test("removal pauses playback and disconnects the graph", () => {
		const element = createElement("drafter-sound", { src: "a.mp3" });
		const audio = getAudio(element);
		audio.dispatchEvent(new Event("play"));
		const context = FakeAudioContext.instances[0];
		const source = context.mediaElementSources[0];

		element.remove();

		expect(pauseMock).toHaveBeenCalled();
		expect(source.disconnect).toHaveBeenCalled();
	});
});
