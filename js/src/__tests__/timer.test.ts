import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/timer";

describe("drafter-timer", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
	});

	afterEach(() => {
		jest.runOnlyPendingTimers();
		jest.useRealTimers();
		document.body.innerHTML = "";
	});

	function createTimer(attributes: Record<string, string> = {}): HTMLElement {
		const timer = document.createElement("drafter-timer");
		for (const [name, value] of Object.entries(attributes)) {
			timer.setAttribute(name, value);
		}
		document.body.appendChild(timer);
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		return timer;
	}

	function getLabel(timer: HTMLElement): HTMLSpanElement {
		const label = timer.querySelector("span");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Timer label was not rendered");
		}
		return label;
	}

	test("supports show attribute updates without stopping the timer", () => {
		const timer = createTimer({ duration: "3000", rate: "1000" });

		expect(timer.hidden).toBe(false);
		expect(getLabel(timer).textContent).toBe("0:03");

		timer.setAttribute("show", "false");
		expect(timer.hidden).toBe(true);

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		timer.removeAttribute("show");
		expect(timer.hidden).toBe(false);
	});

	test("does not start counting down before the page-loaded event", () => {
		const timer = document.createElement("drafter-timer");
		timer.setAttribute("duration", "3000");
		timer.setAttribute("rate", "1000");
		document.body.appendChild(timer);

		expect(getLabel(timer).textContent).toBe("0:03");
		jest.advanceTimersByTime(1500);
		expect(getLabel(timer).textContent).toBe("0:03");

		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");
	});

	test("pauses, resumes, finishes, and restarts from the controls", () => {
		const timer = createTimer({
			duration: "3000",
			rate: "1000",
			controls: "",
		});
		const finishListener = jest.fn();
		timer.addEventListener("finish", finishListener);

		const [toggleButton, restartButton] = Array.from(
			timer.querySelectorAll("button"),
		) as HTMLButtonElement[];

		expect(getLabel(timer).textContent).toBe("0:03");
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		toggleButton.click();
		expect(toggleButton.textContent).toBe("▶");

		jest.advanceTimersByTime(2000);
		expect(getLabel(timer).textContent).toBe("0:02");
		expect(finishListener).not.toHaveBeenCalled();

		toggleButton.click();
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(2000);
		expect(getLabel(timer).textContent).toBe("0:00");
		expect(finishListener).toHaveBeenCalledTimes(1);
		expect(toggleButton.textContent).toBe("▶");

		restartButton.click();
		expect(getLabel(timer).textContent).toBe("0:03");
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(3000);
		expect(finishListener).toHaveBeenCalledTimes(2);
	});

	test("restarts when duration or rate attributes change", () => {
		const timer = createTimer({ duration: "3000", rate: "1000" });

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		timer.setAttribute("duration", "5000");
		expect(getLabel(timer).textContent).toBe("0:05");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:04");

		timer.setAttribute("rate", "500");
		expect(getLabel(timer).textContent).toBe("0:05");

		const tickListener = jest.fn();
		timer.addEventListener("tick", tickListener);

		// The interval now fires at the new 500ms rate; with 4.5s remaining the
		// countdown label still rounds up to the next whole second.
		jest.advanceTimersByTime(500);
		expect(tickListener).toHaveBeenCalledTimes(1);
		expect(
			(tickListener.mock.calls[0][0] as CustomEvent).detail.remaining,
		).toBe(4500);
		expect(getLabel(timer).textContent).toBe("0:05");

		jest.advanceTimersByTime(500);
		expect(getLabel(timer).textContent).toBe("0:04");
	});
});

