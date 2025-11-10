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

// Add theme CSS files
const themesDir = path.join(cssDir, "themes");
if (fs.existsSync(themesDir)) {
    for (const file of fs.readdirSync(themesDir)) {
        if (file.endsWith(".css")) {
            const name = `themes/${path.basename(file, ".css")}`;
            cssEntries[name] = path.join(themesDir, file);
        }
    }
}

export default defineConfig([
    {
        entry: {
            drafter: "src/index.ts",
        },
        format: ["iife"], // or 'esm', 'cjs' if you want others
        globalName: "Drafter", // what gets attached to window.Drafter
        outDir: "dist/js",
        clean: true,
        target: browserslistToEsbuild(), // keep JS output aligned with your Browserslist
        outExtension({ format }) {
            return { js: ".js" }; // for iife this yields dist/drafter.js
        },
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
