/**
 * Tests for the wheel-index fallback (js/src/package_index.ts): when PyPI
 * cannot install a package and what it requires in one step, Drafter
 * installs it piece by piece, taking from a wheel index what PyPI lacks.
 */
import { afterEach, describe, expect, jest, test } from "@jest/globals";

import {
	findIndexFor,
	installWithIndexes,
	loadWheelIndex,
	normalizeProjectName,
	parseWheelIndex,
	requirementName,
	resetWheelIndexesForTesting,
	wheelProjectName,
	type PackageRuntime,
} from "../package_index";

const INDEX_URL = "https://drafter-edu.github.io/packages/wheels.json";
const INDEX_FILE = {
	pyodide_version: "0.29.5",
	wheels: [
		"sym-0.3.7-py2.py3-none-any.whl",
		"pyneqsys-0.5.7-py2.py3-none-any.whl",
		"chempy-0.10.2-py2.py3-none-any.whl",
		"progressbar-2.5-py3-none-any.whl",
		"qmsolve-2.0.0-py3-none-any.whl",
	],
};

jest.spyOn(console, "warn").mockImplementation(() => {});

/** A fetch that serves the given indexes by URL and 404s anything else. */
function fakeFetch(indexes: Record<string, unknown>): typeof fetch {
	return jest.fn(async (input: RequestInfo | URL) => {
		const url = String(input);
		if (url in indexes) {
			return new Response(JSON.stringify(indexes[url]), { status: 200 });
		}
		return new Response("not found", { status: 404 });
	}) as unknown as typeof fetch;
}

/** micropip's message when a requirement has no installable wheel. */
function noWheelError(requirement: string): Error {
	return new Error(
		`ValueError: Can't find a pure Python 3 wheel for '${requirement}'.`,
	);
}

/**
 * A stand-in runtime. `pypi` lists what PyPI (or the browser's own
 * distribution) has a wheel for; wheel URLs always install. `declares` maps
 * a distribution to its declared requirements. Like micropip, installing
 * with `deps` installs what the package requires too, and fails as a whole
 * when PyPI lacks any of it.
 */
function fakeRuntime(pypi: string[], declares: Record<string, string[]> = {}) {
	const installed = new Set<string>();
	const calls: Array<{ specs: string | string[]; deps: boolean }> = [];
	/** The package and everything it requires, or an error for what PyPI lacks. */
	function resolve(spec: string, wanted: Set<string>): void {
		const name = requirementName(spec)!;
		if (installed.has(name) || wanted.has(name)) {
			return;
		}
		if (!pypi.includes(name)) {
			throw noWheelError(spec);
		}
		wanted.add(name);
		for (const requirement of declares[name] ?? []) {
			resolve(requirement, wanted);
		}
	}
	const runtime: PackageRuntime = {
		async install(specs, deps) {
			calls.push({ specs, deps });
			const list = Array.isArray(specs) ? specs : [specs];
			for (const spec of list) {
				if (spec.includes("/")) {
					installed.add(wheelProjectName(spec)!);
					continue;
				}
				const name = requirementName(spec)!;
				if (!pypi.includes(name)) {
					throw noWheelError(spec);
				}
				const wanted = new Set<string>();
				if (deps) {
					resolve(spec, wanted);
				} else {
					wanted.add(name);
				}
				wanted.forEach((each) => installed.add(each));
			}
		},
		async missingRequirements(distributions) {
			const missing = new Set<string>();
			for (const dist of distributions) {
				for (const req of declares[dist] ?? []) {
					if (!installed.has(normalizeProjectName(req))) {
						missing.add(req);
					}
				}
			}
			return Array.from(missing).sort();
		},
	};
	return { runtime, installed, calls };
}

afterEach(() => {
	resetWheelIndexesForTesting();
});

describe("names", () => {
	test("project names normalize the way PyPI does", () => {
		expect(normalizeProjectName("Py_Neq.Sys")).toBe("py-neq-sys");
		expect(normalizeProjectName(" ChemPy ")).toBe("chempy");
	});

	test("requirement names drop version specifiers and extras", () => {
		expect(requirementName("sym>=0.3.7")).toBe("sym");
		expect(requirementName("Pillow[imaging]==10.0")).toBe("pillow");
		expect(requirementName("chempy")).toBe("chempy");
		expect(requirementName(">=1.0")).toBeNull();
	});

	test("wheel file names give their project", () => {
		expect(wheelProjectName("chempy-0.10.2-py2.py3-none-any.whl")).toBe("chempy");
		expect(wheelProjectName("wheels/Sym-0.3.7-py3-none-any.whl")).toBe("sym");
		expect(wheelProjectName("README.md")).toBeNull();
	});
});

