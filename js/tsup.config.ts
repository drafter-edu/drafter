import { defineConfig } from "tsup";
import browserslistToEsbuild from "browserslist-to-esbuild";
import * as fs from "fs";
import * as path from "path";
import postcss from "@chialab/esbuild-plugin-postcss";

function findCssFiles(dir: string): Record<string, string> {
	const entries: Record<string, string> = {};
	for (const file of fs.readdirSync(dir)) {
		if (file.endsWith(".css")) {
			const name = path.basename(file, ".css");
			entries[name] = path.join(dir, file);
		}
	}
	return entries;
}

const cssEntries: Record<string, string> = {
	...findCssFiles(path.resolve(__dirname, "src", "css")),
	...findCssFiles(path.resolve(__dirname, "src", "css", "themes")),
};

export default defineConfig([
	{
		entry: {
			"drafter.skulpt": "src/skulpt.index.tsx",
		},
		format: ["iife"],
		globalName: "Drafter", // what gets attached to window.Drafter
		outDir: "dist/js",
		clean: false,
		target: browserslistToEsbuild(), // keep JS output aligned with your Browserslist
		outExtension({ format }) {
			return { js: ".js" }; // for iife this yields dist/drafter.js
		},
		// Third-party component CSS (e.g. Leaflet's) is imported as a
		// string and injected into the component's shadow root, since
		// document-level stylesheets can't reach shadow-DOM content.
		loader: { ".css": "text" },
		esbuildOptions(options) {
			options.jsx = "automatic";
			options.jsxImportSource = "jsx-dom";
		},
		sourcemap: true,
		minify: true,
	},
	{
		entry: {
			"drafter.pyodide": "src/pyodide.index.tsx",
		},
		format: ["iife"],
		globalName: "Drafter", // what gets attached to window.Drafter
		outDir: "dist/js",
		clean: false,
		target: browserslistToEsbuild(), // keep JS output aligned with your Browserslist
		outExtension({ format }) {
			return { js: ".js" }; // for iife this yields dist/drafter.js
		},
		loader: { ".css": "text" },
		esbuildOptions(options) {
			options.jsx = "automatic";
			options.jsxImportSource = "jsx-dom";
		},
		sourcemap: true,
		minify: true,
	},
	{
		entry: cssEntries,
		bundle: true,
		sourcemap: true,
		minify: true,
		clean: true,
		outDir: "dist/css",
		esbuildPlugins: [postcss()],
	},
]);
