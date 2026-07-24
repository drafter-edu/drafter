/**
 * Pyodide parity tests derived from examples/examples.test.ts scenarios.
 *
 * The examples are partitioned across several thin *.test.ts files (one per
 * partition) instead of living in a single suite: each example run retains
 * memory in the shared Pyodide instance and the process eventually OOMs, so
 * the partitions rely on Jest's workerIdleMemoryLimit to recycle the worker
 * process between files. Keep EXAMPLES_PARITY_PARTITIONS in sync with the
 * number of pyodide.examples-parity.partN.test.ts files.
 */

import {
	describe,
	test,
	expect,
	afterEach,
	beforeAll,
	beforeEach,
} from "@jest/globals";
import { runStudentCode } from "../../pyodide.index";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "./pyodide-test-harness";
import * as fs from "fs";
import * as path from "path";

export const EXAMPLES_PARITY_PARTITIONS = 6;

function getAllFiles() {
	const examplesDir = "../examples/";
	const fileNames = fs.readdirSync(examplesDir);
	return fileNames
		.filter((fileName: string) => fileName.endsWith(".py"))
		.map((fileName: string) => {
			const filePath = path.join(examplesDir, fileName);
			const contents = fs.readFileSync(filePath, "utf-8");
			return { fileName, contents };
		});
}

const SKIP_EXAMPLES = [
	// Coupled two-file example: the harness writes a single main.py per run,
	// so the import can never resolve (and the _friend file is not an app).
	// Candidate for the Playwright examples suite with a real multi-file FS.
	"import_reloading.py",
	"import_reloading_friend.py",
	"file_upload.py",
	"file_upload_testing.py",
	"handle_image_upload.py",
	"pil_image.py",
	// Examples below require optional packages not loaded in the Pyodide test harness
	// (e.g., bakery, requests, pillow, matplotlib) or rely on host integration.
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
const INTENTIONAL_ERROR_EXAMPLES: string[] = [
	"error_non_string_page.py",
	"error_in_route.py",
	"state_conversion.py",
];

export function defineExamplesParitySuite(partitionIndex: number): void {
	if (
		partitionIndex < 0 ||
		partitionIndex >= EXAMPLES_PARITY_PARTITIONS ||
		!Number.isInteger(partitionIndex)
	) {
		throw new Error(
			`partitionIndex must be an integer in [0, ${EXAMPLES_PARITY_PARTITIONS})`,
		);
	}

	const examples = getAllFiles()
		.filter(
			({ fileName }) =>
				!SKIP_EXAMPLES.includes(fileName) &&
				!INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
		)
		.filter(
			(_, index) => index % EXAMPLES_PARITY_PARTITIONS === partitionIndex,
		);

	// The intentional-error examples are few; they all ride in partition 0.
	const errorExamples =
		partitionIndex === 0
			? getAllFiles().filter(({ fileName }) =>
					INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
				)
			: [];

	beforeAll(async () => {
		await setupPyodideWithLocalDrafter();
	});

	beforeEach(async () => {
		await resetPyodideDrafterRuntime();
	});

	afterEach(() => {
		// The examples share one Pyodide instance in one process; nudge the
		// collector between tests to reclaim what actually is garbage.
		// Requires --expose-gc (see test:integration).
		(globalThis as { gc?: () => void }).gc?.();
	});

	if (examples.length > 0) {
		describe.each(examples)(
			"Pyodide Example Test: %s",
			({ fileName, contents }: { fileName: string; contents: string }) => {
				test(`can run example ${fileName}`, async () => {
					await runStudentCode({ code: contents, presentErrors: false });
					const drafterBody = document.querySelector("#drafter-root--");
					expect(drafterBody).not.toBeNull();
					const debugPanel =
						drafterBody?.querySelector(".drafter-debug--");
					expect(debugPanel).not.toBeNull();
					const formBody = drafterBody?.querySelector(".drafter-form--");
					expect(formBody?.textContent).not.toMatch(/error/i);
				});
			},
		);
	}

	if (errorExamples.length > 0) {
		describe.each(errorExamples)(
			"Pyodide Example Test (Expected Errors): %s",
			({ fileName, contents }: { fileName: string; contents: string }) => {
				test(`can run example with expected errors ${fileName}`, async () => {
					await runStudentCode({ code: contents, presentErrors: true });
					const drafterBody = document.querySelector("#drafter-root--");
					expect(drafterBody).not.toBeNull();
					const formBody = drafterBody?.querySelector(".drafter-form--");
					expect(formBody?.textContent).toMatch(/error/i);
				});
			},
		);
	}
}
