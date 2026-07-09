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
import { confirmDialog } from "./dialogs";
import { clearDrafterSiteRoot, reportSystemError } from "./bridge/engine";
import { initializeRuntimeConfigurationOverrides } from "./config_overrides";
export { clearDrafterSiteRoot, reportSystemError } from "./bridge/engine";
export * from "./common.index";

window.DebugPanel = DebugPanel;
initializeRuntimeConfigurationOverrides();

const DRAFTER_CONFIG_FILENAME = "/_drafter_config.json";

function writeConfigFile(pyodide: any) {
	if ((window as any).DRAFTER_MODIFIED_CONFIGURATION) {
		try {
			pyodide.FS.writeFile(
				DRAFTER_CONFIG_FILENAME,
				JSON.stringify((window as any).DRAFTER_MODIFIED_CONFIGURATION),
			);
		} catch (error) {
			throw reportSystemError({
				id: "config.write_failed",
				category: "config",
				message: "Error writing Drafter configuration file",
				error,
				context: { phase: "setup" },
			});
		}
	}
}

const DEFAULT_MOCK_PACKAGES = [
	"watchfiles",
	"uvicorn[standard]",
	"uvicorn",
	"typer",
	"shellingham",
	"annotated-doc",
	"starlette",
	"rich",
];

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
	/** Root element this instance renders into. Defaults to "drafter-root--". */
	rootElementId?: string;
	/** Isolate this instance in a shadow root (default true unless set false). */
	useShadowDom?: boolean;
}

/** Handle for one live Drafter instance on the page. */
export interface DrafterInstanceHandle {
	rootElementId: string;
	/** Re-run this instance, optionally with new code. */
	restart: (code?: string) => Promise<void>;
	/** Tear down this instance's websocket and event listeners. */
	stop: () => void;
}

interface WindowWithDrafterInterruptBuffer extends Window {
	__drafterInterruptBuffer?: Int32Array;
}

async function resetPyodideRuntime(rootElementId: string) {
	const pyodide = (window as any).pyodide;
	if (pyodide === undefined) {
		return;
	}

	try {
		await pyodide.runPythonAsync(
			[
				"from drafter.client_server.commands import reset_server_for_root",
				`reset_server_for_root(${JSON.stringify(rootElementId)})`,
			].join("\n"),
		);
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Failed to reset server for root:",
			error,
		);
	}

	try {
		await pyodide.runPythonAsync(
			`from drafter.files.patch_pyodide import expire_remote_imports; expire_remote_imports()`,
		);
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Failed to expire remote imports:",
			error,
		);
	}

	clearDrafterSiteRoot(rootElementId);
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

/**
 * Create and start one Drafter instance rendering into `options.rootElementId`.
 *
 * All session state (websocket, restart token, current code, run-loop flags)
 * lives in this closure, so multiple instances can run concurrently on one page,
 * sharing the single Pyodide runtime. Each instance renders into its own root
 * element (and, by default, its own shadow root for isolation).
 */
