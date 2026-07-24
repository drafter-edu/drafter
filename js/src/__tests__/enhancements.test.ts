import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	enhanceCodeSnippetsWithCopyButtons,
	enhanceExpandables,
} from "../enhancements";

describe("enhanceCodeSnippetsWithCopyButtons", () => {
	let writeText: jest.Mock<(text: string) => Promise<void>>;

	beforeEach(() => {
		// jsdom has no navigator.clipboard; install a recording stub.
		writeText = jest.fn<(text: string) => Promise<void>>(() =>
			Promise.resolve(),
		);
		Object.defineProperty(navigator, "clipboard", {
			value: { writeText },
			configurable: true,
		});
	});

	afterEach(() => {
		delete (navigator as { clipboard?: unknown }).clipboard;
		document.body.innerHTML = "";
		jest.useRealTimers();
	});

	test("injects a copy button into every .copyable snippet", () => {
		document.body.innerHTML =
			'<pre class="copyable">print(1)</pre>' +
			'<pre class="copyable">print(2)</pre>' +
			"<pre>not copyable</pre>";

		enhanceCodeSnippetsWithCopyButtons();

		const copyable = document.querySelectorAll(".copyable");
		copyable.forEach((snippet) => {
			const buttons = snippet.querySelectorAll("button.copy-button");
			expect(buttons).toHaveLength(1);
			// The button is prepended before the original content.
			expect(snippet.firstElementChild).toBe(buttons[0]);
		});
		// Untagged snippets are untouched.
		expect(
			document.querySelectorAll("pre:not(.copyable) button"),
		).toHaveLength(0);
		// The original code text is preserved after injection.
		expect(copyable[0].textContent).toContain("print(1)");
	});

	test("clicking copies the original snippet text (without the button label)", () => {
		document.body.innerHTML = '<pre class="copyable">x = 42</pre>';
		enhanceCodeSnippetsWithCopyButtons();

		const button = document.querySelector(
			"button.copy-button",
		) as HTMLButtonElement;
		button.click();

		// The text was captured before the button markup was injected, so the
		// clipboard receives exactly the snippet source.
		expect(writeText).toHaveBeenCalledTimes(1);
		expect(writeText).toHaveBeenCalledWith("x = 42");
	});

	test("button label shows 'Copied!' then resets after one second", () => {
		jest.useFakeTimers();
		document.body.innerHTML = '<pre class="copyable">y = 3</pre>';
		enhanceCodeSnippetsWithCopyButtons();

		const button = document.querySelector(
			"button.copy-button",
		) as HTMLButtonElement;
		button.click();
		expect(button.innerText).toBe("Copied!");

		jest.advanceTimersByTime(999);
		expect(button.innerText).toBe("Copied!");
		jest.advanceTimersByTime(1);
		expect(button.innerText).toBe("\u{1F4CB}");
	});

	test("each snippet's button copies its own text", () => {
		document.body.innerHTML =
			'<pre class="copyable">first()</pre>' +
			'<pre class="copyable">second()</pre>';
		enhanceCodeSnippetsWithCopyButtons();

		const buttons = document.querySelectorAll<HTMLButtonElement>(
			"button.copy-button",
		);
		buttons[1].click();
		buttons[0].click();

		expect(writeText).toHaveBeenNthCalledWith(1, "second()");
		expect(writeText).toHaveBeenNthCalledWith(2, "first()");
	});
});

describe("enhanceExpandables", () => {
	afterEach(() => {
		document.body.innerHTML = "";
	});

	const LONG_TEXT = "a".repeat(150);

	test("long content is truncated to 100 characters plus ellipsis", () => {
		document.body.innerHTML = `<span class="expandable">${LONG_TEXT}</span>`;

		enhanceExpandables();

		const expandable = document.querySelector(
			".expandable",
		) as HTMLElement;
		expect(expandable.textContent).toBe("a".repeat(100) + "...");
		expect(expandable.style.cursor).toBe("pointer");
	});

	test("short content is left untouched and not clickable", () => {
		const shortText = "short content";
		document.body.innerHTML = `<span class="expandable">${shortText}</span>`;

		enhanceExpandables();

		const expandable = document.querySelector(
			".expandable",
		) as HTMLElement;
		expect(expandable.textContent).toBe(shortText);
		expect(expandable.style.cursor).toBe("");

		// No toggle behavior was attached.
		expandable.click();
		expect(expandable.textContent).toBe(shortText);
	});

	test("content of exactly 100 characters is not truncated", () => {
		const exact = "b".repeat(100);
		document.body.innerHTML = `<span class="expandable">${exact}</span>`;

		enhanceExpandables();

		expect(document.querySelector(".expandable")?.textContent).toBe(exact);
	});

	test("clicking toggles between truncated and full content", () => {
		document.body.innerHTML = `<span class="expandable">${LONG_TEXT}</span>`;
		enhanceExpandables();

		const expandable = document.querySelector(
			".expandable",
		) as HTMLElement;

		expandable.click();
		expect(expandable.textContent).toBe(LONG_TEXT);

		expandable.click();
		expect(expandable.textContent).toBe("a".repeat(100) + "...");

		expandable.click();
		expect(expandable.textContent).toBe(LONG_TEXT);
	});

	// The toggle tracks its expanded state explicitly, so full content that
	// itself ends with "..." still collapses correctly.
	test("full content ending in '...' still toggles both ways", () => {
		const trickyText = "c".repeat(120) + "...";
		document.body.innerHTML = `<span class="expandable">${trickyText}</span>`;
		enhanceExpandables();

		const expandable = document.querySelector(
			".expandable",
		) as HTMLElement;
		expect(expandable.textContent).toBe("c".repeat(100) + "...");

		expandable.click();
		expect(expandable.textContent).toBe(trickyText);

		expandable.click();
		expect(expandable.textContent).toBe("c".repeat(100) + "...");
	});

	test("multiple expandables toggle independently", () => {
		const textA = "x".repeat(150);
		const textB = "y".repeat(150);
		document.body.innerHTML =
			`<span class="expandable" id="a">${textA}</span>` +
			`<span class="expandable" id="b">${textB}</span>`;
		enhanceExpandables();

		const a = document.getElementById("a") as HTMLElement;
		const b = document.getElementById("b") as HTMLElement;

		a.click();
		expect(a.textContent).toBe(textA);
		expect(b.textContent).toBe("y".repeat(100) + "...");
	});
});
