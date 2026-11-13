// Slide mode on the documentation site (docs/assets/drafter-slides.js): the
// header's Present button turns a page into a deck. Everything it promises is
// about real layout (what fits on a screen, what happens when the window is
// zoomed or resized), so it can only be checked in a real browser.
//
// The fixture page reproduces the structure mkdocs-material gives a docs page
// and loads the real slide-mode assets. No Python runtime is involved.

import { test, expect, type Page } from "playwright/test";

const FIXTURE = "/docs-slides.html";

// Slides the fixture should produce, in order. The opening sections (Goal,
// Before you start) join the title slide, so only the Goal heading used later
// in the page is a slide. The sections at the bottom of the fixture (In more
// depth, Related components, External links, and the four-link block) must
// not appear; Next steps must.
const SLIDE_TITLES = [
	"Fixture page",
	"The smallest version",
	"The theme names",
	"Steps",
	"A long program",
	"Try it",
	"Goal",
	"Next steps",
];

// A laptop, a projector at full screen, the laptop zoomed to 150% and 200%
// (browser zoom shrinks the viewport in CSS pixels), a short wide window,
// and a phone.
const WINDOWS = [
	{ name: "laptop", width: 1440, height: 810 },
	{ name: "full screen", width: 1920, height: 1080 },
	{ name: "zoomed 150%", width: 960, height: 540 },
	{ name: "zoomed 200%", width: 720, height: 405 },
	{ name: "short window", width: 1280, height: 480 },
	{ name: "phone", width: 400, height: 800 },
];

interface Snapshot {
	label: string;
	base: number;
	fit: number;
	overflowing: boolean;
	atBottom: boolean;
	more: boolean;
	stageBottom: number;
	barTop: number;
	lowestBlock: number;
	text: string;
	rows: string[];
	items: string[];
	code: { top: number; hiddenBelow: number } | null;
}

async function snapshot(page: Page): Promise<Snapshot> {
	return page.evaluate(() => {
		const stage = document.querySelector<HTMLElement>("article.md-content__inner")!;
		const bar = document.querySelector<HTMLElement>(".drafter-slides__bar")!;
		const shown = (el: Element) => el.getClientRects().length > 0;
		const blocks = Array.from(
			stage.querySelectorAll<HTMLElement>(".drafter-slides__block--on"),
		);
		const base = parseFloat(
			getComputedStyle(stage).getPropertyValue("--drafter-slides-base"),
		);
		const zoom = parseFloat(stage.style.getPropertyValue("--drafter-slides-zoom"));
		const capped = blocks
			.flatMap((el) => Array.from(el.querySelectorAll<HTMLElement>("pre > code")))
			.find((el) => el.style.maxHeight !== "");
		return {
			label: document.querySelector(".drafter-slides__count")!.textContent ?? "",
			base,
			fit: zoom / base,
			overflowing: stage.scrollHeight > stage.clientHeight + 1,
			atBottom: stage.scrollHeight - stage.clientHeight - stage.scrollTop <= 2,
			more: !document.querySelector<HTMLElement>(".drafter-slides__more")!.hidden,
			stageBottom: stage.getBoundingClientRect().bottom,
			barTop: bar.getBoundingClientRect().top,
			lowestBlock: Math.max(0, ...blocks.map((el) => el.getBoundingClientRect().bottom)),
			text: blocks.map((el) => el.innerText).join("\n"),
			rows: Array.from(stage.querySelectorAll("tbody tr"))
				.filter(shown)
				.map((row) => row.firstElementChild!.textContent ?? ""),
			items: Array.from(stage.querySelectorAll("#items > li"))
				.filter(shown)
				.map((item) => (item.textContent ?? "").split(":")[0]),
			code: capped
				? {
						top: capped.scrollTop,
						hiddenBelow: capped.scrollHeight - capped.clientHeight - capped.scrollTop,
					}
				: null,
		};
	});
}

async function present(page: Page): Promise<void> {
	await page.goto(FIXTURE);
	await page.locator(".drafter-slides-open").click();
	await expect(page.locator("html")).toHaveClass(/drafter-slides/);
}

