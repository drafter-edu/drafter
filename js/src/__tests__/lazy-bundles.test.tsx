/**
 * Tests for on-demand bundle loading (js/src/lazy.ts) and the first feature
 * built on it: the Edit > Convert HTML to Drafter dialog
 * (js/src/debug/htmlconvert.tsx), whose converter lives in its own bundle
 * so it does not enlarge every page's download.
 */
import { afterEach, beforeEach, describe, expect, jest, test } from "@jest/globals";

import {
	findMainBundleUrl,
	loadLazyBundle,
	resetLazyBundlesForTesting,
	resolveLazyBundleUrl,
} from "../lazy";
import { openHtmlConverter } from "../debug/htmlconvert";
import { convertHtmlToDrafter } from "../transpiler.index";

type Scope = Record<string, unknown>;

function addMainBundleScript(src: string): HTMLScriptElement {
	const script = document.createElement("script");
	script.setAttribute("src", src);
	document.head.appendChild(script);
	return script;
}

function lazyScripts(): HTMLScriptElement[] {
	return Array.from(
		document.head.querySelectorAll<HTMLScriptElement>(
			'script[src*="drafter.sample"]',
		),
	);
}

/** Let pending promise callbacks run. */
async function settle(): Promise<void> {
	await new Promise((resolve) => setTimeout(resolve, 0));
}

afterEach(async () => {
	document
		.querySelectorAll<HTMLButtonElement>(".drafter-dialog-close")
		.forEach((button) => button.click());
	await settle();
	document.head.innerHTML = "";
	document.body.innerHTML = "";
	delete (window as unknown as Scope).DrafterSample;
	resetLazyBundlesForTesting();
});

describe("resolveLazyBundleUrl", () => {
	test("sits beside the main bundle", () => {
		expect(
			resolveLazyBundleUrl(
				"drafter.transpiler",
				"https://site.example/assets/js/drafter.pyodide.js",
			),
		).toBe("https://site.example/assets/js/drafter.transpiler.js");
	});

	test("keeps the version stamp so an upgrade refetches it too", () => {
		expect(
			resolveLazyBundleUrl(
				"drafter.transpiler",
				"http://localhost:8000/__drafter_assets/js/drafter.pyodide.js?v=2.1.4",
			),
		).toBe(
			"http://localhost:8000/__drafter_assets/js/drafter.transpiler.js?v=2.1.4",
		);
	});

	test("works for a bundle served from the site root", () => {
		expect(
			resolveLazyBundleUrl("drafter.transpiler", "/drafter.skulpt.js"),
		).toBe("/drafter.transpiler.js");
	});
});

describe("findMainBundleUrl", () => {
	test("finds the Pyodide bundle's script", () => {
		addMainBundleScript("https://site.example/a/js/drafter.pyodide.js?v=9");

		expect(findMainBundleUrl()).toBe(
			"https://site.example/a/js/drafter.pyodide.js?v=9",
		);
	});

	test("finds the Skulpt bundle's script", () => {
		addMainBundleScript("https://site.example/a/js/drafter.skulpt.js");

		expect(findMainBundleUrl()).toContain("drafter.skulpt.js");
	});

	test("is null when no Drafter script is on the page", () => {
		addMainBundleScript("https://cdn.example/some-other-library.js");

		expect(findMainBundleUrl()).toBeNull();
	});
});

describe("loadLazyBundle", () => {
	beforeEach(() => {
		addMainBundleScript("https://site.example/a/js/drafter.pyodide.js?v=9");
	});

	/** Act as the browser finishing the download of the lazy script. */
	function finishLoading(defineGlobal: boolean = true) {
		if (defineGlobal) {
			(window as unknown as Scope).DrafterSample = { answer: 42 };
		}
		lazyScripts()[0].dispatchEvent(new Event("load"));
	}

	test("adds one script beside the main bundle and resolves with its global", async () => {
		const loading = loadLazyBundle<{ answer: number }>(
			"drafter.sample",
			"DrafterSample",
		);

		expect(lazyScripts().map((script) => script.src)).toEqual([
			"https://site.example/a/js/drafter.sample.js?v=9",
		]);
		finishLoading();

		expect((await loading).answer).toBe(42);
	});

	test("concurrent and later calls share a single download", async () => {
		const first = loadLazyBundle("drafter.sample", "DrafterSample");
		const second = loadLazyBundle("drafter.sample", "DrafterSample");
		finishLoading();
		await Promise.all([first, second]);

		await loadLazyBundle("drafter.sample", "DrafterSample");

		expect(lazyScripts()).toHaveLength(1);
	});

	test("a global that is already defined needs no download", async () => {
		(window as unknown as Scope).DrafterSample = { answer: 7 };

		const bundle = await loadLazyBundle<{ answer: number }>(
			"drafter.sample",
			"DrafterSample",
		);

		expect(bundle.answer).toBe(7);
		expect(lazyScripts()).toHaveLength(0);
	});

	test("a failed download rejects, removes the script, and can be retried", async () => {
		const failing = loadLazyBundle("drafter.sample", "DrafterSample");
		lazyScripts()[0].dispatchEvent(new Event("error"));

		await expect(failing).rejects.toThrow("Could not load");
		await settle();
		expect(lazyScripts()).toHaveLength(0);

		const retry = loadLazyBundle("drafter.sample", "DrafterSample");
		finishLoading();
		await expect(retry).resolves.toEqual({ answer: 42 });
	});

	test("a script that defines nothing is reported", async () => {
		const loading = loadLazyBundle("drafter.sample", "DrafterSample");
		finishLoading(false);

		await expect(loading).rejects.toThrow("did not define DrafterSample");
	});

	test("explains when Drafter's own script cannot be found", async () => {
		document.head.innerHTML = "";

		await expect(
			loadLazyBundle("drafter.sample", "DrafterSample"),
		).rejects.toThrow("main script was not found");
	});
});

