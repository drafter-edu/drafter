// Static server for the Playwright e2e suites.
//
// Serves:
//   /                     -> e2e/pages/            (test harness pages)
//   /assets/              -> dist/                 (built drafter bundles + css)
//   /pyodide/             -> node_modules/pyodide/ (local Pyodide distribution)
//   /drafter-pyodide.zip  -> playground/__drafter_assets/drafter-pyodide.zip
//
// Every response carries COOP/COEP headers so pages are cross-origin isolated
// and SharedArrayBuffer (the interrupt machinery) is available. Set
// DRAFTER_E2E_NO_ISOLATION=1 to disable if a third-party fetch breaks.
//
// Prerequisites: `npm run build` and `node playground/build-playground.mjs`
// (or `npm run playground:build`) so dist/ and the drafter zip exist.

import http from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const jsRoot = path.resolve(__dirname, "..");

const PORT = Number(process.env.PORT || 8787);
const ISOLATE = process.env.DRAFTER_E2E_NO_ISOLATION !== "1";

const MOUNTS = [
	{ prefix: "/assets/", root: path.join(jsRoot, "dist") },
	// The drafter runtime resolves its stylesheets relative to this directory
	// (same layout the playground and deployed sites use).
	{ prefix: "/__drafter_assets/", root: path.join(jsRoot, "dist") },
	{ prefix: "/pyodide/", root: path.join(jsRoot, "node_modules", "pyodide") },
	{ prefix: "/", root: path.join(__dirname, "pages") },
];

const ZIP_PATH = path.join(
	jsRoot,
	"playground",
	"__drafter_assets",
	"drafter-pyodide.zip",
);

const CONTENT_TYPES = {
	".html": "text/html; charset=utf-8",
	".js": "text/javascript; charset=utf-8",
	".mjs": "text/javascript; charset=utf-8",
	".css": "text/css; charset=utf-8",
	".json": "application/json",
	".wasm": "application/wasm",
	".zip": "application/zip",
	".whl": "application/octet-stream",
	".py": "text/x-python; charset=utf-8",
	".dat": "application/octet-stream",
	".txt": "text/plain; charset=utf-8",
};

function resolveFile(urlPath) {
	if (urlPath === "/drafter-pyodide.zip") {
		return ZIP_PATH;
	}
	for (const { prefix, root } of MOUNTS) {
		if (!urlPath.startsWith(prefix)) {
			continue;
		}
		const rel = urlPath.slice(prefix.length) || "harness.html";
		const resolved = path.normalize(path.join(root, rel));
		// Path-traversal guard: the resolved file must stay inside the mount.
		if (!resolved.startsWith(path.normalize(root + path.sep))) {
			return null;
		}
		if (existsSync(resolved) && statSync(resolved).isFile()) {
			return resolved;
		}
	}
	return null;
}

const missing = [];
if (!existsSync(path.join(jsRoot, "dist", "js", "drafter.pyodide.js"))) {
	missing.push("dist/js/drafter.pyodide.js (run `npm run build`)");
}
if (!existsSync(ZIP_PATH)) {
	missing.push(
		"playground/__drafter_assets/drafter-pyodide.zip (run `node playground/build-playground.mjs`)",
	);
}
if (missing.length > 0) {
	console.error("e2e server missing prerequisites:\n  - " + missing.join("\n  - "));
	process.exit(1);
}

const server = http.createServer((req, res) => {
	const urlPath = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
	const file = resolveFile(urlPath);

	const headers = { "Cache-Control": "no-store" };
	if (ISOLATE) {
		headers["Cross-Origin-Opener-Policy"] = "same-origin";
		headers["Cross-Origin-Embedder-Policy"] = "require-corp";
		headers["Cross-Origin-Resource-Policy"] = "cross-origin";
	}

	if (file === null) {
		res.writeHead(404, headers);
		res.end(`Not found: ${urlPath}`);
		return;
	}

	headers["Content-Type"] =
		CONTENT_TYPES[path.extname(file).toLowerCase()] ||
		"application/octet-stream";
	res.writeHead(200, headers);
	createReadStream(file).pipe(res);
});

server.listen(PORT, "127.0.0.1", () => {
	console.log(
		`drafter e2e server on http://127.0.0.1:${PORT} (isolation: ${ISOLATE})`,
	);
});