// Press Next until the end card, handing every stop to `visit`.
async function walk(page: Page, visit: (stop: Snapshot) => void): Promise<void> {
	for (let presses = 0; presses < 300; presses++) {
		const stop = await snapshot(page);
		visit(stop);
		if (stop.label.startsWith("End of page")) {
			return;
		}
		await page.keyboard.press("ArrowRight");
	}
	throw new Error("the deck never reached its end card");
}

async function openSlide(page: Page, title: string): Promise<void> {
	await page.locator(".drafter-slides__count").click();
	await page.locator(".drafter-slides__outline button", { hasText: title }).click();
}

for (const size of WINDOWS) {
	test(`nothing is cut off or lost at ${size.name} size (${size.width}x${size.height})`, async ({
		page,
	}) => {
		await page.setViewportSize({ width: size.width, height: size.height });
		await present(page);

		const rows: string[] = [];
		const items: string[] = [];
		const titlesSeen: string[] = [];
		await walk(page, (stop) => {
			// The stage always ends where the control bar begins.
			expect(stop.stageBottom).toBeLessThanOrEqual(stop.barTop + 1);
			// Shrinking is bounded.
			expect(stop.fit).toBeGreaterThanOrEqual(0.65 - 0.001);
			expect(stop.fit).toBeLessThanOrEqual(1.001);
			if (stop.overflowing) {
				// A slide that cannot fit says so until Next has paged to its end.
				expect(stop.more || stop.atBottom).toBe(true);
			} else {
				expect(stop.lowestBlock).toBeLessThanOrEqual(stop.stageBottom + 1);
			}
			expect(stop.text).not.toContain("CLOSING-SECTION");
			for (const row of stop.rows) {
				if (!rows.includes(row)) rows.push(row);
			}
			for (const item of stop.items) {
				if (!items.includes(item)) items.push(item);
			}
			const title = SLIDE_TITLES.find((name) => stop.text.startsWith(name));
			if (title && titlesSeen[titlesSeen.length - 1] !== title) titlesSeen.push(title);
		});

		// Every row and list item was shown, in order, and every section
		// except the closing ones became a slide.
		expect(rows).toEqual(Array.from({ length: 20 }, (_, i) => `theme-${i + 1}`));
		expect(items).toEqual(Array.from({ length: 12 }, (_, i) => `Step ${i + 1}`));
		expect(titlesSeen).toEqual(SLIDE_TITLES.slice(1));
	});
}

test("the opening sections join the title slide", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);

	const first = await snapshot(page);
	expect(first.label).toBe("Slide 1 of 8");
	expect(first.text).toContain("Fixture page");
	expect(first.text).toContain("OPENING-SECTION one");
	expect(first.text).toContain("OPENING-SECTION two");
	// Their text shows without their headings, which are not slides.
	await expect(page.locator("#goal")).toBeHidden();
	await expect(page.locator("#before-you-start")).toBeHidden();
	await page.keyboard.press("ArrowRight");
	expect((await snapshot(page)).text).toMatch(/^The smallest version/);

	// A link to a folded heading still lands on the slide that shows its text.
	await page.evaluate(() => {
		window.location.hash = "#before-you-start";
	});
	await expect.poll(async () => (await snapshot(page)).label).toBe("Slide 1 of 8");

	// The same heading later in the page starts a slide like any other.
	await openSlide(page, "Goal");
	const late = await snapshot(page);
	expect(late.label).toBe("Slide 7 of 8");
	expect(late.text).toContain("An opening heading used later");
	await expect(page.locator("#late-goal")).toBeVisible();
});

test("a program sits beside its running demo on a wide screen", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);
	await openSlide(page, "The smallest version");

	const program = await page.locator("#short-program").boundingBox();
	const demo = await page.locator("#demo").boundingBox();
	expect(program).not.toBeNull();
	expect(demo).not.toBeNull();
	expect(demo!.x).toBeGreaterThanOrEqual(program!.x + program!.width);
	expect(Math.abs(demo!.y - program!.y)).toBeLessThan(12);
});

