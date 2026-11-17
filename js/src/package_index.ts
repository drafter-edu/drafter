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
 * micropip installs a package and everything it requires in one step, and
 * the whole step fails when any one of them has no wheel on PyPI. That
 * happens when the package itself is source-only (ChemPy), and also when a
 * package with a wheel requires one that is source-only (qmsolve requires
 * `progressbar`). When the one-step install fails, the package is installed
 * piece by piece instead: the package alone, from the first index that has
 * it or else from PyPI, and then each requirement it declares and still
 * lacks. Only what the package needs is installed, never the rest of an
 * index.
 *
 * A requirement comes from the index that supplied the package needing it,
 * when that index has it: an index's wheels are built to go together. Any
 * other requirement is installed in one step, so that `sympy` or `numpy`
 * come from the browser's own distribution, and from an index when that
 * fails. A requirement nothing can supply is skipped, since not every
 * declared dependency is needed in the browser.
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
}

/** The outcome of installing one requirement with index fallback. */
export interface IndexInstallResult {
	/** The index the package came from, or null when PyPI supplied it. */
	index: string | null;
	/** Wheel URLs installed from indexes, for the package or what it needs. */
	wheels: string[];
	/** Declared requirements that were fetched from PyPI afterwards. */
	requirements: string[];
	/** Declared requirements nothing could supply. */
	unresolved: string[];
}

/** One piece-by-piece install in progress. */
interface PiecewiseInstall {
	runtime: PackageRuntime;
	indexes: string[];
	fetchImpl: typeof fetch;
	/** Projects already attempted, so nothing is tried twice. */
	attempted: Set<string>;
	result: IndexInstallResult;
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
 * Install one package from an index, without what it requires: from
 * `preferred` when that index has it, else from the first configured index
 * that does.
 *
 * @returns The index the wheel came from, or null when no index has it.
 */
async function installFromIndex(
	project: string | null,
	preferred: WheelIndex | null,
	install: PiecewiseInstall,
): Promise<WheelIndex | null> {
	if (project === null) {
		return null;
	}
	const index = preferred?.wheels.has(project)
		? preferred
		: await findIndexFor(project, install.indexes, install.fetchImpl);
	const url = index?.wheels.get(project);
	if (!index || !url) {
		return null;
	}
	await install.runtime.install([url], false);
	install.result.wheels.push(url);
	return index;
}

/**
 * Install one requirement of a package that was installed alone.
 *
 * A requirement that PyPI cannot install in one step and no index has is
 * an error here; it is never installed alone from PyPI. That step is kept
 * for the package the program asked for: taken any deeper, a requirement
 * such as `notebook` would be installed without what it needs and then
 * pull in the rest of Jupyter one piece at a time.
 *
 * @param source The index that supplied the package needing this one, if any.
 */
async function installRequirement(
	requirement: string,
	project: string | null,
	source: WheelIndex | null,
	install: PiecewiseInstall,
): Promise<void> {
	let failure: unknown;
	// A wheel beside the package that needs it was built to go with it.
	if (project === null || !source?.wheels.has(project)) {
		try {
			await install.runtime.install(requirement, true);
			install.result.requirements.push(requirement);
			return;
		} catch (error) {
			failure = error;
		}
	}
	const index = await installFromIndex(project, source, install);
	if (!index || project === null) {
		throw failure;
	}
	await installRequirementsOf(project, index, install);
}

/**
 * Install what an installed package declares it requires and still lacks.
 * A requirement nothing can supply is recorded and skipped, not fatal.
 *
 * @param source The index that supplied the package, or null for PyPI.
 */
async function installRequirementsOf(
	project: string,
	source: WheelIndex | null,
	install: PiecewiseInstall,
): Promise<void> {
	for (const requirement of await install.runtime.missingRequirements([project])) {
		const needed = requirementName(requirement);
		const key = needed ?? requirement;
		if (install.attempted.has(key)) {
			continue;
		}
		install.attempted.add(key);
		try {
			await installRequirement(requirement, needed, source, install);
		} catch (error) {
			install.result.unresolved.push(requirement);
			console.warn(
				`[Drafter] ${requirement} (needed by ${project}) could not be installed:`,
				error,
			);
		}
	}
}

/**
 * Install a requirement and what it needs: in one step when PyPI and the
 * browser's own distribution can supply all of it, and otherwise piece by
 * piece, with the wheel indexes filling in what PyPI lacks (see the top of
 * this file). Rejects with micropip's own error when neither an index nor
 * PyPI has the requested package itself.
 */
export async function installWithIndexes(
	runtime: PackageRuntime,
	spec: string,
	indexes: string[],
	fetchImpl: typeof fetch = fetch,
): Promise<IndexInstallResult> {
	const result: IndexInstallResult = {
		index: null,
		wheels: [],
		requirements: [],
		unresolved: [],
	};
	let failure: unknown;
	try {
		await runtime.install(spec, true);
		return result;
	} catch (error) {
		failure = error;
	}
	const project = requirementName(spec);
	const install: PiecewiseInstall = {
		runtime,
		indexes,
		fetchImpl,
		attempted: new Set(project === null ? [] : [project]),
		result,
	};
	const index = await installFromIndex(project, null, install);
	if (index) {
		result.index = index.url;
	} else {
		// PyPI may have the package and lack only something it requires.
		try {
			await runtime.install(spec, false);
		} catch {
			throw failure;
		}
	}
	if (project !== null) {
		await installRequirementsOf(project, index, install);
	}
	return result;
}

/** Test hook: forget every loaded index. */
export function resetWheelIndexesForTesting(): void {
	loadedIndexes.clear();
}
