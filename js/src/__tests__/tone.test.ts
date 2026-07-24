import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/tone";
import {
	audioBroker,
	resetAudioBrokerForTests,
} from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio fakes (jsdom has no AudioContext) — mirrors audio.test.ts, with
// gain-node tracking so envelope shaping can be asserted.
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

class FakeAudioContext {
	static instances: FakeAudioContext[] = [];

	state = "running";

	currentTime = 0;

	sampleRate = 48000;

	destination = new FakeAudioNode();

	oscillators: FakeOscillator[] = [];

	gains: FakeGainNode[] = [];

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

	createGain = () => {
		const node = new FakeGainNode();
		this.gains.push(node);
		return node;
	};
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

describe("drafter-tone (extended)", () => {
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

	function getButton(element: HTMLElement): HTMLButtonElement {
		const button = element.querySelector("button");
		if (!(button instanceof HTMLButtonElement)) {
			throw new Error("Play button was not rendered");
		}
		return button;
	}

	function getStatus(element: HTMLElement): HTMLSpanElement {
		const status = element.querySelector("span.drafter-audio-status");
		if (!(status instanceof HTMLSpanElement)) {
			throw new Error("Status area was not rendered");
		}
		return status;
	}

	test("an unparseable pitch emits an error naming the pitch", async () => {
		const element = createElement("drafter-tone", { pitch: "banana" });
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		getButton(element).click();
		await flushMicrotasks();

		expect(errorListener).toHaveBeenCalledTimes(1);
		const detail = (errorListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.status).toBe("error");
		expect(String(detail.message)).toContain("banana");
		expect(getStatus(element).textContent).toContain("banana");
		// Nothing was scheduled on the audio graph.
		expect(FakeAudioContext.instances[0].oscillators).toHaveLength(0);
	});

	test("a raw-frequency pitch plays without a note name", async () => {
		const element = createElement("drafter-tone", {
			pitch: "330",
			duration: "100",
		});
		// No note name means a bare play glyph.
		expect(getButton(element).textContent).toBe("▶");

		const startListener = jest.fn();
		element.addEventListener("start", startListener);
		getButton(element).click();
		await flushMicrotasks();

		expect(startListener).toHaveBeenCalledTimes(1);
		const detail = (startListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.frequency).toBe(330);
		expect("note" in detail).toBe(false);
	});

	test("volume, attack, and release shape the gain envelope", async () => {
		const element = createElement("drafter-tone", {
			pitch: "A4",
			duration: "1000",
			volume: "0.5",
			attack: "100",
			release: "200",
		});
		getButton(element).click();
		await flushMicrotasks();

		const context = FakeAudioContext.instances[0];
		// The envelope gain is created before the effects-chain passthrough.
		const envelope = context.gains[0];
		expect(envelope.gain.setValueAtTime).toHaveBeenCalledWith(0, 0);
		expect(envelope.gain.linearRampToValueAtTime).toHaveBeenCalledWith(
			0.5,
			expect.closeTo(0.1, 10),
		);
		expect(envelope.gain.setValueAtTime).toHaveBeenCalledWith(
			0.5,
			expect.closeTo(0.8, 10),
		);
		expect(envelope.gain.linearRampToValueAtTime).toHaveBeenCalledWith(
			0.0001,
			expect.closeTo(1, 10),
		);

		const oscillator = context.oscillators[0];
		expect(oscillator.started).toEqual([0]);
		expect(oscillator.stopped).toEqual([1]);
	});

	test("the button is disabled with a ♪ status while playing", async () => {
		const element = createElement("drafter-tone", {
			pitch: "C4",
			duration: "100",
		});
		getButton(element).click();
		await flushMicrotasks();

		expect(getButton(element).disabled).toBe(true);
		expect(getStatus(element).textContent).toBe("♪");

		FakeAudioContext.instances[0].oscillators[0].onended?.();
		expect(getButton(element).disabled).toBe(false);
		expect(getStatus(element).textContent).toBe("");
	});

	test("an unknown waveform falls back to sine", async () => {
		const element = createElement("drafter-tone", {
			pitch: "C4",
			waveform: "wobble",
		});
		getButton(element).click();
		await flushMicrotasks();

		expect(FakeAudioContext.instances[0].oscillators[0].type).toBe("sine");
	});

	test("auto-play with a locked context reveals the enable-sound prompt", async () => {
		const element = createElement("drafter-tone", {
			pitch: "C4",
			"auto-play": "true",
		});
		const startListener = jest.fn();
		element.addEventListener("start", startListener);
		const button = getButton(element);
		// auto-play hides the ordinary play button.
		expect(button.hidden).toBe(true);

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		expect(button.hidden).toBe(false);
		expect(button.textContent).toBe("🔊 Enable sound");
		expect(startListener).not.toHaveBeenCalled();

		button.click();
		await flushMicrotasks();

		expect(button.hidden).toBe(true);
		expect(startListener).toHaveBeenCalledTimes(1);
		expect(FakeAudioContext.instances[0].oscillators).toHaveLength(1);
	});

	test("auto-play starts on page load when the context is already unlocked", async () => {
		await audioBroker.requestUnlock();
		const element = createElement("drafter-tone", {
			pitch: "C4",
			"auto-play": "true",
		});
		const startListener = jest.fn();
		element.addEventListener("start", startListener);

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		await flushMicrotasks();

		expect(startListener).toHaveBeenCalledTimes(1);
		expect(getButton(element).hidden).toBe(true);
	});

	test("auto-play without audio support emits an unavailable error", async () => {
		removeFakeAudioContext();
		const element = createElement("drafter-tone", {
			pitch: "C4",
			"auto-play": "true",
		});
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		await flushMicrotasks();

		expect(errorListener).toHaveBeenCalledTimes(1);
		const detail = (errorListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.status).toBe("unavailable");
	});

	test("pitch changes update the idle button label", () => {
		const element = createElement("drafter-tone", { pitch: "C4" });
		expect(getButton(element).textContent).toBe("▶ C4");

		element.setAttribute("pitch", "D4");
		expect(getButton(element).textContent).toBe("▶ D4");

		// A raw frequency has no note name to show.
		element.setAttribute("pitch", "440");
		expect(getButton(element).textContent).toBe("▶");
	});
});
