import { defineConfig } from "tsup";
import browserslistToEsbuild from "browserslist-to-esbuild";
import * as fs from "fs";
import * as path from "path";
import postcss from "@chialab/esbuild-plugin-postcss";

const cssEntries: Record<string, string> = {};
const cssDir = path.resolve(__dirname, "src", "css");
for (const file of fs.readdirSync(cssDir)) {
    if (file.endsWith(".css")) {
        const name = path.basename(file, ".css");
        cssEntries[name] = path.join(cssDir, file);
    }
}

export default defineConfig([
    {
        entry: {
            "drafter.skulpt": "src/skulpt.index.ts",
        },
        format: ["iife"],
        globalName: "Drafter", // what gets attached to window.Drafter
        outDir: "dist/js",
        clean: false,
        target: browserslistToEsbuild(), // keep JS output aligned with your Browserslist
        outExtension({ format }) {
            return { js: ".js" }; // for iife this yields dist/drafter.js
        },
        esbuildOptions(options) {
            options.jsx = "automatic";
            options.jsxImportSource = "jsx-dom";
        },
        sourcemap: true,
        minify: true,
    },
    {
        entry: {
            "drafter.pyodide": "src/pyodide.index.ts",
        },
        format: ["iife"],
        globalName: "Drafter", // what gets attached to window.Drafter
        outDir: "dist/js",
        clean: false,
        target: browserslistToEsbuild(), // keep JS output aligned with your Browserslist
        outExtension({ format }) {
            return { js: ".js" }; // for iife this yields dist/drafter.js
        },
        esbuildOptions(options) {
            options.jsx = "automatic";
            options.jsxImportSource = "jsx-dom";
        },
        sourcemap: true,
        minify: true,
    },
    {
        entry: cssEntries,
        bundle: false,
        sourcemap: true,
        minify: true,
        clean: true,
        outDir: "dist/css",
        esbuildPlugins: [postcss()],
    },
]);
