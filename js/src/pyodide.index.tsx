/**
 * Here is the list of all the things that have to be set up:
 *
 * 1) Load Pyodide
 * 2) Load Base Packages
 *   1) Load micropip
 *   2) Load system dependencies (e.g., Bakery, MatPlotLib, Pillow)
 * 3) Write the Drafter configuration file
 * 4) Mount Drafter (locally or from remote)
 * 5) Apply Drafter's patches
 *
 *
 * Then we can run student's code:
 * 1) Load any new packages detected from code or explicitly requested
 * 2) Execute student's code
 */

import { loadPyodide } from "pyodide";
import { mountDirectory } from "./pyodide_bridge/directories";
import { DebugPanel } from "./debug";
import type { DrafterInitOptions } from "./bridge/engine";
import { alertDialog, confirmDialog } from "./dialogs";
export { clearDrafterSiteRoot, handleSystemError } from "./bridge/engine";
export * from "./common.index";

window.DebugPanel = DebugPanel;

export async function mountDrafterDirectory() {
	try {
		await mountDirectory("./drafter", "reuse-drafter-directory");
	} catch (error) {
		let mountError: unknown = error;
		while (true) {
			const details =
				mountError instanceof Error
					? mountError.message
					: String(mountError);
			const shouldRetry = await confirmDialog(
				`Drafter needs access to your local Drafter directory to mount the local development version of Pedal.\n\nGrant access and retry?\n\n${details}`,
				{
					title: "Directory Access Required",
					confirmLabel: "Grant Access",
					cancelLabel: "Cancel",
					confirmVariant: "primary",
					modal: true,
					draggable: true,
					width: "560px",
				},
			);

			if (!shouldRetry) {
				throw mountError;
			}

			try {
				await mountDirectory("./drafter", "reuse-drafter-directory");
				return;
			} catch (retryError) {
				mountError = retryError;
			}
		}
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
			indexURL: options.pyodideUrl,
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

export async function setupEnvironment(packages: string[]) {
	const pyodide = (window as any).pyodide;
	if (options.loadPackagesAutomatically) {
		// TODO: Provide a nice loading indicator while packages are being loaded
		console.log("Automatically loading packages for student code...");
		const loadedPackages = await pyodide.loadPackagesFromImports(
			options.code,
		);
		console.log("Loaded packages:", loadedPackages);
	} else if (options.explicitPackageList) {
		// TODO: Handle the semicolon-separated list of packages
	}
	try {
		await patchPythonFeatures();
	} catch (error) {
		alertDialog(
			<div>
				Error setting up Python code runner: <pre>{"" + error}</pre>
			</div>,
			{
				title: "Error",
				modal: true,
				draggable: true,
				width: "560px",
			},
		);
		throw error;
	}
}

function writeConfigFile(pyodide: any) {
	if ((window as any).DRAFTER_MODIFIED_CONFIGURATION) {
		pyodide.FS.writeFile(
			"/_drafter_config.json",
			JSON.stringify((window as any).DRAFTER_MODIFIED_CONFIGURATION),
		);
	}
}

async function patchPythonFeatures() {
	await pyodide.runPythonAsync(`import drafter.files.patch_pyodide`);
}

export async function runStudentCode(
	options: DrafterInitOptions,
): Promise<any> {
	console.log("Running student code with options:", options);
	// TODO: Handle URL-based coding loading
	if ((window as any).pyodide === undefined) {
		throw new Error(
			"Pyodide is not initialized. Call setupPyodide() first.",
		);
	}

	try {
		const result = await pyodide.runPythonAsync(options.code, {
			filename: options?.studentFilename || "main.py",
		});
		return result;
	} catch (error) {
		alertDialog(
			<div>
				Error running student code: <pre>{"" + error}</pre>
			</div>,
			{
				title: "Error",
				modal: true,
				draggable: true,
				width: "560px",
			},
		);
		throw error;
	}
}
