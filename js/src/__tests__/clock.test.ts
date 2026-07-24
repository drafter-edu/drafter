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

describe("drafter-clock (extended)", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
	});

	afterEach(() => {
		jest.runOnlyPendingTimers();
		jest.useRealTimers();
		document.body.innerHTML = "";
	});

	function buildClock(attributes: Record<string, string> = {}): HTMLElement {
		const clock = document.createElement("drafter-clock");
		for (const [name, value] of Object.entries(attributes)) {
			clock.setAttribute(name, value);
		}
		document.body.appendChild(clock);
		return clock;
	}

	function pageLoaded(): void {
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
	}

	function getLabel(clock: HTMLElement): HTMLSpanElement {
		const label = clock.querySelector("span");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Clock label was not rendered");
		}
		return label;
	}

	function collectDetails(
		element: HTMLElement,
		eventType: string,
	): Array<Record<string, unknown>> {
		const details: Array<Record<string, unknown>> = [];
		element.addEventListener(eventType, (event) => {
			details.push((event as CustomEvent).detail as Record<string, unknown>);
		});
		return details;
	}

	test("tick payloads carry elapsed and interval; interval change resets elapsed", () => {
		const clock = buildClock({ interval: "500" });
		const ticks = collectDetails(clock, "tick");

		pageLoaded();
		// beginRunning emits an immediate tick at zero elapsed.
		expect(ticks).toEqual([{ elapsed: 0, interval: 500 }]);

		jest.advanceTimersByTime(500);
		expect(ticks.at(-1)).toEqual({ elapsed: 500, interval: 500 });

		jest.advanceTimersByTime(500);
		expect(ticks.at(-1)).toEqual({ elapsed: 1000, interval: 500 });

		// Changing the interval mid-run restarts elapsed from zero and the
		// payload reports the new interval.
		clock.setAttribute("interval", "250");
		expect(ticks.at(-1)).toEqual({ elapsed: 0, interval: 250 });

		jest.advanceTimersByTime(250);
		expect(ticks.at(-1)).toEqual({ elapsed: 250, interval: 250 });
	});

	test("disconnecting mid-run stops tick events", () => {
		const clock = buildClock({ interval: "1000" });
		const ticks = collectDetails(clock, "tick");
		pageLoaded();

		jest.advanceTimersByTime(2000);
		const ticksBeforeRemoval = ticks.length;
		expect(ticksBeforeRemoval).toBeGreaterThan(0);

		clock.remove();
		jest.advanceTimersByTime(5000);
		expect(ticks).toHaveLength(ticksBeforeRemoval);
	});

	test("a clock added after page-loaded waits for the NEXT page-loaded event", () => {
		// Same reachable behavior as the timer: connectedCallback resets
		// pageLoadedForCurrentView, so a late-attached clock stays parked
		// until another drafter-page-loaded event fires.
		pageLoaded();
		const clock = buildClock({ interval: "1000" });

		jest.advanceTimersByTime(3000);
		expect(getLabel(clock).textContent).toBe("0:00");

		pageLoaded();
		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");
	});

	test("setting the persistent attribute mid-run restarts the clock", () => {
		// SUSPECTED DEAD CODE: like the timer, isPersistent() is never called;
		// changing "persistent" simply falls through to the restart branch.
		const clock = buildClock({ interval: "1000" });
		pageLoaded();

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");

		clock.setAttribute("persistent", "true");
		expect(getLabel(clock).textContent).toBe("0:00");
	});

	test("a persistence move keeps the clock running", () => {
		const clock = buildClock({ interval: "1000" }) as HTMLElement & {
			_drafterBeginMove(): void;
			_drafterEndMove(): void;
		};
		pageLoaded();

		jest.advanceTimersByTime(2000);
		expect(getLabel(clock).textContent).toBe("0:02");

		clock._drafterBeginMove();
		clock.remove();
		document.body.appendChild(clock);
		clock._drafterEndMove();

		jest.advanceTimersByTime(1000);
		expect(getLabel(clock).textContent).toBe("0:03");
	});
});
