import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/camera";

// ---------------------------------------------------------------------------
// getUserMedia / canvas fakes — jsdom has neither camera streams nor canvas
// rendering, so both are stubbed at the boundary the component touches.
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
		getVideoTracks: () => tracks,
		getTracks: () => tracks,
	} as unknown as MediaStream;
	return { stream, tracks };
}

const FAKE_DATA_URL = "data:image/png;base64,AAAA";

function installFakeCanvas(): void {
	Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
		configurable: true,
		writable: true,
		value: jest.fn(() => ({ drawImage: jest.fn() })),
	});
	Object.defineProperty(HTMLCanvasElement.prototype, "toDataURL", {
		configurable: true,
		writable: true,
		value: jest.fn(() => FAKE_DATA_URL),
	});
}

function flushMicrotasks(times = 8): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
}

describe("drafter-camera", () => {
	let getUserMedia: jest.Mock;

	beforeEach(() => {
		document.body.innerHTML = "";
		installFakeCanvas();
		getUserMedia = jest.fn();
		Object.defineProperty(window.navigator, "mediaDevices", {
			configurable: true,
			value: { getUserMedia },
		});
	});

	afterEach(() => {
		document.body.innerHTML = "";
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
	});

	function createCamera(
		attributes: Record<string, string> = { name: "photo" },
	): HTMLElement {
		const element = document.createElement("drafter-camera");
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

	function findButton(
		element: HTMLElement,
		label: string,
	): HTMLButtonElement | undefined {
		return Array.from(element.querySelectorAll("button")).find((button) =>
			button.textContent?.includes(label),
		);
	}

	test("renders a prompt with a hidden json-decode field", () => {
		const element = createCamera({ name: "photo" });
		const input = getHiddenInput(element);
		expect(input.name).toBe("photo");
		expect(input.getAttribute("data-transform")).toBe("json-decode");
		expect(getStoredData(element).status).toBe("prompt");
		expect(findButton(element, "Enable camera")).toBeDefined();
	});

	test("enabling the camera shows the live preview", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		expect(getStoredData(element).status).toBe("live");
		const video = element.querySelector("video");
		expect(video).not.toBeNull();
		expect(video?.srcObject).toBe(stream);
		expect(findButton(element, "Take photo")).toBeDefined();
		expect(findButton(element, "Stop")).toBeDefined();
	});

	test("requested constraints include size and facing mode", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({
			name: "photo",
			width: "1280",
			height: "720",
			facing: "environment",
		});

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		expect(getUserMedia).toHaveBeenCalledWith({
			video: {
				width: { ideal: 1280 },
				height: { ideal: 720 },
				facingMode: "environment",
			},
			audio: false,
		});
	});

	test("taking a photo stores it, stops the stream, and emits capture", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({ name: "photo" });
		const captureListener = jest.fn();
		element.addEventListener("capture", captureListener);

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();
		findButton(element, "Take photo")?.click();

		const stored = getStoredData(element);
		expect(stored.status).toBe("granted");
		expect(stored.data_url).toBe(FAKE_DATA_URL);
		expect(typeof stored.width).toBe("number");
		expect(typeof stored.height).toBe("number");
		expect(tracks[0].stop).toHaveBeenCalled();
		expect(captureListener).toHaveBeenCalledTimes(1);
		const detail = (captureListener.mock.calls[0][0] as CustomEvent)
			.detail as Record<string, unknown>;
		expect(typeof detail.width).toBe("number");
		expect(typeof detail.height).toBe("number");
		// The captured photo is displayed with a retake button.
		expect(element.querySelector("img")?.src).toBe(FAKE_DATA_URL);
		expect(findButton(element, "Retake")).toBeDefined();
	});

	test("retake starts a fresh stream", async () => {
		getUserMedia.mockImplementation(() =>
			Promise.resolve(makeFakeStream().stream),
		);
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();
		findButton(element, "Take photo")?.click();
		expect(getUserMedia).toHaveBeenCalledTimes(1);

		findButton(element, "Retake")?.click();
		await flushMicrotasks();
		expect(getUserMedia).toHaveBeenCalledTimes(2);
		expect(getStoredData(element).status).toBe("live");
	});

	test("stop turns off the camera and returns to the prompt", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();
		findButton(element, "Stop")?.click();

		expect(tracks[0].stop).toHaveBeenCalled();
		expect(getStoredData(element).status).toBe("prompt");
		expect(findButton(element, "Enable camera")).toBeDefined();
	});

	test("denied permission stores denied and emits denied and error events", async () => {
		const error = new Error("Permission denied");
		error.name = "NotAllowedError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createCamera({ name: "photo" });
		const deniedListener = jest.fn();
		const errorListener = jest.fn();
		element.addEventListener("denied", deniedListener);
		element.addEventListener("error", errorListener);

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("denied");
		expect(stored.message).toBe("Camera access denied");
		expect(deniedListener).toHaveBeenCalledTimes(1);
		expect(errorListener).toHaveBeenCalledTimes(1);
		expect(
			element.querySelector(".drafter-microphone-error-message"),
		).not.toBeNull();
	});

	test("a missing camera reports a not-found error", async () => {
		const error = new Error("Requested device not found");
		error.name = "NotFoundError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("No camera was found");
	});

	test("a busy camera reports an in-use error", async () => {
		const error = new Error("Could not start video source");
		error.name = "NotReadableError";
		getUserMedia.mockReturnValue(Promise.reject(error));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		const stored = getStoredData(element);
		expect(stored.status).toBe("error");
		expect(stored.message).toBe("The camera is already in use");
	});

	test("a missing mediaDevices API reports unavailable on connect", () => {
		delete (window.navigator as { mediaDevices?: unknown }).mediaDevices;
		const element = createCamera({ name: "photo" });
		expect(getStoredData(element).status).toBe("unavailable");
	});

	test("mirror is applied to the preview and can be turned off", async () => {
		const { stream } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();

		const video = element.querySelector("video") as HTMLVideoElement;
		expect(video.style.transform).toBe("scaleX(-1)");
		element.setAttribute("mirror", "false");
		expect(video.style.transform).toBe("");
	});

	test("disconnecting mid-stream stops the camera tracks", async () => {
		const { stream, tracks } = makeFakeStream();
		getUserMedia.mockReturnValue(Promise.resolve(stream));
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		await flushMicrotasks();
		expect(getStoredData(element).status).toBe("live");

		element.remove();
		expect(tracks[0].stop).toHaveBeenCalled();
	});

	test("disconnecting before permission resolves stops the late stream", async () => {
		const { stream, tracks } = makeFakeStream();
		let resolveStream: (stream: MediaStream) => void = () => {};
		getUserMedia.mockReturnValue(
			new Promise<MediaStream>((resolve) => {
				resolveStream = resolve;
			}),
		);
		const element = createCamera({ name: "photo" });

		findButton(element, "Enable camera")?.click();
		element.remove();
		resolveStream(stream);
		await flushMicrotasks();

		expect(tracks[0].stop).toHaveBeenCalled();
	});

	test("name updates rename the hidden field; show toggles visibility", () => {
		const element = createCamera({ name: "photo" });
		element.setAttribute("name", "selfie");
		expect(getHiddenInput(element).name).toBe("selfie");

		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);
		element.setAttribute("show", "true");
		expect(element.hidden).toBe(false);
	});
});