describe("parseWheelIndex", () => {
	test("plain file names resolve into the wheels folder beside the index", () => {
		const index = parseWheelIndex(INDEX_URL, INDEX_FILE);

		expect(index.wheels.get("chempy")).toBe(
			"https://drafter-edu.github.io/packages/wheels/chempy-0.10.2-py2.py3-none-any.whl",
		);
		expect(index.wheels.size).toBe(5);
	});

	test("entries with a path or full URL are taken as written", () => {
		const index = parseWheelIndex("https://x.example/idx/wheels.json", {
			wheels: [
				"extra/tabulate-0.10.0-py3-none-any.whl",
				"https://cdn.example/pulp-3.3.0-py3-none-any.whl",
			],
		});

		expect(index.wheels.get("tabulate")).toBe(
			"https://x.example/idx/extra/tabulate-0.10.0-py3-none-any.whl",
		);
		expect(index.wheels.get("pulp")).toBe(
			"https://cdn.example/pulp-3.3.0-py3-none-any.whl",
		);
	});

	test("malformed files give an empty index", () => {
		expect(parseWheelIndex(INDEX_URL, {}).wheels.size).toBe(0);
		expect(
			parseWheelIndex(INDEX_URL, { wheels: [42, null, "notes.txt"] }).wheels
				.size,
		).toBe(0);
	});
});

describe("loadWheelIndex and findIndexFor", () => {
	test("an index is fetched once and indexes are searched in order", async () => {
		const course = "https://course.example/wheels.json";
		const fetchImpl = fakeFetch({
			[course]: { wheels: ["sym-9.9.9-py3-none-any.whl"] },
			[INDEX_URL]: INDEX_FILE,
		});

		expect((await findIndexFor("sym", [course, INDEX_URL], fetchImpl))?.url).toBe(
			course,
		);
		expect(
			(await findIndexFor("ChemPy", [course, INDEX_URL], fetchImpl))?.url,
		).toBe(INDEX_URL);
		expect(await findIndexFor("numpy", [course, INDEX_URL], fetchImpl)).toBeNull();
		expect(fetchImpl).toHaveBeenCalledTimes(2);
	});

	test("an unreachable index counts as empty and is not refetched", async () => {
		const fetchImpl = fakeFetch({});
		const gone = "https://gone.example/w.json";

		expect(await findIndexFor("chempy", [gone], fetchImpl)).toBeNull();
		expect(await findIndexFor("sym", [gone], fetchImpl)).toBeNull();

		expect(fetchImpl).toHaveBeenCalledTimes(1);
		expect((await loadWheelIndex(gone, fetchImpl)).wheels.size).toBe(0);
	});
});

