// Custom Jest environment: jsdom + Node's web platform globals.
//
// jsdom does not expose several standard web APIs (Fetch, Compression Streams,
// Streams, Blob/File, etc.) that the Skulpt-compiled Drafter runtime relies on.
// Node provides native implementations of these on its own realm, so we copy
// them onto the jsdom global here.
const { TestEnvironment: JSDOMEnvironment } = require("jest-environment-jsdom");

const GLOBALS_TO_COPY = [
	"fetch",
	"Headers",
	"Request",
	"Response",
	"FormData",
	"Blob",
	"File",
	"ReadableStream",
	"WritableStream",
	"TransformStream",
	"CompressionStream",
	"DecompressionStream",
	"TextEncoder",
	"TextDecoder",
	"structuredClone",
];

class DrafterJSDOMEnvironment extends JSDOMEnvironment {
	constructor(config, context) {
		super(config, context);

		this.testPath = context && context.testPath ? context.testPath : "";

		for (const name of GLOBALS_TO_COPY) {
			if (
				typeof this.global[name] === "undefined" &&
				typeof globalThis[name] !== "undefined"
			) {
				this.global[name] = globalThis[name];
			}
		}
	}

	async setup() {
		await super.setup();

		// Pyodide cannot be loaded inside Jest's `--experimental-vm-modules`
		// sandbox: its internal `await import("node:url")` (and friends) are
		// rejected across the test-scope boundary, hard-crashing Node. To work
		// around this we load Pyodide here in the real Node realm and expose a
		// loader on the jsdom global. `jsglobals` is pointed at the jsdom global
		// so Drafter's Python bridge (`import js; js.document`) renders into the
		// test DOM.
		if (this.testPath.includes("pyodide")) {
			const path = require("path");
			const { loadPyodide } = await import("pyodide");
			const jsGlobal = this.global;

			// Resolve the real Pyodide distribution directory. Pyodide's own
			// `import.meta.url`-based auto-detection misfires here (it points at
			// the source-mapped `src/js` path), so pin indexURL explicitly.
			const pyodideDistDir = path.dirname(require.resolve("pyodide"));

			this.global.__drafterSrcDir = path.resolve(
				__dirname,
				"..",
				"src",
				"drafter",
			);

			this.global.__realLoadPyodide = async (options = {}) => {
				const { indexURL, ...rest } = options || {};
				const finalOptions = {
					...rest,
					jsglobals: jsGlobal,
					// Honor an explicit non-empty indexURL, else use the
					// resolved bundled package directory.
					indexURL: indexURL || pyodideDistDir,
				};
				return loadPyodide(finalOptions);
			};
		}
	}
}

module.exports = DrafterJSDOMEnvironment;
