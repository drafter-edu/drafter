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
