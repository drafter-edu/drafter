import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import "../dist/skulpt/skulpt.js";
import { minify_sync } from "terser";
import { program } from "commander";
import { precompileTypeScript } from "./precompile-typescript.mjs";

program
	.option("-m, --minify", "minify the resulting code")
	.option("-s, --skulpt-dir <path>", "path to the Skulpt directory")
	.parse(process.argv);

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Paths
const repoRoot = path.resolve(__dirname, "..", "..");

// Load env from repo root if present
dotenv.config({ path: path.join(repoRoot, ".env") });

const MODULE_NAME = "drafter";
const drafterPythonDir = path.resolve(repoRoot, "src", "drafter");
const target = path.resolve(repoRoot, "js", "dist", "skulpt");
const targetFilename = path.resolve(target, "skulpt-drafter.js");
const skulptDir = program.opts().skulptDir || process.env.SKULPT_DIR || "";
const javascriptModulesDir = path.resolve(repoRoot, "js", "src");
const extraJavascriptModules = [];

// , new RegExp("bridge/client\\.py")
const SKIP_FILES = [new RegExp("app/.+")];

Sk.configure({ __future__: Sk.python3 });

function buildPythonFile(ret, fullname, contents, shouldMinify) {
	let result = [];
	var internalName = fullname;
	while (internalName.startsWith(drafterPythonDir)) {
		internalName = internalName.slice(drafterPythonDir.length);
	}
	internalName = `src/lib/${MODULE_NAME}` + internalName.replace(/\\/g, "/");
	let co;
	let status = "? Pending";
	let success = false;
	try {
		// TODO: Support compile mode where we remove type annotations and docstrings
		co = Sk.compile(contents, internalName, "exec", true, true);
		status = "✔ Compiled";
		success = true;
	} catch (e) {
		status = "⚠ Failed to compile";
		console.log("Error while compiling: " + internalName);
		console.log(e);
		console.log(e.stack);
	}
	internalName = internalName.replace(/\.py$/, ".js");
	if (success) {
		contents = co.code + "\nvar $builtinmodule = " + co.funcname + ";";
		if (shouldMinify) {
			try {
				contents = minify_sync(contents).code;
				status = "✔ Compiled and Minified";
			} catch (e) {
				status = "⚠ Failed to minify";
				console.log("Error while minifying " + internalName);
				console.log(e);
				console.log(e.stack);
				success = false;
			}
		}
		ret[internalName] = contents;
	}
	result.push({
		status,
		internalName,
		success,
	});
	return result;
}

function processDirectories(dirs, recursive, exts, ret, minifyjs, excludes) {
	const results = [];
	dirs.forEach((dir) => {
		let files = fs.readdirSync(dir);

		files.forEach((file) => {
			let fullname = dir + "/" + file;

			if (!excludes.some((pattern) => pattern.test(fullname))) {
				let stat = fs.statSync(fullname);

				if (recursive && stat.isDirectory()) {
					results.push(
						...processDirectories(
							[fullname],
							recursive,
							exts,
							ret,
							minifyjs,
							excludes,
						),
					);
				} else if (stat.isFile()) {
					let ext = path.extname(file);
					if (exts.includes(ext)) {
						let contents = fs.readFileSync(fullname, "utf8");
						if (ext === ".py") {
							const result = buildPythonFile(
								ret,
								fullname,
								contents,
								minifyjs,
							);
							results.push(...result);
						}
					}
				}
			}
		});
	});
	return results;
}

const result = {};
console.log("Processing Drafter source code files...");
const processResults = processDirectories(
	[drafterPythonDir],
	true,
	[".py"],
	result,
	program.opts().minify,
	SKIP_FILES,
);
let output = [];
for (let filename in result) {
	let contents = result[filename];
	output.push(
		"Sk.builtinFiles.files['" +
			filename +
			"'] = " +
			JSON.stringify(contents),
	);
}
for (let extraFile of extraJavascriptModules) {
	const filePath = path.join(javascriptModulesDir, extraFile);
	const { code } = await precompileTypeScript(filePath, extraFile);
	const asJsPath = `src/lib/${MODULE_NAME}/${extraFile.replace(
		/\.ts$/,
		".js",
	)}`;
	output.push(
		"Sk.builtinFiles.files['" + asJsPath + "'] = " + JSON.stringify(code),
	);
	result[asJsPath] = code;
	processResults.push({
		status: "✔ Precompiled TypeScript",
		internalName: asJsPath,
	});
}
fs.writeFileSync(targetFilename, output.join("\n"), "utf8", { flag: "w" });

console.log("Process Results:");
for (let r of processResults) {
	console.log(r.status + ": " + r.internalName);
}
// Plus total count
console.log(`Total files processed: ${processResults.length}`);
console.log(
	`Total successful files: ${processResults.filter((r) => r.success).length}`,
);
console.log(
	`Total failed files: ${processResults.filter((r) => !r.success).length}`,
);
