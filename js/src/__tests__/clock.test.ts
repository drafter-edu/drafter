import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/timer";

describe("drafter-clock", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
	});

	afterEach(() => {
		jest.runOnlyPendingTimers();
		jest.useRealTimers();
		document.body.innerHTML = "";
	});

	function createClock(attributes: Record<string, string> = {}): HTMLElement {
		const clock = document.createElement("drafter-clock");
		for (const [name, value] of Object.entries(attributes)) {
			clock.setAttribute(name, value);
		}
		document.body.appendChild(clock);
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		return clock;
	}

	function getLabel(clock: HTMLElement): HTMLSpanElement {
		const label = clock.querySelector("span");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Clock label was not rendered");
		}
		return label;
	}

	test("supports show attribute updates without stopping the clock", () => {
		const clock = createClock({ interval: "1000" });

		expect(clock.hidden).toBe(false);
		expect(getLabel(clock).textContent).toBe("0:00");

		clock.setAttribute("show", "false");
		expect(clock.hidden).toBe(true);

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");

		clock.removeAttribute("show");
		expect(clock.hidden).toBe(false);
	});

	test("does not start ticking before the page-loaded event", () => {
		const clock = document.createElement("drafter-clock");
		clock.setAttribute("interval", "1000");
		document.body.appendChild(clock);

		expect(getLabel(clock).textContent).toBe("0:00");
		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:00");

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");
	});

	test("pauses, resumes, and restarts from the controls", () => {
		const clock = createClock({
			interval: "1000",
			controls: "",
		});
		const tickListener = jest.fn();
		clock.addEventListener("tick", tickListener);

		const [toggleButton, restartButton] = Array.from(
			clock.querySelectorAll("button"),
		) as HTMLButtonElement[];

		expect(getLabel(clock).textContent).toBe("0:00");
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");

		toggleButton.click();
		expect(toggleButton.textContent).toBe("▶");

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");

		toggleButton.click();
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:04");

		restartButton.click();
		expect(getLabel(clock).textContent).toBe("0:00");
		expect(toggleButton.textContent).toBe("⏸");
		expect(tickListener).toHaveBeenCalled();
	});

	test("restarts when interval attribute changes", () => {
		const clock = createClock({ interval: "1000" });

		jest.advanceTimersByTime(3000);
		expect(getLabel(clock).textContent).toBe("0:03");

		clock.setAttribute("interval", "500");
		expect(getLabel(clock).textContent).toBe("0:00");

		jest.advanceTimersByTime(1500);
		expect(getLabel(clock).textContent).toBe("0:01");
	});
});
