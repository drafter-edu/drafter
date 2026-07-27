import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { DrafterHTMLElement } from "../components/drafterHTMLElement";

type LifecycleRecord = { event: "connected" | "disconnected"; moving: boolean };

class TestDrafterElement extends DrafterHTMLElement {
	lifecycle: LifecycleRecord[] = [];

	connectedCallback(): void {
		this.lifecycle.push({
			event: "connected",
			moving: this.isMovingBetweenParents(),
		});
	}

	disconnectedCallback(): void {
		this.lifecycle.push({
			event: "disconnected",
			moving: this.isMovingBetweenParents(),
		});
	}

	readBoolean(name: string, defaultValue: boolean): boolean {
		return this.getBooleanAttribute(name, defaultValue);
	}

	readNumber(name: string, defaultValue: number): number {
		return this.getNumberAttribute(name, defaultValue);
	}

	readHandlers(): Record<string, string> {
		return this.getHandlers();
	}

	readMoving(): boolean {
		return this.isMovingBetweenParents();
	}
}

customElements.define("test-drafter-element", TestDrafterElement);

function makeElement(
	attributes: Record<string, string> = {},
): TestDrafterElement {
	const element = document.createElement(
		"test-drafter-element",
	) as TestDrafterElement;
	for (const [name, value] of Object.entries(attributes)) {
		element.setAttribute(name, value);
	}
	return element;
}

afterEach(() => {
	document.body.innerHTML = "";
});

// ---------------------------------------------------------------------------
// getBooleanAttribute
// ---------------------------------------------------------------------------

describe("getBooleanAttribute", () => {
	test("absent attribute returns the default", () => {
		const element = makeElement();
		expect(element.readBoolean("flag", true)).toBe(true);
		expect(element.readBoolean("flag", false)).toBe(false);
	});

	test.each([
		// Bare/empty attribute (HTML boolean-attribute style) is true.
		["", true],
		["   ", true],
		// The attribute's own name as its value (disabled="disabled") is true.
		["flag", true],
		["FLAG", true],
		["FlAg", true],
		// Explicit truthy spellings.
		["true", true],
		["TRUE", true],
		["True", true],
		["1", true],
		["yes", true],
		["YES", true],
		["on", true],
		["On", true],
		// Explicit falsy spellings.
		["false", false],
		["FALSE", false],
		["False", false],
		["0", false],
		["no", false],
		["No", false],
		["off", false],
		["OFF", false],
		["none", false],
		["NONE", false],
		// Whitespace around a recognized value is trimmed.
		["  false  ", false],
		["  true  ", true],
	])("flag=%p parses to %p regardless of default", (value, expected) => {
		const element = makeElement({ flag: value });
		expect(element.readBoolean("flag", true)).toBe(expected);
		expect(element.readBoolean("flag", false)).toBe(expected);
	});

	test.each([["maybe"], ["2"], ["enabled"], ["truthy"], ["-1"]])(
		"unrecognized value %p falls back to the default",
		(value) => {
			const element = makeElement({ flag: value });
			expect(element.readBoolean("flag", true)).toBe(true);
			expect(element.readBoolean("flag", false)).toBe(false);
		},
	);

	test("name matching is case-insensitive against the queried name", () => {
		const element = makeElement({ muted: "MUTED" });
		expect(element.readBoolean("muted", false)).toBe(true);
	});
});

// ---------------------------------------------------------------------------
// getNumberAttribute
// ---------------------------------------------------------------------------

describe("getNumberAttribute", () => {
	test("absent attribute returns the default", () => {
		const element = makeElement();
		expect(element.readNumber("count", 7)).toBe(7);
		expect(element.readNumber("count", 0)).toBe(0);
	});

	test("absent attribute with a negative default returns it as-is", () => {
		// Only parsed attribute values are clamped to 0; a caller-supplied
		// default is returned unchanged.
		const element = makeElement();
		expect(element.readNumber("count", -3)).toBe(-3);
	});

	test.each([
		["42", 42],
		["0", 0],
		["  8", 8],
		// parseInt truncates: fractional attributes lose their fraction.
		["3.9", 3],
		// Negative values are clamped to 0.
		["-5", 0],
		// parseInt stops at the first non-numeric character.
		["12px", 12],
		["1e3", 1],
	])("count=%p parses to %p", (value, expected) => {
		const element = makeElement({ count: value });
		expect(element.readNumber("count", 99)).toBe(expected);
	});

	test.each([["abc"], [""], ["px12"], ["--3"]])(
		"non-numeric value %p falls back to the default",
		(value) => {
			const element = makeElement({ count: value });
			expect(element.readNumber("count", 99)).toBe(99);
		},
	);
});

