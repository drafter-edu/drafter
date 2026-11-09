// Suite C of JS_TESTING_PLAN.md: browser-only features jsdom can't exercise —
// real file uploads, geolocation emulation, real downloads.

import { test, expect } from "playwright/test";

declare global {
	interface Window {
		bootRuntime: () => Promise<void>;
		runExample: (code: string, presentErrors?: boolean) => Promise<void>;
	}
}

const UPLOAD_APP = `
from drafter import *
hide_debug_information()

@dataclass
class State:
    content: str

@route
def index(state: State):
    return Page(state, [
        "Upload a file:",
        FileUpload("doc"),
        Button("Submit", process),
    ])

@route
def process(state: State, doc: str):
    state.content = doc
    return Page(state, [
        f"Received: {state.content}",
        Button("Back", index),
    ])

start_server(State(""))
`;

test("file upload round-trips real file content through a route", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, UPLOAD_APP);

	await page.locator('input[type="file"]').setInputFiles({
		name: "hello.txt",
		mimeType: "text/plain",
		buffer: Buffer.from("hello from playwright"),
	});
	await page.getByRole("button", { name: "Submit" }).click();

	await expect(page.locator("#drafter-root--")).toContainText(
		"Received: hello from playwright",
	);
});

const RUNAWAY_APP = `
import asyncio
from drafter import *

# Yielding infinite loop: never reaches start_server, but keeps the event
# loop responsive so the interrupt can be delivered from JS.
async def spin():
    while True:
        await asyncio.sleep(0.01)

await spin()

start_server()
`;

const AFTER_INTERRUPT_APP = `
from drafter import *
hide_debug_information()

@route
def index(state):
    return Page(state, ["Recovered after interrupt"])

start_server()
`;

test("interruptActiveRun stops a runaway app and the runtime stays usable", async ({
	page,
}) => {
	await page.goto("/harness.html");

	const outcome = await page.evaluate(async (code) => {
		await window.bootRuntime();
		// Deliberately NOT awaited: this run spins forever until interrupted.
		const runaway = (
			window as unknown as {
				Drafter: {
					runStudentCode: (options: {
						code: string;
						presentErrors: boolean;
					}) => Promise<unknown>;
					interruptActiveRun: () => void;
				};
			}
		).Drafter;
		const running = runaway
			.runStudentCode({ code, presentErrors: false })
			.then(
				() => "resolved",
				(error: unknown) => `rejected: ${String(error).slice(0, 1500)}`,
			);
		// Give the loop time to start spinning, then interrupt. Re-signal
		// periodically (like a user mashing stop) until the run settles.
		await new Promise((resolve) => setTimeout(resolve, 500));
		runaway.interruptActiveRun();
		const nag = setInterval(() => runaway.interruptActiveRun(), 500);
		// Never hang the test: report if the interrupt failed to land.
		const timeout = new Promise<string>((resolve) =>
			setTimeout(() => resolve("still-running-after-interrupt"), 10000),
		);
		const result = await Promise.race([running, timeout]);
		clearInterval(nag);
		return result;
	}, RUNAWAY_APP);
	console.log("interrupt outcome:", outcome.slice(0, 400));

	expect(outcome).toContain("rejected");
	// KeyboardInterrupt is the normal delivery; CancelledError is the
	// escalation path (the signal landed in the event loop's own callback
	// machinery, and the orphaned run was cancelled instead — see
	// scheduleInterruptEscalation in pyodide.index.tsx).
	expect(outcome).toMatch(/KeyboardInterrupt|CancelledError/);

	// The interpreter survives: a normal app runs afterwards.
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, AFTER_INTERRUPT_APP);
	await expect(page.locator("#drafter-root--")).toContainText(
		"Recovered after interrupt",
	);
});

const GEOLOCATION_APP = `
from drafter import *
hide_debug_information()

@route
def index(state):
    return Page(state, [
        "Where are you?",
        CurrentLocation("user_location", show_coordinates=True),
    ])

start_server()
`;

test.describe("geolocation", () => {
	test.use({
		geolocation: { latitude: 39.68, longitude: -75.75, accuracy: 12 },
		permissions: ["geolocation"],
	});

	test("granted permission surfaces real coordinates in the component", async ({
		page,
	}) => {
		await page.goto("/harness.html");
		await page.evaluate(async (code) => {
			await window.runExample(code);
		}, GEOLOCATION_APP);

		// Permission is already granted, so the component's permissions-API
		// check auto-requests the position without a click.
		await expect(page.locator(".drafter-geolocation-coords")).toContainText(
			"39.680000, -75.750000",
		);
	});
});

const DOWNLOAD_APP = `
from drafter import *
hide_debug_information()

@route
def index(state):
    return Page(state, [
        "Get your file:",
        Download("Download It", "hello.txt", "downloaded content", "text/plain"),
    ])

start_server()
`;

