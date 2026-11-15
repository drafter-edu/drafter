import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import { setSystemErrorSink, type ErrorTelemetryRecord } from "../bridge/engine";
import { closeDialog } from "../dialogs";
import {
	addMockPackages,
	enqueueRuntimeWork,
	installMissingImports,
	runStudentCode,
	setupEnvironment,
	toVirtualStudentPath,
} from "../pyodide.index";

function deferred<T>(): {
	promise: Promise<T>;
	resolve: (value: T) => void;
	reject: (reason?: unknown) => void;
} {
	let resolve!: (value: T) => void;
	let reject!: (reason?: unknown) => void;
	const promise = new Promise<T>((res, rej) => {
		resolve = res;
		reject = rej;
	});
	return { promise, resolve, reject };
}

function flushMicrotasks(times = 3): Promise<void> {
	let chain = Promise.resolve();
	for (let i = 0; i < times; i += 1) {
		chain = chain.then(() => {});
	}
	return chain;
}

// ---------------------------------------------------------------------------
// enqueueRuntimeWork (the promise-chain mutex around the shared interpreter)
// ---------------------------------------------------------------------------

describe("enqueueRuntimeWork", () => {
	test("propagates the task's resolved value", async () => {
		await expect(enqueueRuntimeWork(async () => 42)).resolves.toBe(42);
		await expect(
			enqueueRuntimeWork(() => Promise.resolve("done")),
		).resolves.toBe("done");
	});

	test("serializes tasks strictly FIFO: B does not start before A settles", async () => {
		const log: string[] = [];
		const gate = deferred<void>();

		const first = enqueueRuntimeWork(async () => {
			log.push("A start");
			await gate.promise;
			log.push("A end");
		});
		const second = enqueueRuntimeWork(async () => {
			log.push("B start");
		});

		// Give B every chance to (incorrectly) start while A is blocked.
		await flushMicrotasks(10);
		expect(log).toEqual(["A start"]);

		gate.resolve();
		await first;
		await second;
		expect(log).toEqual(["A start", "A end", "B start"]);
	});

	test("a rejecting task propagates its rejection to the caller", async () => {
		await expect(
			enqueueRuntimeWork(() => Promise.reject(new Error("boom"))),
		).rejects.toThrow("boom");
	});

	test("a rejecting task does not poison the chain", async () => {
		const failing = enqueueRuntimeWork(() =>
			Promise.reject(new Error("first fails")),
		);
		const after = enqueueRuntimeWork(async () => "still runs");

		await expect(failing).rejects.toThrow("first fails");
		await expect(after).resolves.toBe("still runs");
	});

	test("a later task waits for a pending task even when it will reject", async () => {
		const log: string[] = [];
		const gate = deferred<void>();

		const doomed = enqueueRuntimeWork(async () => {
			log.push("A start");
			await gate.promise;
			throw new Error("A dies");
		});
		const follower = enqueueRuntimeWork(async () => {
			log.push("B start");
			return "B ok";
		});

		await flushMicrotasks(10);
		expect(log).toEqual(["A start"]);

		gate.reject(new Error("A dies"));
		await expect(doomed).rejects.toThrow("A dies");
		await expect(follower).resolves.toBe("B ok");
		expect(log).toEqual(["A start", "B start"]);
	});

	test("many tasks run in enqueue order", async () => {
		const order: number[] = [];
		const tasks = [0, 1, 2, 3, 4].map((index) =>
			enqueueRuntimeWork(async () => {
				// A descending delay would reveal any parallelism: without the
				// chain, task 4 (0ms) would finish before task 0 (8ms).
				await new Promise((resolve) =>
					setTimeout(resolve, (4 - index) * 2),
				);
				order.push(index);
				return index;
			}),
		);
		await expect(Promise.all(tasks)).resolves.toEqual([0, 1, 2, 3, 4]);
		expect(order).toEqual([0, 1, 2, 3, 4]);
	});
});