// ---------------------------------------------------------------------------
// data--drafter-handlers parsing
// ---------------------------------------------------------------------------

describe("getHandlers", () => {
	test("missing attribute yields an empty mapping", () => {
		const element = makeElement();
		expect(element.readHandlers()).toEqual({});
	});

	test("empty attribute yields an empty mapping", () => {
		const element = makeElement({ "data--drafter-handlers": "" });
		expect(element.readHandlers()).toEqual({});
	});

	test("valid JSON parses to the handler mapping", () => {
		const element = makeElement({
			"data--drafter-handlers": JSON.stringify({
				click: "handle_click",
				change: "handle_change",
			}),
		});
		expect(element.readHandlers()).toEqual({
			click: "handle_click",
			change: "handle_change",
		});
	});

	test("invalid JSON warns and falls back to an empty mapping", () => {
		const warnSpy = jest
			.spyOn(console, "warn")
			.mockImplementation(() => {});
		try {
			const element = makeElement({ "data--drafter-handlers": "{oops" });
			expect(element.readHandlers()).toEqual({});
			expect(warnSpy).toHaveBeenCalled();
		} finally {
			warnSpy.mockRestore();
		}
	});

	test("non-object JSON is returned as-is without validation", () => {
		// Documents actual behavior: the parsed value is not shape-checked,
		// so an array (or any JSON value) passes straight through.
		const element = makeElement({ "data--drafter-handlers": '["a", "b"]' });
		expect(element.readHandlers()).toEqual(["a", "b"]);
	});
});

// ---------------------------------------------------------------------------
// Move-aware lifecycle. persistence.test.ts covers component-level behavior
// (timer/clock survive protocol moves); this covers the base-class contract.
// ---------------------------------------------------------------------------

describe("move-aware lifecycle", () => {
	test("elements are not moving by default", () => {
		const element = makeElement();
		expect(element.readMoving()).toBe(false);
	});

	test("beginMove marks the element and endMove clears it", () => {
		const element = makeElement();
		element._drafterBeginMove();
		expect(element.readMoving()).toBe(true);
		element._drafterEndMove();
		expect(element.readMoving()).toBe(false);
	});

	test("connectedMoveCallback is a callable no-op", () => {
		const element = makeElement();
		expect(typeof element.connectedMoveCallback).toBe("function");
		expect(element.connectedMoveCallback()).toBeUndefined();
	});

	test("lifecycle callbacks observe the moving mark during a protocol move", () => {
		const parkingLot = document.createElement("div");
		const page = document.createElement("div");
		document.body.append(page, parkingLot);

		const element = makeElement();
		page.appendChild(element);
		expect(element.lifecycle).toEqual([
			{ event: "connected", moving: false },
		]);

		element.lifecycle = [];
		element._drafterBeginMove();
		parkingLot.appendChild(element);
		element._drafterEndMove();
		expect(element.lifecycle).toEqual([
			{ event: "disconnected", moving: true },
			{ event: "connected", moving: true },
		]);

		// A plain reparent without the protocol sees moving=false, so
		// components tear down and restart as with a normal removal.
		element.lifecycle = [];
		page.appendChild(element);
		expect(element.lifecycle).toEqual([
			{ event: "disconnected", moving: false },
			{ event: "connected", moving: false },
		]);
	});

	test("a real removal after a protocol move sees moving=false", () => {
		const element = makeElement();
		document.body.appendChild(element);

		element._drafterBeginMove();
		document.body.removeChild(element);
		document.body.appendChild(element);
		element._drafterEndMove();

		element.lifecycle = [];
		element.remove();
		expect(element.lifecycle).toEqual([
			{ event: "disconnected", moving: false },
		]);
	});
});
