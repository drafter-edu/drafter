// Ensures the Pyodide-distribution wheels the e2e suites need exist in
// node_modules/pyodide, which e2e/server.mjs serves as /pyodide/.
//
// The pyodide npm package ships only the core runtime (pyodide.asm.wasm,
// python_stdlib.zip, pyodide-lock.json) — NOT the package wheels. In Node,
// pyodide downloads missing packages from the CDN and caches them next to
// the runtime, so loading the packages here once populates the directory
// the browser tests fetch from. On a warm cache this is a fast no-op reload.
//
// Without this, a fresh checkout (e.g. CI) 404s on /pyodide/micropip-*.whl
// and setupPyodide dies with "No module named 'micropip'".

import { loadPyodide } from "pyodide";

// micropip: loaded by setupPyodide at boot (deps resolved automatically).
// pillow: installed by harness.html via micropip, which resolves wheels for
// pyodide-distribution packages from the same /pyodide/ index.
const PACKAGES = ["micropip", "pillow"];

const pyodide = await loadPyodide({ fullStdLib: false });
await pyodide.loadPackage(PACKAGES);
console.log(
	"pyodide package cache ready:",
	Object.keys(pyodide.loadedPackages).sort().join(", "),
);
// Pyodide's Node runtime keeps handles alive; exit explicitly.
process.exit(0);
