// Small helper to resolve paths outside js/ into the Python package assets directory.
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function getRepoRoot() {
  // js/scripts/* -> js -> repo root
  return path.resolve(__dirname, "..", "..");
}

export function getAssetsDir() {
  const repoRoot = getRepoRoot();
  return path.join(repoRoot, "src", "drafter", "assets");
}

export function getAssetPath(...segments) {
  return path.join(getAssetsDir(), ...segments);
}

export default { getRepoRoot, getAssetsDir, getAssetPath };
