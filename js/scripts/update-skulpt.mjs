// Copies Skulpt runtime files from SKULPT_DIR into the Python package assets
// directory so there is a single source of truth under src/drafter/assets.
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Paths
const root = path.resolve(__dirname, "..");
const repoRoot = path.resolve(__dirname, "..", "..");
const target = path.resolve(repoRoot, "src", "drafter", "assets", "js");
dotenv.config({ path: path.join(repoRoot, ".env") });

const skulptDir = process.env.SKULPT_DIR || "";

// Ensure target exists
fs.mkdirSync(target, { recursive: true });

// Helper
function copyFile(src, destDir) {
    const filename = path.basename(src);
    const dest = path.join(destDir, filename);
    fs.copyFileSync(src, dest);
    console.log(`✔ Copied ${filename} → ${path.relative(root, dest)}`);
}

if (skulptDir) {
    const files = [
        "skulpt.js",
        "skulpt.min.js",
        "skulpt-stdlib.js",
        "skulpt.js.map",
        "skulpt-stdlib.js.map",
    ];
    for (const fname of files) {
        const src = path.join(skulptDir, fname);
        if (!fs.existsSync(src)) {
            console.warn(`⚠ Skulpt file not found: ${src}`);
            continue;
        }
        copyFile(src, target);
        console.log(`ℹ File copied: ${fname}`);
    }
} else {
    console.warn("ℹ SKULPT_DIR not set; skipping Skulpt copy.");
}

console.log(`✅ Skulpt assets ready at ${path.relative(repoRoot, target)}.`);
