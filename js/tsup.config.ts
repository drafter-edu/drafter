import { defineConfig } from "tsup";

export default defineConfig({
    entry: {
        drafter: "src/index.ts",
    },
    format: ["iife"], // or 'esm', 'cjs' if you want others
    globalName: "Drafter", // what gets attached to window.Drafter
    outDir: "dist",
    clean: true,
    outExtension({ format }) {
        return { js: ".js" }; // for iife this yields dist/drafter.js
    },
});
