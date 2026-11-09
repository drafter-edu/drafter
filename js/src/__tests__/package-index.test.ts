/**
 * Tests for the wheel-index fallback (js/src/package_index.ts): when PyPI
 * cannot supply a package, Drafter installs the wheel index that has it as
 * a set, then fetches the set's declared requirements best effort.
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
 * distribution) can install; wheel URLs always install. `declares` maps a
 * distribution to its declared requirements.
 */
function fakeRuntime(pypi: string[], declares: Record<string, string[]> = {}) {
	const installed = new Set<string>();
	const calls: Array<{ specs: string | string[]; deps: boolean }> = [];
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
				installed.add(name);
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
		async installedDistributions() {
			return new Set(installed);
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
		expect(index.wheels.size).toBe(3);
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

	test("a package only an index has is installed as that index's set, without dependency resolution", async () => {
		const { runtime, installed, calls } = fakeRuntime(["numpy", "sympy"], {
			chempy: ["numpy", "sympy", "pyneqsys"],
			pyneqsys: ["sym", "notebook"],
		});
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.index).toBe(INDEX_URL);
		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"sym",
			"pyneqsys",
			"chempy",
		]);
		// The set goes in as one deps=False install...
		expect(calls[1]).toEqual({ specs: result.wheels, deps: false });
		// ...then what the set still declares is fetched one by one; a
		// requirement nothing can supply is skipped, not fatal.
		expect(result.requirements).toEqual(["numpy", "sympy"]);
		expect(result.unresolved).toEqual(["notebook"]);
		expect(installed.has("chempy")).toBe(true);
	});

	test("wheels already installed are not downloaded again", async () => {
		const { runtime, calls } = fakeRuntime([]);
		await runtime.install(["https://x.example/wheels/sym-0.3.7-py3-none-any.whl"], false);
		calls.length = 0;
		const fetchImpl = fakeFetch({ [INDEX_URL]: INDEX_FILE });

		const result = await installWithIndexes(runtime, "chempy", [INDEX_URL], fetchImpl);

		expect(result.wheels.map((url) => wheelProjectName(url))).toEqual([
			"pyneqsys",
			"chempy",
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

	test("without indexes the PyPI failure is final and nothing is fetched", async () => {
		const { runtime, calls } = fakeRuntime([]);
		const fetchImpl = fakeFetch({});

		await expect(installWithIndexes(runtime, "chempy", [], fetchImpl)).rejects.toThrow(
			"chempy",
		);
		expect(calls).toHaveLength(1);
		expect(fetchImpl).not.toHaveBeenCalled();
	});
});
