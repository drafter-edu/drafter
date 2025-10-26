// Copies built files from js/dist to src/drafter/assets so the Python dev server can serve fresh assets.
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const jsRoot = path.resolve(__dirname, "..");
const distDir = path.join(jsRoot, "dist");
const repoRoot = path.resolve(jsRoot, "..");
const assetsDir = path.join(repoRoot, "src", "drafter", "assets");

function ensureDir(dir) {
    fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, destDir) {
    const filename = path.basename(src);
    const dest = path.join(destDir, filename);
    fs.copyFileSync(src, dest);
    console.log(
        `✔ Copied ${path.relative(jsRoot, src)} → ${path.relative(
            repoRoot,
            dest
        )}`
    );
}

function main() {
    if (!fs.existsSync(distDir)) {
        console.error(`✖ dist directory not found: ${distDir}`);
        process.exit(1);
    }

    ensureDir(assetsDir);

    const entries = fs.readdirSync(distDir);
    let copied = 0;
    for (const name of entries) {
        const src = path.join(distDir, name);
        const stat = fs.statSync(src);
        if (stat.isFile()) {
            copyFile(src, assetsDir);
            copied += 1;
        }
    }

    if (copied === 0) {
        console.warn("ℹ No files copied from dist.");
    } else {
        console.log(
            `✅ Copied ${copied} file(s) to ${path.relative(
                repoRoot,
                assetsDir
            )}`
        );
    }
}

main();
