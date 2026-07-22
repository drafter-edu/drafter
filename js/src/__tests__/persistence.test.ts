import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import "../components/timer";

type MovableElement = HTMLElement & {
	_drafterBeginMove: () => void;
	_drafterEndMove: () => void;
};

describe("persistence move protocol", () => {
	beforeEach(() => {
		jest.useFakeTimers();
		document.body.innerHTML =
			'<div id="page"></div><div id="parking" hidden></div>';
	});

	afterEach(() => {
		jest.runOnlyPendingTimers();
		jest.useRealTimers();
		document.body.innerHTML = "";
	});

	function getPage(): HTMLElement {
		return document.getElementById("page") as HTMLElement;
	}

	function getParking(): HTMLElement {
		return document.getElementById("parking") as HTMLElement;
	}

	function createElement(
		tag: string,
		attributes: Record<string, string>,
	): MovableElement {
		const element = document.createElement(tag) as MovableElement;
		for (const [name, value] of Object.entries(attributes)) {
			element.setAttribute(name, value);
		}
		getPage().appendChild(element);
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		return element;
	}

	function getLabel(element: HTMLElement): HTMLSpanElement {
		const label = element.querySelector("span");
		if (!(label instanceof HTMLSpanElement)) {
			throw new Error("Label was not rendered");
		}
		return label;
	}

	function protocolMove(element: MovableElement, destination: HTMLElement) {
		element._drafterBeginMove();
		destination.appendChild(element);
		element._drafterEndMove();
	}

	test("timer keeps counting down through a protocol move", () => {
		const timer = createElement("drafter-timer", {
			duration: "10000",
			rate: "1000",
		});

		jest.advanceTimersByTime(3000);
		expect(getLabel(timer).textContent).toBe("0:07");

		protocolMove(timer, getParking());
		jest.advanceTimersByTime(2000);
		expect(getLabel(timer).textContent).toBe("0:05");

		protocolMove(timer, getPage());
		jest.advanceTimersByTime(2000);
		expect(getLabel(timer).textContent).toBe("0:03");
	});

	test("timer finish still fires while parked", () => {
		const timer = createElement("drafter-timer", {
			duration: "5000",
			rate: "1000",
		});
		const finishes: Event[] = [];
		timer.addEventListener("finish", (event) => finishes.push(event));

		jest.advanceTimersByTime(1000);
		protocolMove(timer, getParking());
		jest.advanceTimersByTime(5000);
		expect(finishes).toHaveLength(1);
	});

	test("timer without the protocol resets on a move (baseline)", () => {
		const timer = createElement("drafter-timer", {
			duration: "10000",
			rate: "1000",
		});

		jest.advanceTimersByTime(3000);
		expect(getLabel(timer).textContent).toBe("0:07");

		getParking().appendChild(timer);
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		jest.advanceTimersByTime(1000);
		expect(getLabel(timer).textContent).toBe("0:09");
	});

	test("clock keeps elapsed time through a protocol move", () => {
		const clock = createElement("drafter-clock", { interval: "1000" });

		jest.advanceTimersByTime(4000);
		expect(getLabel(clock).textContent).toBe("0:04");

		protocolMove(clock, getParking());
		jest.advanceTimersByTime(3000);
		expect(getLabel(clock).textContent).toBe("0:07");

		protocolMove(clock, getPage());
		jest.advanceTimersByTime(1000);
		expect(getLabel(clock).textContent).toBe("0:08");
	});

	test("real removal after a protocol move still tears down", () => {
		const clock = createElement("drafter-clock", { interval: "1000" });
		protocolMove(clock, getParking());

		// Eviction is a plain remove(): teardown must run normally.
		clock.remove();
		jest.advanceTimersByTime(3000);

		// Re-attach without the protocol: a fresh lifecycle starts from zero.
		getPage().appendChild(clock);
		window.dispatchEvent(new CustomEvent("drafter-page-loaded"));
		expect(getLabel(clock).textContent).toBe("0:00");
	});
});
