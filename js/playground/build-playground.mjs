/**
 * Assemble the self-contained asset bundle the multi-instance playground serves.
 *
 * Produces js/playground/__drafter_assets/ containing:
 *   - js/drafter.pyodide.js     (the freshly built client bundle)
 *   - css/*.css                 (drafter stylesheets)
 *   - drafter-pyodide.zip       (the current src/drafter package, so the
 *                                playground reflects local Python changes)
 *
 * Run `npm run build` in js/ first (to refresh dist/), then:  node playground/build-playground.mjs
 */

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const jsDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(jsDir, "..");
const assetsDir = path.join(__dirname, "__drafter_assets");

function ensureDir(dir) {
	fs.mkdirSync(dir, { recursive: true });
}

function copyInto(srcFile, destDir) {
	ensureDir(destDir);
	fs.copyFileSync(srcFile, path.join(destDir, path.basename(srcFile)));
}

// 1) Client bundle
const bundle = path.join(jsDir, "dist", "js", "drafter.pyodide.js");
if (!fs.existsSync(bundle)) {
	console.error(
		`Missing ${bundle}. Run \`npm run build\` in js/ before building the playground.`,
	);
	process.exit(1);
}
copyInto(bundle, path.join(assetsDir, "js"));

// 2) CSS
const cssSrc = path.join(jsDir, "dist", "css");
for (const file of fs.readdirSync(cssSrc)) {
	if (file.endsWith(".css")) copyInto(path.join(cssSrc, file), path.join(assetsDir, "css"));
}

// 3) drafter package zip (current src/drafter -> drafter/... + pyproject.toml),
//    matching drafter.builder.build.build_zip so mountDrafterRemote can unpack it.
const zipOut = path.join(assetsDir, "drafter-pyodide.zip");
ensureDir(assetsDir);
const py = `
import os, zipfile
from pathlib import Path
src = Path(${JSON.stringify(path.join(repoRoot, "src", "drafter"))})
out = ${JSON.stringify(zipOut)}
skip = {".pyc"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src):
        if "__pycache__" in root:
            continue
        for f in files:
            p = Path(root) / f
            if p.suffix in skip:
                continue
            z.write(p, Path("drafter") / p.relative_to(src))
    z.write(${JSON.stringify(path.join(repoRoot, "pyproject.toml"))}, "pyproject.toml")
print("wrote", out)
`;
const res = spawnSync("python", ["-c", py], { stdio: "inherit" });
if (res.status !== 0) {
	console.error("Failed to build drafter-pyodide.zip (is `python` on PATH?)");
	process.exit(1);
}

console.log("Playground assets ready in", assetsDir);
