/**
 * Wheel indexes: where the browser looks for a package that PyPI cannot
 * supply as a wheel.
 *
 * Some libraries students want (ChemPy, for example) exist on PyPI only as
 * source, which the browser cannot build. Drafter hosts pure-Python wheels
 * for them at an index: a `wheels.json` file listing wheel file names, with
 * the files in a `wheels/` folder beside it. Courses can host their own and
 * add them with `--package-index`.
 *
 * An index is a curated set of wheels that go together, and it is installed
 * as a set: when a package is found in an index, every wheel of that index
 * is installed without dependency resolution (micropip would otherwise go
 * back to PyPI for dependencies that are only in the index, and fail). The
 * packages' declared requirements that are still missing are then fetched
 * one by one, best effort, so that `sympy` or `numpy` come from the
 * browser's own distribution. A requirement nothing can supply is skipped,
 * since not every declared dependency is needed in the browser.
 */

/** The shape of a `wheels.json` index file. */
interface WheelIndexFile {
	pyodide_version?: string;
	wheels?: unknown;
}

/** One loaded index: wheel URLs by normalized project name. */
export interface WheelIndex {
	url: string;
	wheels: Map<string, string>;
}

/** What `installWithIndexes` needs from the runtime. */
export interface PackageRuntime {
	/** micropip.install for one requirement or a list of wheel URLs. */
	install(specs: string | string[], deps: boolean): Promise<void>;
	/** Declared requirements of installed distributions that are absent. */
	missingRequirements(distributions: string[]): Promise<string[]>;
	/** Normalized names of distributions already installed. */
	installedDistributions(): Promise<Set<string>>;
}

/** The outcome of installing one requirement with index fallback. */
export interface IndexInstallResult {
	/** The index the package came from, or null when PyPI supplied it. */
	index: string | null;
	/** Wheel URLs installed from that index. */
	wheels: string[];
	/** Declared requirements that were fetched afterwards. */
	requirements: string[];
	/** Declared requirements nothing could supply. */
	unresolved: string[];
}

/** Loaded (or failed) indexes by URL, so each is fetched once per page. */
const loadedIndexes = new Map<string, Promise<WheelIndex>>();

/**
 * The PEP 503 normalized form of a project name: lowercase, with runs of
 * `-`, `_` and `.` collapsed to one `-`.
 */
export function normalizeProjectName(name: string): string {
	return name.trim().toLowerCase().replace(/[-_.]+/g, "-");
}

/**
 * The project name at the front of a requirement such as `sym>=0.3.7`,
 * `Pillow[imaging]` or `chempy==0.10.2`; null when the text is not one.
 */
export function requirementName(requirement: string): string | null {
	const match = /^\s*([A-Za-z0-9][A-Za-z0-9._-]*)/.exec(requirement);
	return match ? normalizeProjectName(match[1]) : null;
}

/** The project name a wheel file name starts with, normalized. */
export function wheelProjectName(fileName: string): string | null {
	const base = fileName.split("/").pop() ?? fileName;
	if (!base.toLowerCase().endsWith(".whl")) {
		return null;
	}
	const name = base.split("-")[0];
	return name ? normalizeProjectName(name) : null;
}

/** Turn a fetched `wheels.json` into a lookup table of wheel URLs. */
export function parseWheelIndex(url: string, file: WheelIndexFile): WheelIndex {
	const wheels = new Map<string, string>();
	const entries = Array.isArray(file.wheels) ? file.wheels : [];
	for (const entry of entries) {
		if (typeof entry !== "string") {
			continue;
		}
		const name = wheelProjectName(entry);
		if (!name || wheels.has(name)) {
			continue;
		}
		// Plain file names live in the wheels/ folder beside the index;
		// an entry with a path or a full URL is taken as written.
		const location = entry.includes("/") ? entry : `wheels/${entry}`;
		wheels.set(name, new URL(location, url).href);
	}
	return { url, wheels };
}

/**
 * Fetch and parse an index once. A failure (offline, 404, bad JSON) is
 * reported on the console and the index is treated as empty; the failure
 * is remembered so the index is not re-fetched for every missing package.
 */
export function loadWheelIndex(
	url: string,
	fetchImpl: typeof fetch = fetch,
): Promise<WheelIndex> {
	const existing = loadedIndexes.get(url);
	if (existing) {
		return existing;
	}
	const loading = (async () => {
		try {
			const response = await fetchImpl(url);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}
			return parseWheelIndex(url, (await response.json()) as WheelIndexFile);
		} catch (error) {
			console.warn(`[Drafter] Could not read the wheel index ${url}:`, error);
			return { url, wheels: new Map<string, string>() };
		}
	})();
	loadedIndexes.set(url, loading);
	return loading;
}

/** The first index, in order, that has a wheel for the project; else null. */
export async function findIndexFor(
	projectName: string,
	indexes: string[],
	fetchImpl: typeof fetch = fetch,
): Promise<WheelIndex | null> {
	const wanted = normalizeProjectName(projectName);
	for (const url of indexes) {
		const index = await loadWheelIndex(url, fetchImpl);
		if (index.wheels.has(wanted)) {
			return index;
		}
	}
	return null;
}

/**
 * Install a requirement from PyPI, or from the first wheel index that has
 * it when PyPI cannot supply it. Rejects with micropip's own error when no
 * index has the package either.
 */
export async function installWithIndexes(
	runtime: PackageRuntime,
	spec: string,
	indexes: string[],
	fetchImpl: typeof fetch = fetch,
): Promise<IndexInstallResult> {
	const empty: IndexInstallResult = {
		index: null,
		wheels: [],
		requirements: [],
		unresolved: [],
	};
	let pypiError: unknown;
	try {
		await runtime.install(spec, true);
		return empty;
	} catch (error) {
		pypiError = error;
	}
	const name = requirementName(spec);
	const index =
		name && indexes.length > 0 ? await findIndexFor(name, indexes, fetchImpl) : null;
	if (!index) {
		throw pypiError;
	}

	// The whole set, minus what is already there.
	const installed = await runtime.installedDistributions();
	const wheels = Array.from(index.wheels.entries())
		.filter(([project]) => !installed.has(project))
		.map(([, url]) => url);
	if (wheels.length > 0) {
		await runtime.install(wheels, false);
	}

	// Whatever the set's packages declare and still lack, from PyPI or the
	// browser's own distribution; a requirement nothing can supply is
	// skipped rather than failing the whole install.
	const requirements: string[] = [];
	const unresolved: string[] = [];
	for (const requirement of await runtime.missingRequirements(
		Array.from(index.wheels.keys()),
	)) {
		try {
			await runtime.install(requirement, true);
			requirements.push(requirement);
		} catch (error) {
			unresolved.push(requirement);
			console.warn(
				`[Drafter] ${requirement} (needed by a package from ${index.url}) could not be installed:`,
				error,
			);
		}
	}
	return { index: index.url, wheels, requirements, unresolved };
}

/** Test hook: forget every loaded index. */
export function resetWheelIndexesForTesting(): void {
	loadedIndexes.clear();
}
