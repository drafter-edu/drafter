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

async function patchPythonFeatures() {
	await pyodide.runPythonAsync(`
import sys
import importlib.abc
import importlib.util
from pyodide.http import pyxhr

# This code allows Python code running in Pyodide to import modules from
# a remote server.
class RemoteLoader(importlib.abc.Loader):
    def __init__(self, source):
        self.source = source

    def exec_module(self, module):
        exec(self.source, module.__dict__)


class RemoteFinder(importlib.abc.MetaPathFinder):
    BASE_URL = ""

    def find_spec(self, fullname, path=None, target=None):
        module_name = fullname.split(".")[-1]
        url = f"{self.BASE_URL}/{module_name}.py"

        try:
            response = pyxhr.get(url)
            if response.status_code != 200:
                return None
            text = response.text

            loader = RemoteLoader(text)
            return importlib.util.spec_from_loader(fullname, loader)

        except Exception as e:
            return None


sys.meta_path.append(RemoteFinder())
	`);
}

export async function runStudentCode(
	options: DrafterInitOptions,
): Promise<any> {
	// TODO: Handle URL-based coding loading
	if ((window as any).pyodide === undefined) {
		throw new Error(
			"Pyodide is not initialized. Call setupPyodide() first.",
		);
	}
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
