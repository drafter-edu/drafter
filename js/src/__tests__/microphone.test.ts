import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/microphone";
import { resetAudioBrokerForTests } from "../components/audioBroker";

// ---------------------------------------------------------------------------
// Web Audio fakes (jsdom has no AudioContext) — mirrors audio.test.ts.
// ---------------------------------------------------------------------------

class FakeAudioNode {
	connect = jest.fn();

	disconnect = jest.fn();
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

function flushMicrotasks(times = 8): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
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

describe("drafter-microphone (extended)", () => {
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
		delete (window.navigator as { permissions?: unknown }).permissions;
		jest.useRealTimers();
	});

	function createMicrophone(
		attributes: Record<string, string> = { name: "mic" },
	): HTMLElement {
		const element = document.createElement("drafter-microphone");
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

	async function grantMicrophone(
		attributes: Record<string, string>,
	): Promise<{ element: HTMLElement; tracks: TrackState[] }> {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createMicrophone(attributes);
		element.querySelector("button")?.click();
		await flushMicrotasks();
		expect(getStoredData(element).status).toBe("granted");
		return { element, tracks };
	}

	test("reports pitch alongside volume when the signal is loud enough", async () => {
		const { element } = await grantMicrophone({ name: "mic" });
		const context = FakeAudioContext.instances[0];
		const analyser = context.analysers[0];
		// The component widens the FFT for transient detection.
		expect(analyser.fftSize).toBe(4096);

		analyser.timeDomainValue = 255;
		analyser.frequencyPeakIndex = 100;
		jest.advanceTimersByTime(60);

		const stored = getStoredData(element);
		// Peak amplitude (255-128)/128 rounded to 3 decimal places.
		expect(stored.volume).toBe(0.992);
		// frequency = index * sampleRate / fftSize = 100 * 48000 / 4096.
		expect(stored.pitch).toBe(1171.9);
	});

	test("omits pitch below the volume floor", async () => {
		const { element } = await grantMicrophone({ name: "mic" });
		const analyser = FakeAudioContext.instances[0].analysers[0];
		analyser.timeDomainValue = 128;
		analyser.frequencyPeakIndex = 100;
		jest.advanceTimersByTime(60);

		const stored = getStoredData(element);
		expect(stored.volume).toBe(0);
		expect("pitch" in stored).toBe(false);
	});

	test("rate throttles level events and includes pitch when present", async () => {
		const { element } = await grantMicrophone({
			name: "mic",
			threshold: "1",
			rate: "100",
		});
		const levelListener = jest.fn();
		element.addEventListener("level", levelListener);
		const analyser = FakeAudioContext.instances[0].analysers[0];
		analyser.timeDomainValue = 255;
		analyser.frequencyPeakIndex = 100;

		// Analysis runs every 50ms; levels only every 100ms. The first tick
		// always reports (lastLevelAt starts at 0).
		jest.advanceTimersByTime(60);
		expect(levelListener).toHaveBeenCalledTimes(1);
		const detail = (levelListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(detail.volume).toBe(0.992);
		expect(detail.pitch).toBe(1171.9);

		jest.advanceTimersByTime(40);
		expect(levelListener).toHaveBeenCalledTimes(1);
		jest.advanceTimersByTime(60);
		expect(levelListener).toHaveBeenCalledTimes(2);
	});

	test("cooldown suppresses a second loud event", async () => {
		const { element } = await grantMicrophone({
			name: "mic",
			threshold: "0.5",
			cooldown: "60000",
		});
		const loudListener = jest.fn();
		const quietListener = jest.fn();
		element.addEventListener("loud", loudListener);
		element.addEventListener("quiet", quietListener);
		const analyser = FakeAudioContext.instances[0].analysers[0];

		analyser.timeDomainValue = 255;
		jest.advanceTimersByTime(60);
		expect(loudListener).toHaveBeenCalledTimes(1);

		analyser.timeDomainValue = 128;
		jest.advanceTimersByTime(60);
		expect(quietListener).toHaveBeenCalledTimes(1);

		// Loud again inside the cooldown window: no second event.
		analyser.timeDomainValue = 255;
		jest.advanceTimersByTime(200);
		expect(loudListener).toHaveBeenCalledTimes(1);
	});

	test("the meter visualization tracks volume and marks loud levels", async () => {
		const { element } = await grantMicrophone({
			name: "mic",
			threshold: "0.5",
		});
		const meterFill = element.querySelector(
			".drafter-microphone-meter-fill",
		) as HTMLDivElement;
		expect(meterFill).not.toBeNull();

		const analyser = FakeAudioContext.instances[0].analysers[0];
		analyser.timeDomainValue = 255;
		jest.advanceTimersByTime(60);

		expect(meterFill.style.width).toBe("99%");
		expect(
			meterFill.classList.contains("drafter-microphone-meter-loud"),
		).toBe(true);
	});

	test("waveform and bars visualizations render a canvas instead of a meter", async () => {
		const { element } = await grantMicrophone({
			name: "mic",
			visualize: "waveform",
		});
		expect(element.querySelector("canvas")).not.toBeNull();
		expect(element.querySelector(".drafter-microphone-meter")).toBeNull();

		// Switching the visualize attribute while granted re-renders.
		element.setAttribute("visualize", "meter");
		expect(element.querySelector("canvas")).toBeNull();
		expect(
			element.querySelector(".drafter-microphone-meter"),
		).not.toBeNull();

		element.setAttribute("visualize", "bars");
		expect(element.querySelector("canvas")).not.toBeNull();
	});

	test("a remembered grant starts capture without a click", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		Object.defineProperty(window.navigator, "permissions", {
			configurable: true,
			value: {
				query: jest.fn(() => Promise.resolve({ state: "granted" })),
			},
		});

		const element = createMicrophone({ name: "mic" });
		await flushMicrotasks();

		expect(getUserMedia).toHaveBeenCalledTimes(1);
		expect(getStoredData(element).status).toBe("granted");
	});

	test("a remembered denial renders denied without emitting events", async () => {
		Object.defineProperty(window.navigator, "permissions", {
			configurable: true,
			value: {
				query: jest.fn(() => Promise.resolve({ state: "denied" })),
			},
		});

		const element = document.createElement("drafter-microphone");
		element.setAttribute("name", "mic");
		const deniedListener = jest.fn();
		const errorListener = jest.fn();
		element.addEventListener("denied", deniedListener);
		element.addEventListener("error", errorListener);
		document.body.appendChild(element);
		await flushMicrotasks();

		expect(getStoredData(element).status).toBe("denied");
		expect(getUserMedia).not.toHaveBeenCalled();
		// The passive permission check renders the state but does not fire
		// denied/error events (those are reserved for an actual attempt).
		expect(deniedListener).not.toHaveBeenCalled();
		expect(errorListener).not.toHaveBeenCalled();
	});

	test("a missing microphone reports a not-found error", async () => {
		const error = new Error("Requested device not found");
		error.name = "NotFoundError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createMicrophone({ name: "mic" });
		const errorListener = jest.fn();
		element.addEventListener("error", errorListener);

		element.querySelector("button")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("No microphone was found");
		expect(errorListener).toHaveBeenCalledTimes(1);
	});

	test("the denied help button opens the how-to alert", async () => {
		const alertSpy = jest
			.spyOn(window, "alert")
			.mockImplementation(() => {});
		const error = new Error("Permission denied");
		error.name = "NotAllowedError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createMicrophone({ name: "mic" });

		element.querySelector("button")?.click();
		await flushMicrotasks();

		const helpButton = element.querySelector(
			".drafter-microphone-help-link",
		) as HTMLButtonElement;
		expect(helpButton).not.toBeNull();
		helpButton.click();
		expect(alertSpy).toHaveBeenCalledTimes(1);
		expect(String(alertSpy.mock.calls[0][0])).toContain(
			"Microphone permissions",
		);
		alertSpy.mockRestore();
	});

	test("reports unavailable when audio itself is unsupported", () => {
		// mediaDevices exists, but there is no AudioContext to analyze with.
		removeFakeAudioContext();
		const element = createMicrophone({ name: "mic" });
		expect(getStoredData(element).status).toBe("unavailable");
	});

	test("disconnecting stops analysis and releases the microphone", async () => {
		const { element, tracks } = await grantMicrophone({ name: "mic" });
		expect(tracks[0].stop).not.toHaveBeenCalled();

		element.remove();
		expect(tracks[0].stop).toHaveBeenCalledTimes(1);
		// No stray analysis interval keeps running after removal.
		expect(() => jest.advanceTimersByTime(500)).not.toThrow();
	});

	test("name updates rename the hidden field; show toggles visibility", () => {
		const element = createMicrophone({ name: "mic" });
		element.setAttribute("name", "listener");
		expect(getHiddenInput(element).name).toBe("listener");

		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);
		element.setAttribute("show", "true");
		expect(element.hidden).toBe(false);
	});
});