describe("drafter-timer (extended)", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML = "";
	});

	afterEach(() => {
		jest.runOnlyPendingTimers();
		jest.useRealTimers();
		document.body.innerHTML = "";
	});

	function buildTimer(attributes: Record<string, string> = {}): HTMLElement {
		const timer = document.createElement("drafter-timer");
		for (const [name, value] of Object.entries(attributes)) {
			timer.setAttribute(name, value);
		}
		document.body.appendChild(timer);
		return timer;
	}

	function pageLoaded(): void {
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
	}

	function getLabel(timer: HTMLElement): HTMLSpanElement {
		const label = timer.querySelector("span");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Timer label was not rendered");
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

	test("tick payloads carry remaining and duration across a run; finish carries zero", () => {
		const timer = buildTimer({ duration: "3000", rate: "1000" });
		const ticks = collectDetails(timer, "tick");
		const finishes = collectDetails(timer, "finish");

		pageLoaded();
		// beginRunning emits an immediate tick with the full duration left.
		expect(ticks).toEqual([{ remaining: 3000, duration: 3000 }]);

		jest.advanceTimersByTime(1000);
		expect(ticks.at(-1)).toEqual({ remaining: 2000, duration: 3000 });

		jest.advanceTimersByTime(1000);
		expect(ticks.at(-1)).toEqual({ remaining: 1000, duration: 3000 });

		jest.advanceTimersByTime(1000);
		expect(ticks.map((tick) => tick.remaining)).toEqual([
			3000, 2000, 1000, 0,
		]);
		for (const tick of ticks) {
			expect(tick.duration).toBe(3000);
		}
		expect(finishes).toEqual([{ remaining: 0, duration: 3000 }]);
	});

	test("toggling a finished timer restarts the countdown", () => {
		const timer = buildTimer({
			duration: "2000",
			rate: "1000",
			controls: "",
		});
		pageLoaded();
		const finishes = collectDetails(timer, "finish");

		jest.advanceTimersByTime(2000);
		expect(finishes).toHaveLength(1);
		const toggleButton = timer.querySelector("button")!;
		expect(toggleButton.textContent).toBe("▶");

		// resume() on a finished timer routes through restart().
		toggleButton.click();
		expect(getLabel(timer).textContent).toBe("0:02");
		expect(toggleButton.textContent).toBe("⏸");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:01");
		jest.advanceTimersByTime(1000);
		expect(finishes).toHaveLength(2);
	});

	test("controls can be added and removed mid-run without restarting", () => {
		const timer = buildTimer({ duration: "5000", rate: "1000" });
		pageLoaded();
		expect(timer.querySelectorAll("button")).toHaveLength(0);

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:04");

		timer.setAttribute("controls", "");
		const buttons = timer.querySelectorAll("button");
		expect(buttons).toHaveLength(2);
		// The countdown was not reset by the re-render.
		expect(getLabel(timer).textContent).toBe("0:04");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:03");

		// The freshly-added toggle is live: it pauses the running timer.
		(buttons[0] as HTMLButtonElement).click();
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:03");
		(buttons[0] as HTMLButtonElement).click();

		timer.removeAttribute("controls");
		expect(timer.querySelectorAll("button")).toHaveLength(0);
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");
	});

	test("disconnecting mid-run stops ticking and emits no further events", () => {
		const timer = buildTimer({ duration: "3000", rate: "1000" });
		const ticks = collectDetails(timer, "tick");
		const finishes = collectDetails(timer, "finish");
		pageLoaded();

		jest.advanceTimersByTime(1000);
		const ticksBeforeRemoval = ticks.length;
		expect(ticksBeforeRemoval).toBeGreaterThan(0);

		timer.remove();
		jest.advanceTimersByTime(5000);
		expect(ticks).toHaveLength(ticksBeforeRemoval);
		expect(finishes).toHaveLength(0);
	});

	test("a timer added after page-loaded starts without another page-loaded event", () => {
		// The module remembers that the current view already loaded, so a
		// late-inserted timer starts on its own (on the next task, letting a
		// pending persistence adoption or page-loaded event win first).
		pageLoaded();
		const timer = buildTimer({ duration: "3000", rate: "1000" });

		expect(getLabel(timer).textContent).toBe("0:03");
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:01");
	});

	test("a late-inserted timer removed before its deferred start never ticks", () => {
		pageLoaded();
		const timer = buildTimer({ duration: "3000", rate: "1000" });
		const ticks = collectDetails(timer, "tick");

		// Removed (e.g., replaced by persistence adoption) before the next
		// task runs: the deferred start must be cancelled.
		timer.remove();
		jest.advanceTimersByTime(3000);
		expect(ticks).toHaveLength(0);
	});

	test("a page-loaded event beats the deferred start and starts the timer once", () => {
		pageLoaded();
		const timer = buildTimer({ duration: "3000", rate: "1000" });
		const ticks = collectDetails(timer, "tick");

		// The next view finishes loading before the fallback task runs.
		pageLoaded();
		expect(ticks).toHaveLength(1);

		jest.advanceTimersByTime(1000);
		expect(ticks).toHaveLength(2);
		expect(getLabel(timer).textContent).toBe("0:02");
	});

	test("setting the persistent attribute mid-run does not restart the timer", () => {
		// Changing "persistent" only re-syncs the data-drafter-persistent
		// parking flag (read by the bridge's persistence machinery); the
		// countdown keeps running untouched.
		const timer = buildTimer({ duration: "3000", rate: "1000" });
		pageLoaded();

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		timer.setAttribute("persistent", "true");
		expect(getLabel(timer).textContent).toBe("0:02");
		expect(timer.getAttribute("data-drafter-persistent")).toBe("true");

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:01");

		timer.setAttribute("persistent", "false");
		expect(timer.hasAttribute("data-drafter-persistent")).toBe(false);
		expect(getLabel(timer).textContent).toBe("0:01");
	});

	test("a persistence move keeps the timer running", () => {
		const timer = buildTimer({
			duration: "3000",
			rate: "1000",
		}) as HTMLElement & {
			_drafterBeginMove(): void;
			_drafterEndMove(): void;
		};
		pageLoaded();

		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:02");

		timer._drafterBeginMove();
		timer.remove();
		document.body.appendChild(timer);
		timer._drafterEndMove();

		// Neither the disconnect nor the reconnect reset the countdown.
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:01");
	});
});
