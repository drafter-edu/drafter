import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import "../../src/drafter/assets/skulpt.js";
import { minify_sync } from "terser";
import { program } from "commander";
import { precompileTypeScript } from "./precompile-typescript.mjs";

program.option("-m, --minify", "minify the resulting code").parse(process.argv);

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Paths
const repoRoot = path.resolve(__dirname, "..", "..");

// Load env from repo root if present
dotenv.config({ path: path.join(repoRoot, ".env") });

const MODULE_NAME = "drafter";
const drafterPythonDir = path.resolve(repoRoot, "src", "drafter");
const target = path.resolve(repoRoot, "src", "drafter", "assets");
const targetFilename = path.resolve(target, "skulpt-drafter.js");
const skulptDir = process.env.SKULPT_DIR || "";
const javascriptModulesDir = path.resolve(repoRoot, "js", "src");
const extraJavascriptModules = ["bridge/client.ts"];

const SKIP_FILES = [new RegExp("app/.+"), new RegExp("bridge/client\\.py")];

Sk.configure({ __future__: Sk.python3 });

function buildPythonFile(ret, fullname, contents, shouldMinify) {
    var internalName = fullname;
    while (internalName.startsWith(drafterPythonDir)) {
        internalName = internalName.slice(drafterPythonDir.length);
    }
    internalName = `src/lib/${MODULE_NAME}` + internalName.replace(/\\/g, "/");
    let co;
    try {
        // TODO: Support compile mode where we remove type annotations and docstrings
        co = Sk.compile(contents, internalName, "exec", true, true);
        console.log("Compiled: " + internalName);
    } catch (e) {
        console.log("Failed to compile: " + internalName);
        console.log(e);
        console.log(e.stack);
    }
    internalName = internalName.replace(/\.py$/, ".js");
    contents = co.code + "\nvar $builtinmodule = " + co.funcname + ";";
    if (shouldMinify) {
        contents = minify_sync(contents).code;
    }
    ret[internalName] = contents;
}

function processDirectories(dirs, recursive, exts, ret, minifyjs, excludes) {
    dirs.forEach((dir) => {
        let files = fs.readdirSync(dir);

        files.forEach((file) => {
            let fullname = dir + "/" + file;

            if (!excludes.some((pattern) => pattern.test(fullname))) {
                let stat = fs.statSync(fullname);

                if (recursive && stat.isDirectory()) {
                    processDirectories(
                        [fullname],
                        recursive,
                        exts,
                        ret,
                        minifyjs,
                        excludes
                    );
                } else if (stat.isFile()) {
                    let ext = path.extname(file);
                    if (exts.includes(ext)) {
                        let contents = fs.readFileSync(fullname, "utf8");
                        if (ext === ".py") {
                            buildPythonFile(ret, fullname, contents, minifyjs);
                        }
                    }
                }
            }
        });
    });
}

const result = {};
processDirectories(
    [drafterPythonDir],
    true,
    ".py",
    result,
    program.opts().minify,
    SKIP_FILES
);
let output = [];
for (let filename in result) {
    let contents = result[filename];
    output.push(
        "Sk.builtinFiles.files['" +
            filename +
            "'] = " +
            JSON.stringify(contents)
    );
}
for (let extraFile of extraJavascriptModules) {
    const filePath = path.join(javascriptModulesDir, extraFile);
    const { code } = await precompileTypeScript(filePath, extraFile);
    const asJsPath = `src/lib/${MODULE_NAME}/${extraFile.replace(
        /\.ts$/,
        ".js"
    )}`;
    output.push(
        "Sk.builtinFiles.files['" + asJsPath + "'] = " + JSON.stringify(code)
    );
    result[asJsPath] = code;
}
fs.writeFileSync(targetFilename, output.join("\n"), "utf8", { flag: "w" });

console.log(Object.keys(result));
