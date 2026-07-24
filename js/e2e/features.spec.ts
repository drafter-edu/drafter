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
		await expect(
			page.locator(".drafter-geolocation-coords"),
		).toContainText("39.680000, -75.750000");
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
