import { loadPyodide } from "pyodide";
import { mountDirectory } from "./pyodide_bridge/directories";
import { DebugPanel } from "./debug";
import type { DrafterInitOptions } from "./bridge/engine";
export { clearDrafterSiteRoot, handleSystemError } from "./bridge/engine";

window.DebugPanel = DebugPanel;

export async function mountDrafterDirectory() {
    await mountDirectory("./drafter", "reuse-drafter-directory");
}

export async function setupPyodide() {
    if ((window as any).pyodide === undefined) {
        const pyodide = ((window as any).pyodide = await loadPyodide({
            packages: ["micropip"],
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/",
        }));
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install("bakery");
    }
    return (window as any).pyodide;
}

export async function runStudentCode(
    options: DrafterInitOptions
): Promise<any> {
    if ((window as any).pyodide === undefined) {
        throw new Error(
            "Pyodide is not initialized. Call setupPyodide() first."
        );
    }
    const pyodide = (window as any).pyodide;
    try {
        const result = await pyodide.runPythonAsync(options.code);
        return result;
    } catch (error) {
        throw error;
    }
}
