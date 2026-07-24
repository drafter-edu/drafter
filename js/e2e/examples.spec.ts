// Suite A of JS_TESTING_PLAN.md: run every runnable example in a real
// browser. Batches share one page (one Pyodide boot); each batch gets a
// fresh page so memory is reclaimed by the OS between batches. This replaces
// the jest examples-parity suite's role as the broad "does every example
// run" net (the jest partitions remain until this suite is proven in CI).

import { test, expect } from "playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

declare global {
	interface Window {
		bootRuntime: () => Promise<void>;
		runExample: (code: string, presentErrors?: boolean) => Promise<void>;
	}
}

const EXAMPLES_DIR = path.resolve(__dirname, "..", "..", "examples");
const BATCH_SIZE = 8;

// Kept in sync with js/src/__tests__/pyodide/examples-parity-suite.ts.
// Several of these (file uploads, plotting, PIL) are browser-feasible and
// should be un-skipped as dedicated e2e feature specs are added.
const SKIP_EXAMPLES = [
	"import_reloading.py",
	"import_reloading_friend.py",
	"file_upload.py",
	"file_upload_testing.py",
	"handle_image_upload.py",
	"pil_image.py",
	"bulleted_list_weirdness.py",
	"button_arguments.py",
	"calculator_features.py",
	"calculator_two_page.py",
	"deployed_full_width.py",
	"dict_state.py",
	"error_link.py",
	"error_missing_page.py",
	"explicit_routes.py",
	"fetch_weather.py",
	"file_handling.py",
	"file_handling_external.py",
	"fun_style.py",
	"plotting.py",
	"plotting_seaborn.py",
	"simplest.py",
	"simple_image.py",
	"simple_ring.py",
	"successful_link.py",
	"table.py",
	"todo_list.py",
	"unittest_full_state.py",
	"weird_plot.py",
	"complex_state.py",
	"no_start.py",
];
const INTENTIONAL_ERROR_EXAMPLES = [
	"error_non_string_page.py",
	"error_in_route.py",
	"state_conversion.py",
];

type Example = { fileName: string; contents: string };

function getAllExamples(): Example[] {
	return fs
		.readdirSync(EXAMPLES_DIR)
		.filter((fileName) => fileName.endsWith(".py"))
		.map((fileName) => ({
			fileName,
			contents: fs.readFileSync(
				path.join(EXAMPLES_DIR, fileName),
				"utf-8",
			),
		}));
}

const runnable = getAllExamples().filter(
	({ fileName }) =>
		!SKIP_EXAMPLES.includes(fileName) &&
		!INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);
const errorExamples = getAllExamples().filter(({ fileName }) =>
	INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);

const batches: Example[][] = [];
for (let i = 0; i < runnable.length; i += BATCH_SIZE) {
	batches.push(runnable.slice(i, i + BATCH_SIZE));
}

// Runs one example in the already-booted page and reports what rendered.
async function runInPage(
	page: import("playwright/test").Page,
	example: Example,
	presentErrors: boolean,
): Promise<string | null> {
	try {
		return await page.evaluate(
			async ({ code, presentErrors }) => {
				await window.runExample(code, presentErrors);
				const root = document.querySelector("#drafter-root--");
				if (!root) {
					return "missing #drafter-root--";
				}
				const debugPanel = root.querySelector(".drafter-debug--");
				const formBody = root.querySelector(".drafter-form--");
				const formText = formBody?.textContent ?? "";
				if (!presentErrors) {
					if (!debugPanel) {
						return "missing .drafter-debug--";
					}
					if (/error/i.test(formText)) {
						return `form contains error text: ${formText.slice(0, 300)}`;
					}
				} else if (!/error/i.test(formText)) {
					return `expected error text, got: ${formText.slice(0, 300)}`;
				}
				return null;
			},
			{ code: example.contents, presentErrors },
		);
	} catch (error) {
		return `threw: ${String(error).slice(0, 500)}`;
	}
}

for (const [index, batch] of batches.entries()) {
	const names = batch.map((example) => example.fileName);
	test(`examples batch ${index + 1}/${batches.length}: ${names.join(", ")}`, async ({
		page,
	}) => {
		await page.goto("/harness.html");
		await page.evaluate(() => window.bootRuntime());

		const failures: string[] = [];
		for (const example of batch) {
			const problem = await runInPage(page, example, false);
			if (problem !== null) {
				failures.push(`${example.fileName}: ${problem}`);
			}
		}
		expect(failures).toEqual([]);
	});
}

test("intentional-error examples render an error page", async ({ page }) => {
	await page.goto("/harness.html");
	await page.evaluate(() => window.bootRuntime());

	const failures: string[] = [];
	for (const example of errorExamples) {
		const problem = await runInPage(page, example, true);
		if (problem !== null) {
			failures.push(`${example.fileName}: ${problem}`);
		}
	}
	expect(failures).toEqual([]);
});
