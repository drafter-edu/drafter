import { loadPyodide } from "pyodide";
import { mountDirectory } from "./pyodide_bridge/directories";
import { DebugPanel } from "./debug";
import type { DrafterInitOptions } from "./bridge/engine";
export { clearDrafterSiteRoot, handleSystemError } from "./bridge/engine";

window.DebugPanel = DebugPanel;

async function politelyAskUserForDirectory() {
    // Create a little permissions box to explain why we need access to the directory
    const permissionBox = document.createElement("div");
    permissionBox.style.position = "fixed";
    permissionBox.style.display = "flex";
    permissionBox.style.flexDirection = "column";
    permissionBox.style.alignItems = "center";
    permissionBox.style.justifyContent = "center";
    permissionBox.style.top = "50%";
    permissionBox.style.left = "50%";
    permissionBox.style.transform = "translate(-50%, -50%)";
    permissionBox.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
    permissionBox.style.backgroundColor = "#fff";
    permissionBox.style.border = "1px solid #ccc";
    permissionBox.style.padding = "10px";
    permissionBox.style.zIndex = "10000";
    permissionBox.innerHTML = `
        <p>Drafter needs access to your local Drafter directory in order to mount the local dev version of Pedal.</p>
        <button id="grant-permission-button">Grant Access</button>
    `;
    document.body.appendChild(permissionBox);

    return new Promise<void>((resolve) => {
        const button = document.getElementById(
            "grant-permission-button",
        ) as HTMLButtonElement;
        button.onclick = () => {
            document.body.removeChild(permissionBox);
            resolve();
        };
    });
}

export async function mountDrafterDirectory() {
    try {
        await mountDirectory("./drafter", "reuse-drafter-directory");
    } catch (error) {
        // Ask the user for permission and try again:
        await politelyAskUserForDirectory();
        await mountDirectory("./drafter", "reuse-drafter-directory");
    }
}

export async function mountDrafterRemote(url: string) {
    /*console.log("mountDrafterRemote is not implemented yet.");
    alert("mountDrafterRemote is not implemented yet.");*/
    let response = await fetch(url); // .zip, .whl, ...
    let buffer = await response.arrayBuffer();
    await pyodide.unpackArchive(buffer, "zip"); // by default, unpacks to the current dir
    pyodide.pyimport("drafter");
}

export async function setupPyodide() {
    if ((window as any).pyodide === undefined) {
        window.pyodide = (window as any).pyodide = await loadPyodide({
            packages: ["micropip"],
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/",
            env: {
                DRAFTER_CONFIG_FILE: "/_drafter_config.json",
            },
        });
        await window.pyodide.loadPackage("micropip");
        window.micropip = window.pyodide.pyimport("micropip");
        await window.micropip.install("bakery");
        writeConfigFile(pyodide);
    }
    return (window as any).pyodide;
}

function writeConfigFile(pyodide: any) {
    if ((window as any).DRAFTER_MODIFIED_CONFIGURATION) {
        pyodide.FS.writeFile(
            "/_drafter_config.json",
            JSON.stringify((window as any).DRAFTER_MODIFIED_CONFIGURATION),
        );
    }
}

export async function runStudentCode(
    options: DrafterInitOptions,
): Promise<any> {
    if ((window as any).pyodide === undefined) {
        throw new Error(
            "Pyodide is not initialized. Call setupPyodide() first.",
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