describe("installWithIndexes", () => {
	test("a package PyPI can supply never touches the indexes", async () => {
		const { runtime, calls } = fakeRuntime(["wordfreq"]);
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "wordfreq", [INDEX_URL], fetchImpl);

		expect(result.index).toBeNull();
		expect(calls).toEqual([{ specs: "wordfreq", deps: true }]);
		expect(fetchImpl).not.toHaveBeenCalled();
	});

	test("a package only an index has is installed with just the wheels it needs", async () => {
		const { runtime, installed, calls } = fakeRuntime(["numpy", "sympy"], {
			chempy: ["numpy", "sympy", "pyneqsys"],
			pyneqsys: ["sym", "notebook"],
		});
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.index).toBe(INDEX_URL);
		// Each wheel goes in alone, without dependency resolution: micropip
		// would go back to PyPI for requirements only the index has.
		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"chempy",
			"pyneqsys",
			"sym",
		]);
		expect(calls[1]).toEqual({ specs: [result.wheels[0]], deps: false });
		// What the wheels declare and PyPI has is fetched one by one; a
		// requirement nothing can supply is skipped, not fatal.
		expect(result.requirements).toEqual(["numpy", "sympy"]);
		expect(result.unresolved).toEqual(["notebook"]);
		expect(installed.has("chempy")).toBe(true);
		// The index's other wheels are someone else's packages.
		expect(installed.has("qmsolve")).toBe(false);
		expect(installed.has("progressbar")).toBe(false);
	});

	test("a PyPI package is installed when only something it requires is missing from PyPI", async () => {
		// qmsolve has a wheel on PyPI; progressbar, which it requires, is
		// source-only there, so the one-step install fails.
		const { runtime, installed } = fakeRuntime(["qmsolve", "numpy", "scipy"], {
			qmsolve: ["numpy", "scipy", "progressbar"],
		});
		const course = "https://course.example/wheels.json";
		const fetchImpl = fakeFetch({
			[course]: { wheels: ["progressbar-2.5-py3-none-any.whl"] },
		});

		const result = await installWithIndexes(runtime, "qmsolve", [course], fetchImpl);

		// qmsolve itself came from PyPI, so no index is credited with it.
		expect(result.index).toBeNull();
		expect(result.wheels).toEqual([
			"https://course.example/wheels/progressbar-2.5-py3-none-any.whl",
		]);
		expect(result.requirements).toEqual(["numpy", "scipy"]);
		expect(result.unresolved).toEqual([]);
		expect([...installed].sort()).toEqual(["numpy", "progressbar", "qmsolve", "scipy"]);
	});

	test("a PyPI package is still installed when nothing can supply one of its requirements", async () => {
		const { runtime, installed } = fakeRuntime(["qmsolve", "numpy"], {
			qmsolve: ["numpy", "progressbar"],
		});
		const fetchImpl = fakeFetch({});

		const result = await installWithIndexes(runtime, "qmsolve", [], fetchImpl);

		expect(result.unresolved).toEqual(["progressbar"]);
		expect(installed.has("qmsolve")).toBe(true);
		expect(installed.has("numpy")).toBe(true);
	});

	test("a requirement comes from the index that supplied the package needing it", async () => {
		// PyPI has its own tabulate, but the index pins the one its chempy
		// was built with.
		const { runtime, calls } = fakeRuntime(["tabulate"], {
			chempy: ["tabulate"],
		});
		const fetchImpl = fakeFetch({
			[INDEX_URL]: {
				wheels: [
					"chempy-0.10.2-py2.py3-none-any.whl",
					"tabulate-0.10.0-py3-none-any.whl",
				],
			},
		});

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"chempy",
			"tabulate",
		]);
		expect(result.requirements).toEqual([]);
		expect(calls).not.toContainEqual({ specs: "tabulate", deps: true });
	});

	test("a requirement PyPI cannot fully install is not installed alone", async () => {
		// notebook has a wheel, but what it requires does not. Installing
		// it alone would start pulling in the rest of Jupyter piece by piece.
		const { runtime, installed, calls } = fakeRuntime(["notebook"], {
			chempy: ["notebook"],
			notebook: ["tornado"],
		});
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.unresolved).toEqual(["notebook"]);
		expect(installed.has("notebook")).toBe(false);
		expect(calls).not.toContainEqual({ specs: "notebook", deps: false });
	});

	test("wheels that require each other are each installed once", async () => {
		const { runtime, calls } = fakeRuntime([], {
			sym: ["pyneqsys"],
			pyneqsys: ["sym"],
		});
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "sym", [INDEX_URL], fetchImpl);

		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"sym",
			"pyneqsys",
		]);
		expect(calls.filter((call) => !call.deps)).toHaveLength(2);
	});

	test("wheels already installed are not downloaded again", async () => {
		const { runtime, calls } = fakeRuntime([], {
			chempy: ["pyneqsys"],
			pyneqsys: ["sym"],
		});
		await runtime.install(["https://x.example/wheels/sym-0.3.7-py3-none-any.whl"], false);
		calls.length = 0;
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"chempy",
			"pyneqsys",
		]);
	});

	test("the first index listing the package wins", async () => {
		const course = "https://course.example/wheels.json";
		const { runtime } = fakeRuntime([]);
		const fetchImpl = fakeFetch({
			[course]: { wheels: ["chempy-0.11.0-py3-none-any.whl"] },
			[INDEX_URL]: INDEX_FILE,
		});

		const result = await installWithIndexes(runtime, "chempy", [course, INDEX_URL], fetchImpl);

		expect(result.index).toBe(course);
		expect(result.wheels).toEqual([
			"https://course.example/wheels/chempy-0.11.0-py3-none-any.whl",
		]);
	});

	test("a package in no index fails with micropip's own error", async () => {
		const { runtime } = fakeRuntime([]);
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		await expect(
			installWithIndexes(runtime, "numpy-rocket", [INDEX_URL], fetchImpl),
		).rejects.toThrow("Can't find a pure Python 3 wheel for 'numpy-rocket'");
	});

	test("the error names what was missing when PyPI lacks the package itself", async () => {
		// The one-step failure is the one reported, not the retry's.
		const { runtime } = fakeRuntime([]);
		runtime.install = jest.fn(async (_specs: string | string[], deps: boolean) => {
			throw new Error(deps ? "one-step failure" : "alone failure");
		});

		await expect(
			installWithIndexes(runtime, "chempy", [], fakeFetch({})),
		).rejects.toThrow("one-step failure");
	});

	test("without indexes PyPI alone decides and nothing is fetched", async () => {
		const { runtime, calls } = fakeRuntime([]);
		const fetchImpl = fakeFetch({});

		await expect(installWithIndexes(runtime, "chempy", [], fetchImpl)).rejects.toThrow(
			"chempy",
		);
		// In one step, then alone.
		expect(calls).toEqual([
			{ specs: "chempy", deps: true },
			{ specs: "chempy", deps: false },
		]);
		expect(fetchImpl).not.toHaveBeenCalled();
	});
});