// ---------------------------------------------------------------------------
// toVirtualStudentPath
// ---------------------------------------------------------------------------

describe("toVirtualStudentPath", () => {
	test.each([
		[undefined, "/main.py"],
		["", "/main.py"],
		["   ", "/main.py"],
		["main.py", "/main.py"],
		["/main.py", "/main.py"],
		["folder/file.py", "/folder/file.py"],
		["/already/absolute.py", "/already/absolute.py"],
		["  padded.py  ", "/padded.py"],
		// Instance ids and student names may contain special characters;
		// they are preserved verbatim (sanitization happens elsewhere).
		["my file (v2)!.py", "/my file (v2)!.py"],
		["instances/demo-1/üñïçødé.py", "/instances/demo-1/üñïçødé.py"],
		["weird\\backslash.py", "/weird\\backslash.py"],
	])("maps %p to %p", (input, expected) => {
		expect(toVirtualStudentPath(input as string | undefined)).toBe(
			expected,
		);
	});
});

// ---------------------------------------------------------------------------
// setupEnvironment: explicit package-spec dedup + automatic loading
// ---------------------------------------------------------------------------

type AnyWindow = Window & {
	pyodide?: unknown;
	micropip?: unknown;
};

describe("setupEnvironment package handling", () => {
	let install: jest.Mock<(pkg: string) => Promise<void>>;
	let loadPackagesFromImports: jest.Mock<(code: string) => Promise<string[]>>;
	let loadPackage: jest.Mock<(pkg: string) => Promise<void>>;

	beforeEach(() => {
		install = jest.fn(async (_pkg: string) => {});
		loadPackagesFromImports = jest.fn(async (_code: string) => []);
		loadPackage = jest.fn(async (_pkg: string) => {});
		(window as AnyWindow).pyodide = { loadPackagesFromImports, loadPackage };
		(window as AnyWindow).micropip = { install };
	});

	afterEach(() => {
		delete (window as AnyWindow).pyodide;
		delete (window as AnyWindow).micropip;
	});

	// NOTE: requestedPackageSpecs is a module-level Set with no reset hook,
	// so these tests use unique package names per test and verify idempotence
	// rather than relying on a clean slate.

	test("installs each explicit package once and skips already-requested specs", async () => {
		await setupEnvironment({
			code: "",
			explicitPackageList: ["dedup-a", "dedup-b"],
		});
		expect(install.mock.calls.map((call) => call[0])).toEqual([
			"dedup-a",
			"dedup-b",
		]);

		install.mockClear();
		await setupEnvironment({
			code: "",
			explicitPackageList: ["dedup-a", "dedup-c"],
		});
		expect(install.mock.calls.map((call) => call[0])).toEqual(["dedup-c"]);
	});

	test("duplicates within a single explicit list install only once", async () => {
		await setupEnvironment({
			code: "",
			explicitPackageList: ["dup-x", "dup-x", "dup-x"],
		});
		expect(install).toHaveBeenCalledTimes(1);
		expect(install).toHaveBeenCalledWith("dup-x");
	});

	test("a failed install is not marked as requested, so a retry re-installs", async () => {
		install.mockRejectedValueOnce(new Error("network down"));
		await expect(
			setupEnvironment({
				code: "",
				explicitPackageList: ["retry-pkg"],
			}),
		).rejects.toThrow();

		install.mockClear();
		await setupEnvironment({
			code: "",
			explicitPackageList: ["retry-pkg"],
		});
		expect(install).toHaveBeenCalledTimes(1);
		expect(install).toHaveBeenCalledWith("retry-pkg");
	});

	test("loadPackagesAutomatically delegates to pyodide.loadPackagesFromImports", async () => {
		await setupEnvironment({
			code: "import math",
			loadPackagesAutomatically: true,
		});
		expect(loadPackagesFromImports).toHaveBeenCalledTimes(1);
		expect(loadPackagesFromImports).toHaveBeenCalledWith("import math");
		expect(install).not.toHaveBeenCalled();
		expect(loadPackage).not.toHaveBeenCalled();
	});

	test("MatPlotLibPlot usage in code loads matplotlib", async () => {
		await setupEnvironment({
			code: "from drafter import *\nMatPlotLibPlot()",
			loadPackagesAutomatically: true,
		});
		expect(loadPackage).toHaveBeenCalledTimes(1);
		expect(loadPackage).toHaveBeenCalledWith("matplotlib");
	});

	test("MatPlotLibPlot is not loaded without automatic package loading", async () => {
		await setupEnvironment({
			code: "MatPlotLibPlot()",
		});
		expect(loadPackage).not.toHaveBeenCalled();
	});

	test("automatic loading and explicit packages both apply when both are set", async () => {
		await setupEnvironment({
			code: "import math",
			loadPackagesAutomatically: true,
			explicitPackageList: ["combined-pkg"],
		});
		expect(loadPackagesFromImports).toHaveBeenCalledTimes(1);
		expect(loadPackagesFromImports).toHaveBeenCalledWith("import math");
		expect(install).toHaveBeenCalledTimes(1);
		expect(install).toHaveBeenCalledWith("combined-pkg");
	});

	test("does nothing when neither package option is set", async () => {
		await setupEnvironment({ code: "print('hi')" });
		expect(install).not.toHaveBeenCalled();
		expect(loadPackagesFromImports).not.toHaveBeenCalled();
	});
});

