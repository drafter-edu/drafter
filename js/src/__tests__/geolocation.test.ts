import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/geolocation";

type SuccessCallback = (position: unknown) => void;
type ErrorCallback = (error: unknown) => void;

const ERROR_CODES = {
	PERMISSION_DENIED: 1,
	POSITION_UNAVAILABLE: 2,
	TIMEOUT: 3,
};

describe("drafter-current-location", () => {
	let getCurrentPosition: jest.Mock;

	beforeEach(() => {
		document.body.innerHTML = "";
		getCurrentPosition = jest.fn();
		Object.defineProperty(window.navigator, "geolocation", {
			configurable: true,
			value: { getCurrentPosition },
		});
	});

	afterEach(() => {
		document.body.innerHTML = "";
		delete (window.navigator as { geolocation?: unknown }).geolocation;
	});

	function createComponent(
		attributes: Record<string, string> = { name: "spot" },
	): HTMLElement {
		const element = document.createElement("drafter-current-location");
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

	function getStoredLocation(element: HTMLElement): Record<string, unknown> {
		return JSON.parse(getHiddenInput(element).value);
	}

	function resolvePosition(callIndex = 0): {
		success: SuccessCallback;
		fail: ErrorCallback;
	} {
		const call = getCurrentPosition.mock.calls[callIndex] as [
			SuccessCallback,
			ErrorCallback,
			unknown,
		];
		return { success: call[0], fail: call[1] };
	}

	test("renders the prompt state into a decodable hidden field", () => {
		const element = createComponent({ name: "spot" });
		const input = getHiddenInput(element);

		expect(input.name).toBe("spot");
		expect(input.getAttribute("data-transform")).toBe("json-decode");
		expect(getStoredLocation(element).status).toBe("prompt");
		expect(element.querySelector("button")?.textContent).toBe(
			"📍 Use my location",
		);
		expect(getCurrentPosition).not.toHaveBeenCalled();
	});

	test("supports show attribute updates", () => {
		const element = createComponent({ name: "spot" });

		expect(element.hidden).toBe(false);
		element.setAttribute("show", "false");
		expect(element.hidden).toBe(true);

		element.removeAttribute("show");
		expect(element.hidden).toBe(false);
	});

	test("stores the position and emits locate when permission is granted", () => {
		const element = createComponent({
			name: "spot",
			"show-coordinates": "true",
		});
		const locateListener = jest.fn();
		element.addEventListener("locate", locateListener);

		const button = element.querySelector("button") as HTMLButtonElement;
		button.click();
		expect(getStoredLocation(element).status).toBe("pending");
		expect(element.querySelector(".drafter-geolocation-spinner")).not.toBeNull();

		resolvePosition().success({
			coords: {
				latitude: 39.68,
				longitude: -75.75,
				accuracy: 12.4,
				altitude: null,
				heading: null,
				speed: null,
			},
			timestamp: 1234567890,
		});

		const stored = getStoredLocation(element);
		expect(stored).toEqual({
			status: "granted",
			message: "Location available",
			lat: 39.68,
			lon: -75.75,
			accuracy: 12.4,
			timestamp: 1234567890,
		});
		expect(
			element.querySelector(".drafter-geolocation-coords")?.textContent,
		).toBe("39.680000, -75.750000 (±12m)");

		expect(locateListener).toHaveBeenCalledTimes(1);
		const event = locateListener.mock.calls[0][0] as CustomEvent;
		expect(event.detail.status).toBe("granted");
		expect(event.detail.lat).toBe(39.68);
	});

	test("maps a permission error to the denied state", () => {
		const element = createComponent({ name: "spot" });
		const locateListener = jest.fn();
		element.addEventListener("locate", locateListener);

		(element.querySelector("button") as HTMLButtonElement).click();
		resolvePosition().fail({ code: 1, ...ERROR_CODES });

		expect(getStoredLocation(element)).toEqual({
			status: "denied",
			message: "Location access denied",
		});
		expect(
			element.querySelector(".drafter-geolocation-error-message")
				?.textContent,
		).toBe("Location access denied");
		expect(locateListener).toHaveBeenCalledTimes(1);
	});

	test("maps a timeout to the error state", () => {
		const element = createComponent({ name: "spot" });

		(element.querySelector("button") as HTMLButtonElement).click();
		resolvePosition().fail({ code: 3, ...ERROR_CODES });

		expect(getStoredLocation(element)).toEqual({
			status: "error",
			message: "Location request timed out",
		});
	});

	test("reports unavailable when the geolocation API is missing", () => {
		delete (window.navigator as { geolocation?: unknown }).geolocation;

		const element = createComponent({ name: "spot" });

		expect(getStoredLocation(element).status).toBe("unavailable");
		expect(element.querySelector("button")).toBeNull();
	});

	test("updates the hidden field name when the attribute changes", () => {
		const element = createComponent({ name: "spot" });

		element.setAttribute("name", "destination");
		expect(getHiddenInput(element).name).toBe("destination");
	});
});