test("a program too long for the screen scrolls in its own box, and Next pages through it", async ({
	page,
}) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);
	await openSlide(page, "A long program");

	let stop = await snapshot(page);
	expect(stop.label).toBe("Slide 5 of 8");
	expect(stop.overflowing).toBe(false);
	expect(stop.code).not.toBeNull();
	expect(stop.code!.hiddenBelow).toBeGreaterThan(2);
	expect(stop.more).toBe(true);

	await page.keyboard.press("ArrowRight");
	stop = await snapshot(page);
	expect(stop.label).toBe("Slide 5 of 8");
	expect(stop.code!.top).toBeGreaterThan(0);

	// Keep going: the slide only changes once the last line has been shown.
	for (let presses = 0; presses < 40 && stop.label === "Slide 5 of 8"; presses++) {
		const hiddenBefore = stop.code!.hiddenBelow;
		await page.keyboard.press("ArrowRight");
		stop = await snapshot(page);
		if (stop.label !== "Slide 5 of 8") {
			expect(hiddenBefore).toBeLessThanOrEqual(2);
		}
	}
	expect(stop.label).toBe("Slide 6 of 8");
});

test("resizing the window lays the deck out again on the same content", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);
	await openSlide(page, "The theme names");
	const before = await snapshot(page);
	expect(before.base).toBe(1.6);

	// What zooming the browser to 200% does to the viewport.
	await page.setViewportSize({ width: 720, height: 405 });
	await expect
		.poll(async () => {
			const stop = await snapshot(page);
			return stop.base === 1.3 && stop.fit <= 1.001;
		})
		.toBe(true);

	const after = await snapshot(page);
	expect(after.label).toMatch(/^Slide 3 of 8/);
	expect(after.rows[0]).toBe("theme-1");
	expect(after.overflowing).toBe(false);
	expect(after.lowestBlock).toBeLessThanOrEqual(after.stageBottom + 1);
	// Less room per slide, so the table takes more slides than before.
	expect(after.rows.length).toBeLessThan(before.rows.length);
});

test("the deck opens at the section being read and Exit returns there", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await page.goto(FIXTURE);
	await page.evaluate(() => document.getElementById("steps")!.scrollIntoView());
	await page.locator(".drafter-slides-open").click();
	expect((await snapshot(page)).label).toMatch(/^Slide 4 of 8/);

	await openSlide(page, "Goal");
	await page.keyboard.press("Escape");
	await expect(page.locator("html")).not.toHaveClass(/drafter-slides/);
	const goal = await page.locator("#late-goal").boundingBox();
	expect(goal!.y).toBeGreaterThanOrEqual(-1);
	expect(goal!.y).toBeLessThan(200);
});

test("leaving slide mode puts the page back exactly as it was", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await page.goto(FIXTURE);
	const before = await page.locator("article").innerHTML();
	await page.locator(".drafter-slides-open").click();
	await walk(page, () => {});
	await page.keyboard.press("Escape");

	await expect(page.locator(".drafter-slides__bar")).toBeHidden();
	expect(await page.locator("article").innerHTML()).toBe(before);
});

test("the end card opens the next page, still in slide mode", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);
	await page.keyboard.press("End");
	await expect(page.locator(".drafter-slides__end")).toContainText("Next: Later page");

	await page.keyboard.press("ArrowRight");
	await page.waitForURL(/page=next/);
	await expect(page.locator("html")).toHaveClass(/drafter-slides/);
	expect((await snapshot(page)).label).toBe("Slide 1 of 8");
});

test("typing in a field on a slide does not turn the slide", async ({ page }) => {
	await page.setViewportSize({ width: 1440, height: 810 });
	await present(page);
	await openSlide(page, "Try it");

	await page.locator("#field").click();
	await page.keyboard.type("a b");
	await page.keyboard.press("ArrowRight");
	await page.keyboard.press("PageDown");
	await expect(page.locator("#field")).toHaveValue("a b");
	expect((await snapshot(page)).label).toBe("Slide 6 of 8");
});
