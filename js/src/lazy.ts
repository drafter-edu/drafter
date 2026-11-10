/**
 * On-demand loading of optional Drafter bundles.
 *
 * Every Drafter page downloads the main bundle, so anything large that only
 * a few visitors use (the HTML-to-Drafter converter pulls in an HTML parser
 * and a CSS parser) is built as its own file and fetched the first time it
 * is needed. A lazy bundle is a plain IIFE that defines one global; loading
 * it means adding a <script> element next to the main bundle and waiting
 * for that global to appear.
 */

/** File names of the main bundles, used to find where Drafter's scripts live. */
const MAIN_BUNDLE_NAMES = ["drafter.pyodide.js", "drafter.skulpt.js"];

/**
 * The address this script was loaded from, captured while the bundle is
 * first executing (the only time `document.currentScript` is set).
 */
const CURRENT_SCRIPT_SRC: string | null =
	typeof document !== "undefined" &&
	document.currentScript instanceof HTMLScriptElement
		? document.currentScript.src || null
		: null;

/** In-flight and finished loads, so each bundle is requested once. */
const pendingLoads = new Map<string, Promise<unknown>>();

/**
 * The address of Drafter's main bundle on this page, or null when it cannot
 * be determined (for example, in a unit test with no script element).
 */
export function findMainBundleUrl(doc: Document = document): string | null {
	if (CURRENT_SCRIPT_SRC) {
		return CURRENT_SCRIPT_SRC;
	}
	for (const script of Array.from(doc.querySelectorAll("script[src]"))) {
		const src = (script as HTMLScriptElement).src;
		if (MAIN_BUNDLE_NAMES.some((name) => src.includes(name))) {
			return src;
		}
	}
	return null;
}

/**
 * Work out a lazy bundle's address from the main bundle's: the same folder
 * and the same query string, so the version stamp that keeps browsers from
 * reusing an old main bundle (`?v=2.1.4`) protects lazy bundles too.
 */
export function resolveLazyBundleUrl(
	bundleName: string,
	mainBundleUrl: string,
): string {
	const queryStart = mainBundleUrl.indexOf("?");
	const path =
		queryStart === -1 ? mainBundleUrl : mainBundleUrl.slice(0, queryStart);
	const query = queryStart === -1 ? "" : mainBundleUrl.slice(queryStart);
	const folder = path.slice(0, path.lastIndexOf("/") + 1);
	return `${folder}${bundleName}.js${query}`;
}

/**
 * Load an optional bundle and return the global it defines.
 *
 * Safe to call repeatedly: the script is added once, and later calls get
 * the same result. A failed load is forgotten, so calling again retries.
 *
 * @param bundleName File name without ".js", such as "drafter.transpiler".
 * @param globalName The global the bundle defines, such as "DrafterTranspiler".
 * @param doc The document to add the script to (the one running this code).
 */
export function loadLazyBundle<T = unknown>(
	bundleName: string,
	globalName: string,
	doc: Document = document,
): Promise<T> {
	const scope = (doc.defaultView ?? window) as unknown as Record<
		string,
		unknown
	>;
	if (scope[globalName] !== undefined) {
		return Promise.resolve(scope[globalName] as T);
	}
	const existing = pendingLoads.get(bundleName);
	if (existing) {
		return existing as Promise<T>;
	}
	const load = new Promise<T>((resolve, reject) => {
		const mainBundleUrl = findMainBundleUrl(doc);
		if (!mainBundleUrl) {
			reject(
				new Error(
					`Cannot load ${bundleName}.js: Drafter's main script was not found on this page.`,
				),
			);
			return;
		}
		const url = resolveLazyBundleUrl(bundleName, mainBundleUrl);
		const script = doc.createElement("script");
		script.src = url;
		script.async = true;
		script.addEventListener("load", () => {
			if (scope[globalName] === undefined) {
				reject(
					new Error(
						`${url} loaded but did not define ${globalName}.`,
					),
				);
				return;
			}
			resolve(scope[globalName] as T);
		});
		script.addEventListener("error", () => {
			script.remove();
			reject(new Error(`Could not load ${url}.`));
		});
		(doc.head ?? doc.documentElement).appendChild(script);
	});
	pendingLoads.set(bundleName, load);
	// Forget a failure so the next call can try again (a dropped connection
	// should not disable the feature for the rest of the session).
	load.catch(() => pendingLoads.delete(bundleName));
	return load;
}

/** Test hook: forget every load so a test starts from a clean slate. */
export function resetLazyBundlesForTesting(): void {
	pendingLoads.clear();
}
