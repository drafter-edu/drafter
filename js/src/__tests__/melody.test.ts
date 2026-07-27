import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/melody";
import {
	audioBroker,
	AUDIO_UNSUPPORTED_ERROR,
	resetAudioBrokerForTests,
} from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio fakes (jsdom has no AudioContext) — mirrors audio.test.ts, with
// gain-node tracking so the master volume can be asserted.
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

	start = jest.fn();

	stop = jest.fn();
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

describe("drafter-melody (extended)", () => {
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

	function getPrimaryButton(element: HTMLElement): HTMLButtonElement {
		const button = element.querySelector("button.drafter-audio-play-button");
		if (!(button instanceof HTMLButtonElement)) {
			throw new Error("Primary button was not rendered");
		}
		return button;
	}

	function getLabel(element: HTMLElement): HTMLSpanElement {
		const label = element.querySelector("span.drafter-audio-status");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Status label was not rendered");
		}
		return label;
	}

	test("an empty melody finishes immediately with a zero count", async () => {
		const element = createElement("drafter-melody", { notes: "[]" });
		const finishListener = jest.fn();
		element.addEventListener("finish", finishListener);

		getPrimaryButton(element).click();
		await flushMicrotasks();

		expect(finishListener).toHaveBeenCalledTimes(1);
		expect(
			(finishListener.mock.calls[0][0] as CustomEvent).detail,
		).toEqual({ count: 0 });
		expect(FakeAudioContext.instances[0].oscillators).toHaveLength(0);
	});

	test("volume and waveform reach the audio graph", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
			volume: "0.4",
			waveform: "triangle",
		});
		getPrimaryButton(element).click();
		await flushMicrotasks();

		const context = FakeAudioContext.instances[0];
		// The master gain is the first gain created by play().
		expect(context.gains[0].gain.value).toBe(0.4);
		expect(context.oscillators[0].type).toBe("triangle");
	});

	test("pause captures the elapsed offset and resume skips finished notes", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([
				["C4", 1],
				["E4", 1],
			]),
			tempo: "60",
			controls: "true",
		});
		const button = getPrimaryButton(element);
		button.click();
		await flushMicrotasks();

		const context = FakeAudioContext.instances[0];
		expect(context.oscillators).toHaveLength(2);
		expect(button.textContent).toBe("⏸");

		// 1.2s into a 2s melody: the first (1s) note has already ended.
		context.currentTime = 1.2;
		button.click();
		await flushMicrotasks();
		expect(button.textContent).toBe("▶");

		button.click();
		await flushMicrotasks();
		expect(button.textContent).toBe("⏸");
		// Only the still-pending E4 was rescheduled.
		expect(context.oscillators).toHaveLength(3);
		expect(context.oscillators[2].frequency.value).toBeCloseTo(329.628, 2);
	});

	test("the restart control replays the melody from the beginning", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([
				["C4", 1],
				["E4", 1],
			]),
			tempo: "60",
			controls: "true",
		});
		getPrimaryButton(element).click();
		await flushMicrotasks();

		const context = FakeAudioContext.instances[0];
		expect(context.oscillators).toHaveLength(2);

		const restartButton = Array.from(
			element.querySelectorAll("button"),
		).find((button) => button.getAttribute("aria-label") === "Restart melody");
		expect(restartButton).toBeDefined();

		restartButton!.click();
		await flushMicrotasks();
		// Both notes were scheduled again from zero.
		expect(context.oscillators).toHaveLength(4);
	});

	test("changing the notes mid-play resets to an idle rendering", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 4]]),
			tempo: "60",
		});
		getPrimaryButton(element).click();
		await flushMicrotasks();
		expect(getPrimaryButton(element).disabled).toBe(true);

		element.setAttribute("notes", JSON.stringify([["D4", 1]]));
		const button = getPrimaryButton(element);
		expect(button.textContent).toBe("▶");
		expect(button.disabled).toBe(false);
		expect(getLabel(element).textContent).toBe("");
	});

	test("reports unavailable when there is no audio support", async () => {
		removeFakeAudioContext();
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
		});
		const button = getPrimaryButton(element);

		button.click();
		await flushMicrotasks();

		expect(button.hidden).toBe(true);
		expect(getLabel(element).textContent).toBe(AUDIO_UNSUPPORTED_ERROR);
	});

	test("auto-play with a locked context shows the enable-sound prompt", async () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
			"auto-play": "true",
		});
		const button = getPrimaryButton(element);

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		expect(button.textContent).toBe("🔊 Enable sound");
		expect(FakeAudioContext.instances).toHaveLength(0);

		button.click();
		await flushMicrotasks();

		// Unlocking through the prompt starts playback; auto-play playback
		// hides the primary button.
		expect(FakeAudioContext.instances[0].oscillators).toHaveLength(1);
		expect(button.hidden).toBe(true);
	});

	test("auto-play starts on page load when the context is already unlocked", async () => {
		await audioBroker.requestUnlock();
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
			"auto-play": "true",
		});

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		await flushMicrotasks();

		expect(FakeAudioContext.instances[0].oscillators).toHaveLength(1);
	});

	test("supports show attribute updates", () => {
		const element = createElement("drafter-melody", {
			notes: JSON.stringify([["C4", 1]]),
		});
		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);
		element.setAttribute("show", "true");
		expect(element.hidden).toBe(false);
	});
});
