import { createPyodideBridge } from "./bridge/client_pyodide";
import { DebugPanel } from "./debug";

declare global {
    interface Window {
        pyodide: any;
        loadPyodide: (config?: any) => Promise<any>;
    }
}

const preStyle = `background-color: #f0f0f0; padding: 4px; border: 1px solid lightgrey; margin: 0px`;

export async function setupPyodide() {
    if (typeof window.loadPyodide === "undefined") {
        console.error(
            "Pyodide loader not found. Ensure pyodide.js is loaded before drafter.js."
        );
        throw new Error("Pyodide loader not found");
    }

    if (!window.pyodide) {
        console.log("Loading Pyodide...");
        window.pyodide = await window.loadPyodide({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/",
        });
        console.log("Pyodide loaded successfully");
    }

    const pyodide = window.pyodide;

    // Set up environment variable to indicate we're in Pyodide
    await pyodide.runPythonAsync(`
        import os
        os.environ['DRAFTER_PYODIDE'] = '1'
    `);

    // Register the bridge module
    const bridgeModule = createPyodideBridge();
    pyodide.registerJsModule("drafter.bridge.client", bridgeModule);

    // Set up DebugPanel on window object for Pyodide bridge to access
    (window as any).Sk = { DebugPanel };

    console.log("Pyodide setup complete");
}

export async function startServerPyodide(
    pythonCode: string,
    mainFilename = "main",
    presentErrors = true
): Promise<void> {
    const pyodide = window.pyodide;
    if (!pyodide) {
        throw new Error("Pyodide not initialized. Call setupPyodide() first.");
    }

    try {
        // Run the Python code
        await pyodide.runPythonAsync(pythonCode);
        console.log("Python code executed successfully");
    } catch (error: any) {
        if (!presentErrors) {
            throw error;
        }
        showError(error, mainFilename + ".py", pythonCode);
    }
}

function showError(err: any, filenameExecuted: string, code: string) {
    console.error(err);
    const errorMessage = err.message || String(err);
    document.body.innerHTML = [
        "<h1>Error Running Site!</h1>",
        "<div>There was an error running your site. Here is the error message:</div>",
        `<div><pre style="${preStyle}">${errorMessage}</pre></div>`,
    ].join("\n");
}

export async function installPyodidePackage(packageName: string) {
    const pyodide = window.pyodide;
    if (!pyodide) {
        throw new Error("Pyodide not initialized");
    }
    
    console.log(`Installing package: ${packageName}`);
    await pyodide.loadPackage(packageName);
    console.log(`Package ${packageName} installed successfully`);
}