export async function createDrafterInstance(
	options: AppServerPyodideOptions,
): Promise<DrafterInstanceHandle> {
	const rootElementId = options.rootElementId ?? "drafter-root--";
	const useShadowDom = options.useShadowDom;

	let latestStudentCode: string | null = null;
	let runInProgress = false;
	let restartRequested = false;
	let instanceWebSocket: WebSocket | null = null;

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
				await resetPyodideRuntime(rootElementId);
				const code = await getStudentCode();
				(window as any).__drafterCurrentCode = code;
				const executionOptions: DrafterInitOptions = {
					code,
					// Pass the RAW option (may be undefined) so the single-instance
					// back-compat path never triggers per-instance reconfiguration.
					rootElementId: options.rootElementId,
					useShadowDom,
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

	if (options.devWsUrl) {
		instanceWebSocket = new WebSocket(options.devWsUrl);
		instanceWebSocket.onmessage = (e) => {
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

	// Allow external callers (e.g. the in-browser code editor) to trigger a
	// restart with optionally new code by dispatching a custom window event.
	// A per-instance token ensures only events targeting THIS instance are
	// accepted; the dispatcher must include the token and (optionally) the
	// rootElementId so multiple instances don't all restart at once.
	const sessionToken = crypto.randomUUID();
	(window as any).__drafterRestartToken = sessionToken;

	const restartListener = (event: Event) => {
		const detail = (
			event as CustomEvent<{
				code?: string;
				_token?: string;
				rootElementId?: string;
			}>
		).detail;
		if (
			detail?.rootElementId !== undefined &&
			detail.rootElementId !== rootElementId
		) {
			return;
		}
		if (detail?._token !== sessionToken) {
			console.warn(
				"[Drafter] Ignoring drafter-restart-student-code event with invalid token.",
			);
			return;
		}
		if (typeof detail?.code === "string") {
			latestStudentCode = detail.code;
		} else {
			latestStudentCode = null;
		}
		runStudentExecution().catch((error) => {
			console.error(
				"[Drafter AppServer Scaffolding] Failed to restart student code via editor:",
				error,
			);
		});
	};
	window.addEventListener("drafter-restart-student-code", restartListener);

	await runStudentExecution();

	return {
		rootElementId,
		restart: async (code?: string) => {
			latestStudentCode = typeof code === "string" ? code : null;
			await runStudentExecution();
		},
		stop: () => {
			if (instanceWebSocket) {
				instanceWebSocket.close();
				instanceWebSocket = null;
			}
			window.removeEventListener(
				"drafter-restart-student-code",
				restartListener,
			);
		},
	};
}

/**
 * Back-compat entry point for the single-instance scaffolding. Starts one
 * instance on the default root and resolves once its initial run completes.
 */
export async function startPyodideAppServerSession(
	options: AppServerPyodideOptions,
): Promise<void> {
	await createDrafterInstance(options);
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
			throw reportSystemError({
				id: "runtime.pyodide_setup_failed",
				category: "runtime",
				message: "Error setting up Pyodide",
				error,
				context: { phase: "setup" },
			});
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
		throw reportSystemError({
			id: "runtime.drafter_mount_failed",
			category: "runtime",
			message: "Error mounting Drafter remotely",
			error,
			context: { phase: "setup" },
		});
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
			throw reportSystemError({
				id: "runtime.package_load_failed",
				category: "runtime",
				message: "Error loading packages automatically",
				error,
				context: { phase: "setup" },
			});
		}
	} else if (options.explicitPackageList) {
		// TODO: Handle the semicolon-separated list of packages
		const loaded = [];
		for (const pkg of options.explicitPackageList) {
			try {
				await pyodide.micropip.install(pkg);
				loaded.push(pkg);
			} catch (error) {
				throw reportSystemError({
					id: "runtime.package_install_failed",
					category: "runtime",
					message: `Error installing package \"${pkg}\"`,
					error,
					context: { phase: "setup" },
				});
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
		throw reportSystemError({
			id: "runtime.python_patch_failed",
			category: "runtime",
			message: "Error patching Python features",
			error,
			context: { phase: "setup" },
		});
	}
}

// Serializes student-code execution across all instances. Pyodide is single
// threaded and each run mutates shared global config (via configure_instance),
// so concurrent createDrafterInstance() calls (e.g. Promise.all) must not
// interleave their configure -> run critical sections. This chain guarantees
// each run completes fully before the next begins.
let executionChain: Promise<unknown> = Promise.resolve();

export function runStudentCode(options: DrafterInitOptions): Promise<any> {
	const result = executionChain.then(
		() => runStudentCodeInner(options),
		() => runStudentCodeInner(options),
	);
	executionChain = result.catch(() => undefined);
	return result;
}

async function runStudentCodeInner(options: DrafterInitOptions): Promise<any> {
	console.log("Running student code with options:", options);
	// TODO: Handle URL-based coding loading
	if ((window as any).pyodide === undefined) {
		throw new Error(
			"Pyodide is not initialized. Call setupPyodide() first.",
		);
	}

	// Only reconfigure when a root is explicitly requested (the multi-instance
	// path). The single-instance back-compat path leaves rootElementId undefined
	// so config/env defaults (root id, shadow DOM) are preserved exactly.
	if (options.rootElementId !== undefined) {
		const shadowArg =
			options.useShadowDom === undefined
				? "None"
				: options.useShadowDom
					? "True"
					: "False";
		try {
			await pyodide.runPythonAsync(
				[
					"from drafter.client_server.commands import configure_instance",
					`configure_instance(${JSON.stringify(
						options.rootElementId,
					)}, ${shadowArg})`,
				].join("\n"),
			);
		} catch (error) {
			throw reportSystemError({
				id: "runtime.instance_configure_failed",
				category: "runtime",
				message: "Error configuring Drafter instance",
				error,
				context: { phase: "setup", dom_id: options.rootElementId },
			});
		}
	}

	// For concurrent instances, run the student code in its own module namespace
	// so they don't share __main__ globals (route functions, State classes, etc.).
	// The single-instance path runs in the main globals exactly as before.
	const runOptions: { filename: string; globals?: any } = {
		filename: options?.studentFilename || "main.py",
	};
	if (options.rootElementId !== undefined) {
		runOptions.globals = pyodide.toPy({ __name__: "__main__" });
	}
	try {
		const result = await pyodide.runPythonAsync(options.code, runOptions);
		return result;
	} catch (error) {
		if (
			error instanceof Error &&
			error.message.includes("KeyboardInterrupt")
		) {
			console.info("Student code execution interrupted.");
			throw error;
		}
		throw reportSystemError({
			id: "runtime.student_code_failed",
			category: "runtime",
			message: "Error running student code",
			title: "Error",
			error,
			recoverable: true,
			context: { phase: "setup" },
		});
	}
}