// ---------------------------------------------------------------------------
// Automatic installs for imports Pyodide's own loading does not cover
// ---------------------------------------------------------------------------

describe("automatic installs for missing imports", () => {
	let install: jest.Mock<(pkg: string) => Promise<void>>;
	let runPythonAsync: jest.Mock<(code: string, options?: unknown) => Promise<string>>;
	let destroyed: number;

	/** Make Python report these names as the program's missing imports. */
	function pythonReportsMissing(names: string[]) {
		runPythonAsync.mockImplementation(async () => JSON.stringify(names));
	}

	beforeEach(() => {
		destroyed = 0;
		install = jest.fn(async (_pkg: string) => {});
		runPythonAsync = jest.fn(async () => "[]");
		(window as AnyWindow).pyodide = {
			loadPackagesFromImports: jest.fn(async () => []),
			loadPackage: jest.fn(async () => {}),
			runPythonAsync,
			toPy: (value: unknown) => ({
				value,
				destroy: () => {
					destroyed += 1;
				},
			}),
		};
		(window as AnyWindow).micropip = { install };
	});

	afterEach(() => {
		delete (window as AnyWindow).pyodide;
		delete (window as AnyWindow).micropip;
	});

	test("installs each import that nothing else provides", async () => {
		pythonReportsMissing(["auto-seaborn", "auto-wordfreq"]);

		await setupEnvironment({
			code: "import seaborn\nimport wordfreq",
			loadPackagesAutomatically: true,
		});

		expect(install.mock.calls.map((call) => call[0])).toEqual([
			"auto-seaborn",
			"auto-wordfreq",
		]);
	});

	test("hands the program's source to Python and cleans up afterwards", async () => {
		await setupEnvironment({
			code: "import seaborn",
			loadPackagesAutomatically: true,
		});

		const [snippet, options] = runPythonAsync.mock.calls[0] as [
			string,
			{ globals: { value: Record<string, string> } },
		];
		// The helper's Python travels with the bundle: the browser's own
		// drafter may be a published version without it (the development
		// server and the docs demos install drafter from PyPI).
		expect(snippet).not.toContain("from drafter");
		expect(snippet).toContain("exec(__drafter_import_helpers");
		expect(options.globals.value.__drafter_import_helpers).toContain(
			"def find_missing_imports(",
		);
		expect(options.globals.value.__drafter_import_source).toBe(
			"import seaborn",
		);
		expect(destroyed).toBe(1);
	});

	test("a library that cannot be installed does not stop the program", async () => {
		pythonReportsMissing(["auto-typo-pkg", "auto-fine-pkg"]);
		install.mockImplementation(async (pkg: string) => {
			if (pkg === "auto-typo-pkg") {
				throw new Error("Can't find a pure Python 3 wheel");
			}
		});

		await expect(
			setupEnvironment({ code: "", loadPackagesAutomatically: true }),
		).resolves.toBeUndefined();

		expect(install).toHaveBeenCalledWith("auto-fine-pkg");
	});

	test("a failed install is not retried on the next run", async () => {
		pythonReportsMissing(["auto-never-installs"]);
		install.mockRejectedValue(new Error("no such package"));

		await setupEnvironment({ code: "", loadPackagesAutomatically: true });
		await setupEnvironment({ code: "", loadPackagesAutomatically: true });

		expect(install).toHaveBeenCalledTimes(1);
	});

	test("an installed library is not requested again", async () => {
		pythonReportsMissing(["auto-installed-once"]);

		await setupEnvironment({ code: "", loadPackagesAutomatically: true });
		await setupEnvironment({ code: "", loadPackagesAutomatically: true });

		expect(install).toHaveBeenCalledTimes(1);
	});

	test("an explicitly listed library is not installed twice", async () => {
		pythonReportsMissing(["auto-and-explicit"]);

		await setupEnvironment({
			code: "",
			loadPackagesAutomatically: true,
			explicitPackageList: ["auto-and-explicit"],
		});

		expect(install).toHaveBeenCalledTimes(1);
	});

	test("nothing is installed when the check itself cannot run", async () => {
		// For example: a Pyodide whose interpreter rejects the check.
		runPythonAsync.mockRejectedValue(new Error("PythonError"));

		await expect(
			setupEnvironment({ code: "import x", loadPackagesAutomatically: true }),
		).resolves.toBeUndefined();

		expect(install).not.toHaveBeenCalled();
		expect(destroyed).toBe(1);
	});

	test("turning automatic loading off turns this off too", async () => {
		pythonReportsMissing(["auto-should-not-install"]);

		await setupEnvironment({ code: "import x" });

		expect(runPythonAsync).not.toHaveBeenCalled();
		expect(install).not.toHaveBeenCalled();
	});

	test("installMissingImports reports what it installed", async () => {
		pythonReportsMissing(["auto-reported"]);

		expect(await installMissingImports("import reported")).toEqual([
			"auto-reported",
		]);
	});
});

