import { describe, expect, test } from "@jest/globals";

import {
	handleSystemError,
	normalizeSystemError,
	presentSystemError,
} from "../bridge/engine";

describe("system error helpers", () => {
	test("normalizeSystemError wraps non-Error values", () => {
		const error = normalizeSystemError("boom");

		expect(error).toBeInstanceOf(Error);
		expect(error.message).toBe("boom");
	});

	test("presentSystemError can render into the Drafter root", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		const error = presentSystemError(
			"Failed to initialize",
			new Error("boom"),
			{
				presentation: "root",
				suggestion: "Reload and try again.",
			},
		);

		const root = document.getElementById("drafter-root--");
		expect(error).toBeInstanceOf(Error);
		expect(root?.textContent).toContain("Drafter System Error");
		expect(root?.textContent).toContain("Failed to initialize");
		expect(root?.textContent).toContain("Reload and try again.");
		expect(root?.textContent).toContain("Error: boom");
	});

	test("handleSystemError returns the normalized error", () => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';

		const error = handleSystemError(
			"Failed to initialize",
			"boom",
			"Reload and try again.",
		);

		expect(error).toBeInstanceOf(Error);
		expect(error.message).toBe("boom");
	});
});