test("Download component produces a real browser download", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, DOWNLOAD_APP);

	const downloadPromise = page.waitForEvent("download");
	await page.locator('a[download="hello.txt"]').click();
	const download = await downloadPromise;

	expect(download.suggestedFilename()).toBe("hello.txt");
	const stream = await download.createReadStream();
	const chunks: Buffer[] = [];
	for await (const chunk of stream) {
		chunks.push(chunk as Buffer);
	}
	expect(Buffer.concat(chunks).toString("utf-8")).toBe("downloaded content");
});

// drafter-edu/drafter#232: a stylesheet that cannot be fetched used to leave
// the site unstyled with no explanation. jsdom never fetches stylesheets, so
// only a real browser can show the <link> error event reaching the notice.
const MISSING_STYLESHEET_URL = "https://drafter-test.invalid/missing-style.css";
const MISSING_STYLESHEET_APP = `
from drafter import *
hide_debug_information()
add_website_css_file("${MISSING_STYLESHEET_URL}")

@route
def index() -> Page:
    return Page(["The page still works"])

start_server()
`;

test("a stylesheet that fails to load shows a dismissible notice", async ({
	page,
}) => {
	await page.route(MISSING_STYLESHEET_URL, (route) => route.abort());
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, MISSING_STYLESHEET_APP);

	const notice = page.locator("#drafter-stylesheet-notice--");
	await expect(notice).toContainText("styling did not load");
	await expect(notice.locator("li")).toHaveText([MISSING_STYLESHEET_URL]);
	// The app itself is unaffected.
	await expect(page.locator("#drafter-root--")).toContainText(
		"The page still works",
	);

	await notice.getByRole("button", { name: "Dismiss" }).click();
	await expect(notice).toHaveCount(0);
});

// Slider and ColorPicker submit through real browser controls, which jsdom
// only imitates: the range input's stepping, the color input's value
// normalization, and (with alpha on) the inline handlers that keep the
// hidden field in step with the swatch and the opacity slider.
const PICKERS_APP = `
from drafter import *
hide_debug_information()

@dataclass
class State:
    report: str

@route
def index(state: State) -> Page:
    return Page(state, [
        Output("report", [state.report]),
        Slider("size", 0, 100, 25, step=5),
        ColorPicker("plain", "tomato"),
        ColorPicker("glass", [51, 102, 255, 255], alpha=True),
        Button("Send", save),
    ])

@route
def save(state: State, size: int, plain: list[int], glass: Color) -> Page:
    state.report = (
        "size=" + str(size)
        + " plain=" + str(plain)
        + " glass=" + str(glass.to_list(alpha=True))
        + " hex=" + glass.to_hex()
    )
    return index(state)

start_server(State("nothing sent yet"))
`;

test("Slider and ColorPicker deliver their values in the annotated forms", async ({
	page,
}) => {
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, PICKERS_APP);
	const root = page.locator("#drafter-root--");
	await expect(root).toContainText("nothing sent yet");

	// Untouched controls submit their starting values: the named color and
	// the list were both turned into hex codes for the browser.
	await page.getByRole("button", { name: "Send" }).click();
	await expect(root).toContainText(
		"size=25 plain=[255, 99, 71] glass=[51, 102, 255, 255] hex=#3366ff",
	);

	// Change all three the way a visitor would.
	await page.locator('input[name="size"]').fill("60");
	await page.locator('input[name="plain"]').fill("#00ff00");
	await page.locator("#glass").fill("#ff8800");
	await page.getByLabel("glass opacity").fill("128");
	await page.getByRole("button", { name: "Send" }).click();
	await expect(root).toContainText(
		"size=60 plain=[0, 255, 0] glass=[255, 136, 0, 128] hex=#ff880080",
	);
});

// The converter is a separate bundle fetched on first use (js/src/lazy.ts).
// Only a real browser can show the whole path: the menu item, the script
// request for drafter.transpiler.js beside the main bundle, and the result.
const CONVERTER_HOST_APP = `
from drafter import *

@route
def index() -> Page:
    return Page(["A page with the debug panel open"])

start_server()
`;

