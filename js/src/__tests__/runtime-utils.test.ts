import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	addMockPackages,
	enqueueRuntimeWork,
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

	test("does nothing when neither package option is set", async () => {
		await setupEnvironment({ code: "print('hi')" });
		expect(install).not.toHaveBeenCalled();
		expect(loadPackagesFromImports).not.toHaveBeenCalled();
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
