// Run each pyodide integration test file in its own Jest process.
//
// The pyodide suites cannot safely share a process: every file boots a fresh
// Pyodide runtime whose WASM memory is never reclaimed, and a runaway render
// loop left behind by one file (timer/animation examples keep scheduling work
// on the shared event loop) can keep executing while later files run,
// ballooning the heap until whichever file is active OOMs. A process per file
// makes both impossible. workerIdleMemoryLimit cannot catch this: it only
// recycles workers between files, and the runaway spikes mid-file.
//
// Usage: node scripts/run-integration-tests.mjs [substring ...]
// Any non-flag arguments filter the test files by substring match.

import { spawnSync } from "node:child_process";
import { readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const jsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const testDir = path.join(jsRoot, "src", "__tests__", "pyodide");

const filters = process.argv.slice(2).filter((arg) => !arg.startsWith("-"));

const files = readdirSync(testDir)
	.filter((name) => /\.test\.tsx?$/.test(name))
	.filter(
		(name) =>
			filters.length === 0 ||
			filters.some((filter) => name.includes(filter)),
	)
	.sort()
	.map((name) => path.join(testDir, name));

if (files.length === 0) {
	console.error(
		`No pyodide integration test files matched: ${filters.join(", ")}`,
	);
	process.exit(1);
}

const failed = [];
for (const file of files) {
	const label = path.basename(file);
	console.log(`\n=== ${label} ===`);
	const result = spawnSync(
		process.execPath,
		[
			"--max-old-space-size=6144",
			"--expose-gc",
			"--experimental-vm-modules",
			path.join(jsRoot, "node_modules", "jest", "bin", "jest.js"),
			"--selectProjects",
			"pyodide",
			"--runTestsByPath",
			file,
		],
		{ cwd: jsRoot, stdio: "inherit" },
	);
	if (result.status !== 0) {
		failed.push(label);
	}
}

console.log(
	`\n${files.length - failed.length}/${files.length} integration test files passed.`,
);
if (failed.length > 0) {
	console.log(`Failed: ${failed.join(", ")}`);
	process.exit(1);
}