test("Convert HTML to Drafter loads its bundle on demand and converts", async ({
	page,
}) => {
	const transpilerRequests: string[] = [];
	page.on("request", (request) => {
		if (request.url().includes("drafter.transpiler.js")) {
			transpilerRequests.push(request.url());
		}
	});
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, CONVERTER_HOST_APP);
	await expect(page.locator("#drafter-root--")).toContainText(
		"A page with the debug panel open",
	);
	// Nothing is downloaded until the converter is actually used.
	expect(transpilerRequests).toHaveLength(0);

	await page.locator(".drafter-menu-button-edit").click();
	await page.locator(".drafter-menu-item-convert-html").click();
	const dialog = page.locator(".drafter-html-converter");
	await expect(dialog).toBeVisible();
	expect(transpilerRequests).toHaveLength(0);

	await dialog
		.locator(".drafter-html-converter-input")
		.fill('<h1>Corgi Cafe</h1><input type="color" name="ink" value="#ff8800">');
	await dialog.locator(".drafter-html-converter-convert").click();

	const output = dialog.locator(".drafter-html-converter-output");
	await expect(output).toContainText("Corgi Cafe");
	await expect(output).toContainText('ColorPicker("ink", default_value="#ff8800")');
	await expect(dialog.locator(".drafter-html-converter-copy")).toBeEnabled();
	expect(transpilerRequests).toHaveLength(1);
	expect(transpilerRequests[0]).toContain("/js/drafter.transpiler.js");

	// A second conversion reuses the loaded converter.
	await dialog.locator(".drafter-html-converter-input").fill("<p>Again</p>");
	await dialog.locator(".drafter-html-converter-convert").click();
	await expect(output).toContainText("Again");
	expect(transpilerRequests).toHaveLength(1);
});

// Mirrors examples/piano.py: each key returns a Fragment holding a hidden,
// auto-playing Tone. The tone used to wait forever for a page-loaded event
// that only full page loads dispatched, so the piano made no sound.
const FRAGMENT_TONE_APP = `
from drafter import *
hide_debug_information()

@route
def index() -> Page:
    return Page([
        Button("A4", "play_note", [Argument("note", "A4")]),
        Output("sound_area", ["Click a key"]),
    ])

@route
def play_note(note: str) -> Fragment:
    return Fragment(
        [Tone(note, duration=200, auto_play=True, show=False)],
        target="#sound_area",
    )

start_server()
`;

test("an auto-play Tone inserted by a Fragment plays", async ({ page }) => {
	await page.addInitScript(() => {
		const started: number[] = [];
		(window as unknown as { startedOscillators: number[] }).startedOscillators =
			started;
		const originalStart = OscillatorNode.prototype.start;
		OscillatorNode.prototype.start = function (
			this: OscillatorNode,
			...args: [number?]
		) {
			started.push(Math.round(this.frequency.value));
			return originalStart.apply(this, args);
		};
	});
	await page.goto("/harness.html");
	await page.evaluate(async (code) => {
		await window.runExample(code);
	}, FRAGMENT_TONE_APP);

	await page.getByRole("button", { name: "A4" }).click();

	await expect(page.locator("#sound_area drafter-tone")).toHaveCount(1);
	await expect
		.poll(() =>
			page.evaluate(
				() =>
					(window as unknown as { startedOscillators: number[] })
						.startedOscillators,
			),
		)
		.toEqual([440]);
});

const REGRESSION_APP = `
from drafter import *

@dataclass
class State:
    clicks: int

@route
def index(state: State):
    return Page(state, [
        "Clicked " + str(state.clicks) + " times",
        Button("Click", add_click),
    ])

@route
def add_click(state: State):
    state.clicks += 1
    return index(state)

start_server(State(0))
`;

test.describe("debug panel regression tests", () => {
	test.use({ permissions: ["clipboard-read", "clipboard-write"] });

	test("Copy and Download export the tests generated from page visits", async ({
		page,
	}) => {
		await page.goto("/harness.html");
		await page.evaluate(async (code) => {
			await window.runExample(code);
		}, REGRESSION_APP);
		await page.getByRole("button", { name: "Click" }).click();
		await expect(page.locator("#drafter-root--")).toContainText(
			"Clicked 1 times",
		);

		await page.getByRole("tab", { name: "Tests" }).click();
		const expected = [
			"assert_equal(index(State(clicks=0)),",
			"assert_equal(add_click(State(clicks=0)),",
			"Page(State(clicks=1), [",
		];

		await page.locator(".drafter-debug-copy-tests-btn").click();
		await expect(
			page.locator(".drafter-debug-copy-tests-status"),
		).toHaveText("Copied!");
		const copied = await page.evaluate(() => navigator.clipboard.readText());
		for (const line of expected) {
			expect(copied).toContain(line);
		}

		const downloadPromise = page.waitForEvent("download");
		await page.locator(".drafter-debug-download-tests-btn").click();
		const download = await downloadPromise;
		expect(download.suggestedFilename()).toBe("drafter_tests.py");
		const stream = await download.createReadStream();
		const chunks: Buffer[] = [];
		for await (const chunk of stream) {
			chunks.push(chunk as Buffer);
		}
		// The OS clipboard may rewrite newlines (CRLF on Windows).
		expect(Buffer.concat(chunks).toString("utf-8")).toBe(
			copied.replace(/\r\n/g, "\n"),
		);
	});
});
