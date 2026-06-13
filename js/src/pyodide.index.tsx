/**
 * Here is the list of all the things that have to be set up:
 *
 * 1) Load Pyodide
 *   1) Load micropip
 *   2) Load system dependencies (e.g., Bakery, MatPlotLib, Pillow)
 *   3) Write the Drafter configuration file
 * 2) Mount Drafter (locally or from remote)
 * 3) Apply Drafter's patches
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

const DRAFTER_CONFIG_FILENAME = "/_drafter_config.json";

function writeConfigFile(pyodide: any) {
	if ((window as any).DRAFTER_MODIFIED_CONFIGURATION) {
		try {
			pyodide.FS.writeFile(
				DRAFTER_CONFIG_FILENAME,
				JSON.stringify((window as any).DRAFTER_MODIFIED_CONFIGURATION),
			);
		} catch (error) {
			alertDialog(
				<div>
					Error writing Drafter configuration file:{" "}
					<pre>{"" + error}</pre>
				</div>,
				{
					title: "Error",
					modal: true,
					draggable: true,
					width: "560px",
				},
			);
			console.error("Error writing Drafter configuration file:", error);
			throw error;
		}
	}
}

interface PyodideSettings {
	pyodideUrl: string;
	systemPackages: string[];
}

export async function setupPyodide(options: PyodideSettings) {
	if ((window as any).pyodide === undefined) {
		try {
			// Load Pyodide itself
			window.pyodide = (window as any).pyodide = await loadPyodide({
				packages: ["micropip"],
				indexURL: options.pyodideUrl,
				env: {
					DRAFTER_CONFIG_FILE: DRAFTER_CONFIG_FILENAME,
				},
			});
			// Load micropip
			await window.pyodide.loadPackage("micropip");
			window.micropip = window.pyodide.pyimport("micropip");
			// Load system packages
			for (const pkg of options.systemPackages) {
				await window.micropip.install(pkg);
			}
			// Write Drafter configuration file
			writeConfigFile(window.pyodide);
		} catch (error) {
			alertDialog(
				<div>
					Error setting up Pyodide: <pre>{"" + error}</pre>
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
	return (window as any).pyodide;
}

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
	try {
		if (url === "drafter") {
			await window.micropip.install("drafter");
		} else {
			let response = await fetch(url); // .zip, .whl, ...
			let buffer = await response.arrayBuffer();
			await pyodide.unpackArchive(buffer, "zip"); // by default, unpacks to the current dir
			// This is the slowest step, would prefer to be using micropip to install
			pyodide.pyimport("drafter");
		}
	} catch (error) {
		alertDialog(
			<div>
				Error mounting Drafter remotely: <pre>{"" + error}</pre>
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

export async function setupEnvironment(options: DrafterInitOptions) {
	const pyodide = (window as any).pyodide;
	if (options.loadPackagesAutomatically) {
		// TODO: Provide a nice loading indicator while packages are being loaded
		console.log("Automatically loading packages for student code...");
		try {
			const loadedPackages = await pyodide.loadPackagesFromImports(
				options.code,
			);
			console.log("Loaded packages:", loadedPackages);
		} catch (error) {
			alertDialog(
				<div>
					Error loading packages automatically:{" "}
					<pre>{"" + error}</pre>
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
	} else if (options.explicitPackageList) {
		// TODO: Handle the semicolon-separated list of packages
		const loaded = [];
		for (const pkg of options.explicitPackageList) {
			try {
				await pyodide.micropip.install(pkg);
				loaded.push(pkg);
			} catch (error) {
				alertDialog(
					<div>
						Error installing package "{pkg}":{" "}
						<pre>{"" + error}</pre>
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
		console.log("Loaded explicit packages:", loaded);
	}
}

export async function patchPythonFeatures() {
	try {
		await pyodide.runPythonAsync(
			`import drafter.files.patch_pyodide as _PYODIDE_PATCHED_SUCCESSFULLY`,
		);
	} catch (error) {
		alertDialog(
			<div>
				Error patching Python features: <pre>{"" + error}</pre>
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