// ---------------------------------------------------------------------------
// Saying so when an import was filled from PyPI
// ---------------------------------------------------------------------------

describe("imports filled from PyPI", () => {
	// A deployed site whose `helpers.py` is missing used to install the
	// unrelated PyPI package `helpers` without a word, and the student then
	// saw that package's error. Each test uses its own library name because
	// the page-long record of what was installed has no reset hook.

	const WARNING_ID = "runtime.import_installed_from_pypi";

	let install: jest.Mock<(spec: string | string[]) => Promise<void>>;
	let missingImports: string[];
	let importedModules: string[];
	let studentCodeError: Error | null;
	let loadedPackages: Record<string, string>;
	let received: ErrorTelemetryRecord[];

	beforeEach(() => {
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		missingImports = [];
		importedModules = [];
		studentCodeError = null;
		loadedPackages = {};
		received = [];
		setSystemErrorSink((event) => received.push(event));
		jest.spyOn(console, "warn").mockImplementation(() => {});
		jest.spyOn(console, "error").mockImplementation(() => {});
		install = jest.fn(async (spec: string | string[]) => {
			// Like micropip, record where each library came from.
			if (typeof spec === "string" && !(spec in loadedPackages)) {
				loadedPackages[spec] = "pypi";
			}
		});
		(window as AnyWindow).micropip = { install };
		(window as AnyWindow).pyodide = {
			loadedPackages,
			loadPackagesFromImports: jest.fn(async () => []),
			loadPackage: jest.fn(async () => {}),
			toPy: (value: unknown) => ({ value, destroy: () => {} }),
			FS: { writeFile: () => {}, mkdirTree: () => {} },
			runPythonAsync: jest.fn(async (code: string) => {
				if (code.includes('_helpers["find_missing_imports"]')) {
					return JSON.stringify(missingImports);
				}
				if (code.includes('_helpers["find_imported_modules"]')) {
					return JSON.stringify(importedModules);
				}
				if (code.startsWith("import ") && studentCodeError) {
					throw studentCodeError;
				}
				// Package metadata questions, and the no-op that absorbs a
				// pending interrupt.
				return "[]";
			}),
		};
	});

	afterEach(() => {
		closeDialog("runtime.student_code_failed");
		setSystemErrorSink(null);
		jest.restoreAllMocks();
		delete (window as AnyWindow).pyodide;
		delete (window as AnyWindow).micropip;
		document.body.innerHTML = "";
	});

	/** Set up and run a program that imports `name`, as an instance does. */
	async function runProgramImporting(
		name: string,
		options: { explicitPackageList?: string[]; packageIndexes?: string[] } = {},
	): Promise<void> {
		const code = `import ${name}`;
		importedModules = [name];
		await setupEnvironment({
			code,
			loadPackagesAutomatically: true,
			...options,
		});
		await runStudentCode({ code });
	}

	function warnings(): ErrorTelemetryRecord[] {
		return received.filter((event) => event.error.id === WARNING_ID);
	}

	test("the debug panel is told which library was installed", async () => {
		missingImports = ["pypi_helpers"];

		await runProgramImporting("pypi_helpers");

		expect(install).toHaveBeenCalledWith("pypi_helpers");
		expect(warnings()).toHaveLength(1);
		const envelope = warnings()[0].error;
		expect(envelope.severity).toBe("warning");
		expect(envelope.friendly_message).toContain(
			"Drafter installed the library named pypi_helpers from PyPI",
		);
		expect(envelope.friendly_message).toContain("no pypi_helpers.py");
		// Not tied to one page, so the panel keeps showing it.
		expect(envelope.context.request_id).toBeNull();
		// A warning goes to the debug panel only: the site keeps running.
		expect(document.querySelector(".drafter-dialog")).toBeNull();
		expect(document.querySelector(".drafter-system-error")).toBeNull();
	});

	test("the warning is given again on each run, without installing again", async () => {
		missingImports = ["pypi_rerun"];
		await runProgramImporting("pypi_rerun");
		// From now on the library is installed, so nothing is missing.
		missingImports = [];
		received = [];

		await runProgramImporting("pypi_rerun");

		expect(install).toHaveBeenCalledTimes(1);
		expect(warnings()).toHaveLength(1);
	});

	test("the warning stops once the program no longer imports the library", async () => {
		missingImports = ["pypi_dropped"];
		await runProgramImporting("pypi_dropped");
		missingImports = [];
		received = [];

		importedModules = [];
		await runStudentCode({ code: "import math" });

		expect(warnings()).toHaveLength(0);
	});

	test("a library the project declared is installed without a warning", async () => {
		missingImports = ["pypi_declared"];

		await runProgramImporting("pypi_declared", {
			explicitPackageList: ["Pypi-Declared>=1.0"],
		});

		expect(install).toHaveBeenCalledWith("pypi_declared");
		expect(warnings()).toHaveLength(0);
	});

	test("a library that comes with Pyodide is installed without a warning", async () => {
		missingImports = ["pypi_shipped"];
		// micropip serves the request from Pyodide's own distribution.
		install.mockImplementation(async () => {
			loadedPackages["pypi-shipped"] = "default channel";
		});

		await runProgramImporting("pypi_shipped");

		expect(install).toHaveBeenCalledWith("pypi_shipped");
		expect(warnings()).toHaveLength(0);
	});

	test("a library from a wheel index is installed without a warning", async () => {
		missingImports = ["pypi_indexed"];
		const indexUrl = "https://wheels.example/pypi-indexed/wheels.json";
		// PyPI cannot supply it; the course's wheel index can.
		install.mockImplementation(async (spec: string | string[]) => {
			if (spec === "pypi_indexed") {
				throw new Error("Can't find a pure Python 3 wheel");
			}
		});
		jest.spyOn(globalThis, "fetch").mockResolvedValue({
			ok: true,
			json: async () => ({
				wheels: ["pypi_indexed-1.0-py3-none-any.whl"],
			}),
		} as Response);

		await runProgramImporting("pypi_indexed", {
			packageIndexes: [indexUrl],
		});

		expect(install).toHaveBeenCalledWith(
			["https://wheels.example/pypi-indexed/wheels/pypi_indexed-1.0-py3-none-any.whl"],
		);
		expect(warnings()).toHaveLength(0);
	});

	test.each([
		[
			"a name that cannot be imported from it",
			"ImportError: cannot import name 'make_greeting' from 'MODULE' (/lib/python3.14/site-packages/MODULE/__init__.py)",
			"make_greeting",
		],
		[
			"an attribute it does not have",
			"AttributeError: module 'MODULE' has no attribute 'make_greeting'",
			"make_greeting",
		],
		[
			"a submodule it does not have",
			"ModuleNotFoundError: No module named 'MODULE.greetings'",
			"greetings",
		],
	])(
		"an error about %s explains that the library came from PyPI",
		async (label, pythonError, missing) => {
			const module = `pypi_shadow_${label.split(" ")[1]}`;
			missingImports = [module];
			studentCodeError = new Error(
				`Traceback (most recent call last):\n  File "main.py", line 1, in <module>\n${pythonError.replaceAll("MODULE", module)}\n`,
			);
			studentCodeError.name = "PythonError";

			await expect(runProgramImporting(module)).rejects.toBe(
				studentCodeError,
			);

			const failure = received.find(
				(event) => event.error.id === "runtime.student_code_failed",
			);
			const steps = failure?.error.friendly_steps ?? [];
			expect(steps).toHaveLength(3);
			expect(steps[0]).toBe(
				`There is no \`${module}.py\` next to your program, so Drafter installed the library named \`${module}\` from PyPI. If \`${module}\` is meant to be one of your own files, that library is something else.`,
			);
			expect(steps[1]).toContain("deployed with your site");
			expect(steps[2]).toContain(`nothing named \`${missing}\``);
			// The student sees the same steps in the error dialog.
			expect(
				document.querySelector(".drafter-dialog-content")?.textContent,
			).toContain(`installed the library named \`${module}\` from PyPI`);
		},
	);

	test("the same error about a library the student asked for keeps the usual advice", async () => {
		missingImports = ["pypi_asked_for"];
		studentCodeError = new Error(
			"Traceback (most recent call last):\nImportError: cannot import name 'nope' from 'pypi_asked_for' (/lib/x.py)\n",
		);

		await expect(
			runProgramImporting("pypi_asked_for", {
				explicitPackageList: ["pypi_asked_for"],
			}),
		).rejects.toBe(studentCodeError);

		const failure = received.find(
			(event) => event.error.id === "runtime.student_code_failed",
		);
		expect(failure?.error.friendly_steps?.join(" ")).not.toContain("PyPI");
	});
});

// ---------------------------------------------------------------------------
// addMockPackages
// ---------------------------------------------------------------------------

describe("addMockPackages", () => {
	afterEach(() => {
		delete (window as AnyWindow).micropip;
	});

	test("registers each package as a 1.0.0 mock via micropip", () => {
		const addMockPackage = jest.fn();
		(window as AnyWindow).micropip = { add_mock_package: addMockPackage };
		addMockPackages(["rich", "typer"]);
		expect(addMockPackage.mock.calls).toEqual([
			["rich", "1.0.0"],
			["typer", "1.0.0"],
		]);
	});

	test("is a no-op when micropip is not present", () => {
		delete (window as AnyWindow).micropip;
		expect(() => addMockPackages(["rich"])).not.toThrow();
	});
});
