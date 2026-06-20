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
import { clearDrafterSiteRoot } from "./bridge/engine";
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

const DEFAULT_MOCK_PACKAGES = ["watchfiles", "uvicorn[standard]", "uvicorn"];

export function addMockPackages(packages: string[]) {
	if ((window as any).micropip) {
		for (const pkg of packages) {
			window.micropip.add_mock_package(pkg, "1.0.0");
		}
	}
}

interface PyodideSettings {
	pyodideUrl: string;
	systemPackages: string[];
}

interface AppServerPyodideOptions {
	devWsUrl?: string;
	pythonUrl?: string;
	inlineCode?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
}

interface WindowWithDrafterInterruptBuffer extends Window {
	__drafterInterruptBuffer?: Int32Array;
}

let appServerWebSocket: WebSocket | null = null;

async function resetPyodideRuntime() {
	const pyodide = (window as any).pyodide;
	if (pyodide === undefined) {
		return;
	}

	try {
		await pyodide.runPythonAsync(
			[
				"from drafter.client_server.commands import set_main_server",
				"set_main_server(None)",
			].join("\n"),
		);
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Failed to reset main server:",
			error,
		);
	}

	clearDrafterSiteRoot();
}

function interruptActiveRun() {
	const pyodide = (window as any).pyodide;
	if (pyodide === undefined) {
		return;
	}

	try {
		if (
			typeof SharedArrayBuffer !== "undefined" &&
			typeof Atomics !== "undefined"
		) {
			const stateWindow = window as WindowWithDrafterInterruptBuffer;
			if (
				!stateWindow.__drafterInterruptBuffer &&
				typeof pyodide?.setInterruptBuffer === "function"
			) {
				stateWindow.__drafterInterruptBuffer = new Int32Array(
					new SharedArrayBuffer(4),
				);
				pyodide.setInterruptBuffer(
					stateWindow.__drafterInterruptBuffer,
				);
			}

			if (stateWindow.__drafterInterruptBuffer) {
				Atomics.store(stateWindow.__drafterInterruptBuffer, 0, 2);
			}
		}
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Could not interrupt active run:",
			error,
		);
	}
}

async function fetchStudentCode(pythonUrl?: string): Promise<string> {
	if (!pythonUrl) {
		throw new Error(
			"Cannot fetch student code because pythonUrl was not provided.",
		);
	}
	const response = await fetch(`${pythonUrl}?t=${Date.now()}`, {
		cache: "no-store",
	});
	if (!response.ok) {
		throw new Error(
			`Failed to fetch student code: ${response.status} ${response.statusText}`,
		);
	}
	return response.text();
}

export async function startPyodideAppServerSession(
	options: AppServerPyodideOptions,
) {
	let latestStudentCode: string | null = null;
	let runInProgress = false;
	let restartRequested = false;

	const getStudentCode = async () => {
		if (latestStudentCode !== null) {
			return latestStudentCode;
		}
		if (typeof options.inlineCode === "string") {
			return options.inlineCode;
		}
		return fetchStudentCode(options.pythonUrl);
	};

	const runStudentExecution = async () => {
		if (runInProgress) {
			restartRequested = true;
			interruptActiveRun();
			return;
		}

		runInProgress = true;
		try {
			while (true) {
				restartRequested = false;
				await resetPyodideRuntime();
				const code = await getStudentCode();
				const executionOptions: DrafterInitOptions = {
					code,
					loadPackagesAutomatically:
						options.loadPackagesAutomatically,
					explicitPackageList: options.explicitPackageList,
				};

				try {
					await setupEnvironment(executionOptions);
					await runStudentCode(executionOptions);
				} catch (error) {
					// Interrupt-driven restarts are expected while live-editing.
					if (!restartRequested) {
						throw error;
					}
				}

				if (!restartRequested) {
					break;
				}
			}
		} finally {
			runInProgress = false;
		}
	};

	if (appServerWebSocket) {
		appServerWebSocket.close();
		appServerWebSocket = null;
	}

	if (options.devWsUrl) {
		appServerWebSocket = new WebSocket(options.devWsUrl);
		appServerWebSocket.onmessage = (e) => {
			const msg = JSON.parse(e.data);
			if (msg.type === "reload") {
				location.reload();
				return;
			}
			if (msg.type === "restart_student_code") {
				if (typeof msg.code === "string") {
					latestStudentCode = msg.code;
				} else {
					latestStudentCode = null;
				}
				runStudentExecution().catch((error) => {
					console.error(
						"[Drafter AppServer Scaffolding] Failed to restart student code:",
						error,
					);
				});
			}
		};
	}

	await runStudentExecution();
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
			// Load mock packages
			addMockPackages(DEFAULT_MOCK_PACKAGES);
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
		if (url.startsWith("drafter")) {
			await window.micropip.install(url, true);
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
		if (
			error instanceof Error &&
			error.message.includes("KeyboardInterrupt")
		) {
			console.info("Student code execution interrupted.");
			throw error;
		}
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
