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