describe("the converter bundle's entry point", () => {
	test("turns HTML into Drafter code", () => {
		const code = convertHtmlToDrafter(
			'<h1>Hello</h1><input type="range" name="volume">',
		);

		expect(code).toContain("def index(state: State) -> Page:");
		expect(code).toContain("Hello");
		expect(code).toContain('Slider("volume", 0, 100)');
	});
});

describe("Convert HTML to Drafter dialog", () => {
	function dialog(): HTMLElement {
		return document.querySelector(".drafter-html-converter") as HTMLElement;
	}
	function field<T extends HTMLElement>(cls: string): T {
		return dialog().querySelector(`.${cls}`) as T;
	}
	function outputText(): string {
		return field<HTMLElement>("drafter-html-converter-output").textContent ?? "";
	}
	function statusText(): string {
		return field<HTMLElement>("drafter-html-converter-status").textContent ?? "";
	}
	async function convert(html: string) {
		field<HTMLTextAreaElement>("drafter-html-converter-input").value = html;
		field<HTMLButtonElement>("drafter-html-converter-convert").click();
		await settle();
		await settle();
	}

	test("opens with an empty input, a disabled Copy, and no converter loaded", () => {
		const load = jest.fn(async () => (html: string) => html);

		openHtmlConverter(load);

		expect(dialog()).not.toBeNull();
		expect(
			field<HTMLButtonElement>("drafter-html-converter-copy").disabled,
		).toBe(true);
		// Opening the dialog alone must not download anything.
		expect(load).not.toHaveBeenCalled();
	});

	test("Convert loads the converter and shows the generated Python", async () => {
		const load = jest.fn(async () => convertHtmlToDrafter);
		openHtmlConverter(load);

		await convert("<h1>Corgi Cafe</h1>");

		expect(load).toHaveBeenCalledTimes(1);
		expect(outputText()).toContain("Corgi Cafe");
		expect(outputText()).toContain("Page(");
		expect(
			field<HTMLButtonElement>("drafter-html-converter-copy").disabled,
		).toBe(false);
		expect(statusText()).toContain("Converted");
	});

	test("an empty input asks for HTML and loads nothing", async () => {
		const load = jest.fn(async () => convertHtmlToDrafter);
		openHtmlConverter(load);

		await convert("   ");

		expect(load).not.toHaveBeenCalled();
		expect(statusText()).toContain("Paste some HTML first");
	});

	test("a converter that cannot be downloaded says so and can be retried", async () => {
		let attempts = 0;
		const load = jest.fn(async () => {
			attempts += 1;
			if (attempts === 1) {
				throw new Error("Could not load drafter.transpiler.js");
			}
			return convertHtmlToDrafter;
		});
		openHtmlConverter(load);

		await convert("<p>Hi</p>");
		expect(statusText()).toContain("Could not load the converter");
		expect(
			field<HTMLButtonElement>("drafter-html-converter-convert").disabled,
		).toBe(false);

		await convert("<p>Hi</p>");
		expect(outputText()).toContain("Hi");
	});

	test("a conversion error is shown with its message", async () => {
		const load = async () => () => {
			throw new Error("unexpected end of input");
		};
		openHtmlConverter(load);

		await convert("<p>broken");

		expect(statusText()).toContain("unexpected end of input");
		expect(
			field<HTMLButtonElement>("drafter-html-converter-copy").disabled,
		).toBe(true);
	});

	test("choosing a file fills the input and converts it", async () => {
		openHtmlConverter(async () => convertHtmlToDrafter);
		const upload = field<HTMLInputElement>("drafter-html-converter-upload");
		const file = new File(["<h2>From a file</h2>"], "page.html", {
			type: "text/html",
		});
		// jsdom's File has no text(); supply the browser behavior.
		Object.defineProperty(file, "text", {
			value: async () => "<h2>From a file</h2>",
		});
		Object.defineProperty(upload, "files", { value: [file] });

		upload.dispatchEvent(new Event("change"));
		await settle();
		await settle();

		expect(
			field<HTMLTextAreaElement>("drafter-html-converter-input").value,
		).toBe("<h2>From a file</h2>");
		expect(outputText()).toContain("From a file");
	});

	test("Copy puts the generated Python on the clipboard", async () => {
		const writeText = jest.fn(async (_text: string) => {});
		Object.defineProperty(navigator, "clipboard", {
			value: { writeText },
			configurable: true,
		});
		openHtmlConverter(async () => convertHtmlToDrafter);
		await convert("<h1>Copy me</h1>");

		field<HTMLButtonElement>("drafter-html-converter-copy").click();
		await settle();

		expect(writeText).toHaveBeenCalledTimes(1);
		expect(writeText.mock.calls[0][0]).toContain("Copy me");
		expect(statusText()).toContain("Copied");
	});
});
