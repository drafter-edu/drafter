/**
 * Test-only replacement for the `pyodide` package entry point.
 *
 * Jest's `--experimental-vm-modules` sandbox cannot evaluate Pyodide's internal
 * dynamic `node:*` imports, so the real loader is preloaded in the Node realm by
 * `jest.jsdom-env.cjs` and exposed as `__realLoadPyodide`. This shim forwards to
 * it, allowing production code (`pyodide.index`) to keep importing from
 * `"pyodide"` unchanged.
 */

type LoadPyodideOptions = Record<string, unknown>;

export function loadPyodide(
	options: LoadPyodideOptions = {},
): Promise<unknown> {
	const realLoadPyodide = (globalThis as Record<string, unknown>)
		.__realLoadPyodide as
		| ((options: LoadPyodideOptions) => Promise<unknown>)
		| undefined;

	if (typeof realLoadPyodide !== "function") {
		throw new Error(
			"Real Pyodide loader is unavailable. The pyodide Jest environment " +
				"(jest.jsdom-env.cjs) must preload it for pyodide test files.",
		);
	}

	return realLoadPyodide(options);
}
