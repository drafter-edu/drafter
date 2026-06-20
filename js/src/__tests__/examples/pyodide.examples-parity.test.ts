/**
 * Pyodide parity tests derived from examples/examples.test.ts scenarios.
 */

import { describe, test, expect, beforeAll, beforeEach } from "@jest/globals";
import { runStudentCode } from "../../pyodide.index";
import {
	resetPyodideDrafterRuntime,
	setupPyodideWithLocalDrafter,
} from "../pyodide-test-harness";
import * as fs from "fs";
import * as path from "path";

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
];
const INTENTIONAL_ERROR_EXAMPLES: string[] = [
	"error_non_string_page.py",
	"error_in_route.py",
	"state_conversion.py",
];

const examples = getAllFiles().filter(
	({ fileName }) =>
		!SKIP_EXAMPLES.includes(fileName) &&
		!INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);

const errorExamples = getAllFiles().filter(({ fileName }) =>
	INTENTIONAL_ERROR_EXAMPLES.includes(fileName),
);

beforeAll(async () => {
	await setupPyodideWithLocalDrafter();
});

beforeEach(async () => {
	await resetPyodideDrafterRuntime();
});

describe.each(examples)(
	"Pyodide Example Test: %s",
	({ fileName, contents }: { fileName: string; contents: string }) => {
		test(`can run example ${fileName}`, async () => {
			await runStudentCode({ code: contents, presentErrors: false });
			const drafterBody = document.querySelector("#drafter-root--");
			expect(drafterBody).not.toBeNull();
			const debugPanel = drafterBody?.querySelector(".drafter-debug--");
			expect(debugPanel).not.toBeNull();
			const formBody = drafterBody?.querySelector(".drafter-form--");
			expect(formBody?.textContent).not.toMatch(/error/i);
		});
	},
);

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
