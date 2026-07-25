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
import {
	getStoredConfigurationOverrides,
	initializeRuntimeConfigurationOverrides,
	syncWindowConfigurationOverrides,
} from "./config_overrides";
import { getPrinterConsole } from "./console/printer";
export { attachPrinterConsole, getPrinterConsole } from "./console/printer";
export { clearDrafterSiteRoot, reportSystemError } from "./bridge/engine";
export * from "./common.index";

window.DebugPanel = DebugPanel;
initializeRuntimeConfigurationOverrides();

const DRAFTER_CONFIG_FILENAME = "/_drafter_config.json";

export function toVirtualStudentPath(studentFilename?: string): string {
	const rawFilename = (studentFilename ?? "main.py").trim() || "main.py";
	return rawFilename.startsWith("/") ? rawFilename : `/${rawFilename}`;
}

function writeStudentCodeFile(
	pyodide: any,
	studentFilename: string | undefined,
	code: string,
) {
	const filePath = toVirtualStudentPath(studentFilename);
	const lastSlash = filePath.lastIndexOf("/");
	const parentDirectory = lastSlash > 0 ? filePath.slice(0, lastSlash) : "/";
	if (parentDirectory !== "/") {
		pyodide.FS.mkdirTree(parentDirectory);
	}
	pyodide.FS.writeFile(filePath, code);
}

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
	loadSlowly?: boolean;
}

interface AppServerPyodideOptions {
	/** How verbose the Pyodide runtime should be in terms of logging. */
	verbose: boolean;
	devWsUrl?: string;
	pythonUrl?: string;
	inlineCode?: string;
	studentFilename?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
	/** Root element this instance renders into. Defaults to "drafter-root--". */
	rootElementId?: string;
	/** Isolate this instance in a shadow root (default true unless set false). */
	useShadowDom?: boolean;
	/**
	 * The window this instance renders into (an iframe's contentWindow for
	 * embedded instances sharing this page's Pyodide runtime). Defaults to
	 * the global window.
	 */
	targetWindow?: Window;
	/**
	 * Unique key for this instance in the shared Python server registry.
	 * Required when several instances use the same rootElementId in separate
	 * iframe documents; defaults to rootElementId.
	 */
	instanceId?: string;
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

async function resetPyodideRuntime(
	instanceKey: string,
	rootElementId: string,
	targetDocument?: Document,
) {
	const pyodide = (window as any).pyodide;
	if (pyodide === undefined) {
		return;
	}

	try {
		await pyodide.runPythonAsync(
			[
				"from drafter.client_server.commands import reset_server_for_root",
				`reset_server_for_root(${JSON.stringify(instanceKey)})`,
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

	clearDrafterSiteRoot(rootElementId, targetDocument ?? document);
}

export function interruptActiveRun() {
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
				scheduleInterruptEscalation(
					stateWindow.__drafterInterruptBuffer,
					pyodide,
				);
			}
		}
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Could not interrupt active run:",
			error,
		);
	}
}

let interruptEscalationTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * The interrupt signal is only checked while Python bytecode is executing.
 * If it instead lands inside the event loop's own callback machinery (a
 * timer wakeup, a future's done-callback), that callback dies, the run's
 * coroutine is left suspended on a future nobody will ever complete, and no
 * Python ever runs again — so the signal sits unconsumed forever, the run's
 * promise never settles, and the runtime work queue is bricked behind it.
 *
 * Escalation closes that race: if the signal is still unconsumed after a
 * grace period (proof the loop went idle instead of raising into the run),
 * clear it and cancel the orphaned tasks directly so the run settles with
 * CancelledError. Callers treating "interrupted" should accept both
 * KeyboardInterrupt and CancelledError.
 */
function scheduleInterruptEscalation(buffer: Int32Array, pyodide: any) {
	if (interruptEscalationTimer !== null) {
		return;
	}
	interruptEscalationTimer = setTimeout(() => {
		interruptEscalationTimer = null;
		if (Atomics.load(buffer, 0) !== 2) {
			// Consumed: the normal interrupt path delivered KeyboardInterrupt.
			return;
		}
		// Clear the signal first so the cancel snippet below (and the next
		// legitimate run) is not itself killed at compile time.
		Atomics.store(buffer, 0, 0);
		pyodide
			.runPythonAsync(
				[
					"import asyncio",
					"for _drafter_task in asyncio.all_tasks() - {asyncio.current_task()}:",
					"    _drafter_task.cancel()",
				].join("\n"),
			)
			.catch((error: unknown) => {
				console.warn(
					"[Drafter AppServer Scaffolding] Interrupt escalation failed:",
					error,
				);
			});
	}, 1000);
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
	// Registry key in the shared Python runtime. Iframe-embedded instances all
	// use the same root id in their own documents, so they must supply a
	// unique instanceId to stay distinguishable.
	const instanceKey = options.instanceId ?? rootElementId;
	const targetDocument = options.targetWindow?.document;

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
				const code = await getStudentCode();
				(window as any).__drafterCurrentCode = code;
				const executionOptions: DrafterInitOptions = {
					code,
					studentFilename: options.studentFilename,
					// Pass the RAW option (may be undefined) so the single-instance
					// back-compat path never triggers per-instance reconfiguration.
					rootElementId: options.rootElementId,
					useShadowDom,
					targetWindow: options.targetWindow,
					instanceId: options.instanceId,
					loadPackagesAutomatically:
						options.loadPackagesAutomatically,
					explicitPackageList: options.explicitPackageList,
				};

				try {
					// One queue slot for the whole reset -> package-install ->
					// configure -> run critical section, so concurrent
					// instances can never interleave their setup phases.
					await enqueueRuntimeWork(async () => {
						await resetPyodideRuntime(
							instanceKey,
							rootElementId,
							targetDocument,
						);
						await setupEnvironment(executionOptions);
						return runStudentCodeInner(executionOptions);
					});
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

function yieldToBrowser(loadSlowly = false): Promise<void> {
	if (!loadSlowly) {
		return Promise.resolve();
	}
	// scheduler.yield() is not yet in TS's lib definitions.
	const scheduler = (globalThis as any).scheduler;
	if (scheduler?.yield) {
		return scheduler.yield();
	}

	return new Promise((resolve) => setTimeout(resolve, 0));
}

export async function setupPyodide(options: PyodideSettings, verbose = false) {
	const verboseLog = (...args: any[]) => {
		if (verbose) {
			console.log("[Drafter AppServer Scaffolding]", ...args);
		}
	};

	if ((window as any).pyodide === undefined) {
		verboseLog("Loading Pyodide with options:", options);
		try {
			// Load Pyodide itself
			window.pyodide = (window as any).pyodide = await loadPyodide({
				packages: ["micropip"],
				indexURL: options.pyodideUrl,
				env: {
					DRAFTER_CONFIG_FILE: DRAFTER_CONFIG_FILENAME,
				},
			});
			verboseLog(
				"Pyodide loaded successfully. Environment Variables:",
				window.pyodide?._module?.ENV,
			);
			// Route Python print()/stderr into the printer console instead of
			// Pyodide's default devtools sink (the console still mirrors every
			// line to devtools, so nothing is lost in any mode).
			const printerConsole = getPrinterConsole();
			window.pyodide.setStdout({
				batched: (line: string) =>
					printerConsole.recordOutput("stdout", `${line}\n`),
			});
			window.pyodide.setStderr({
				batched: (line: string) =>
					printerConsole.recordOutput("stderr", `${line}\n`),
			});
			// Arm the interrupt buffer up front (when cross-origin isolation
			// allows): registering it mid-execution makes the first
			// interruptActiveRun unreliable.
			if (
				typeof SharedArrayBuffer !== "undefined" &&
				typeof Atomics !== "undefined" &&
				typeof window.pyodide.setInterruptBuffer === "function"
			) {
				const interruptWindow =
					window as WindowWithDrafterInterruptBuffer;
				if (!interruptWindow.__drafterInterruptBuffer) {
					interruptWindow.__drafterInterruptBuffer = new Int32Array(
						new SharedArrayBuffer(4),
					);
				}
				window.pyodide.setInterruptBuffer(
					interruptWindow.__drafterInterruptBuffer,
				);
			}
			// Load micropip
			verboseLog("Loading micropip...");
			await window.pyodide.loadPackage("micropip");
			await yieldToBrowser(options.loadSlowly);
			window.micropip = window.pyodide.pyimport("micropip");
			// Load mock packages
			verboseLog("Adding mock packages:", DEFAULT_MOCK_PACKAGES);
			addMockPackages(DEFAULT_MOCK_PACKAGES);
			// Load system packages
			verboseLog("Installing system packages:", options.systemPackages);
			for (const pkg of options.systemPackages) {
				await window.micropip.install(pkg);
				await yieldToBrowser(options.loadSlowly);
			}
			// Write Drafter configuration file
			verboseLog("Writing Drafter configuration file...");
			writeConfigFile(window.pyodide);
			verboseLog("Pyodide setup complete.");
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

// Package specs already installed through this runtime, so several instances
// sharing it never re-request the same package. (loadPackagesFromImports has
// its own built-in tracking of loaded packages.)
const requestedPackageSpecs = new Set<string>();

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
			if (requestedPackageSpecs.has(pkg)) {
				continue;
			}
			try {
				await (window as any).micropip.install(pkg);
				requestedPackageSpecs.add(pkg);
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

// Serializes all work that touches the shared Pyodide interpreter: package
// installs, configure -> run critical sections, and instance teardown.
// Pyodide is single threaded and each run mutates shared global config (via
// configure_instance), so concurrent createDrafterInstance() calls (e.g. from
// several iframes attaching to one host) must not interleave. This chain
// guarantees each unit of work completes fully before the next begins.
let executionChain: Promise<unknown> = Promise.resolve();

/** Run `work` after all previously enqueued interpreter work has finished. */
export function enqueueRuntimeWork<T>(work: () => Promise<T>): Promise<T> {
	const result = executionChain.then(work, work);
	executionChain = result.catch(() => undefined);
	return result;
}

export function runStudentCode(options: DrafterInitOptions): Promise<any> {
	return enqueueRuntimeWork(() => runStudentCodeInner(options));
}

async function runStudentCodeInner(options: DrafterInitOptions): Promise<any> {
	console.log("Running student code with options:", options);
	// TODO: Handle URL-based coding loading
	if ((window as any).pyodide === undefined) {
		throw new Error(
			"Pyodide is not initialized. Call setupPyodide() first.",
		);
	}

	// A stale stop-signal aimed at the PREVIOUS run (e.g. a user mashing the
	// stop button as the run settled) must not kill this run at compile time.
	const interruptWindow = window as WindowWithDrafterInterruptBuffer;
	if (
		interruptWindow.__drafterInterruptBuffer &&
		typeof Atomics !== "undefined"
	) {
		Atomics.store(interruptWindow.__drafterInterruptBuffer, 0, 0);
	}

	// Only reconfigure when an instance is explicitly requested (the
	// multi-instance path). The single-instance back-compat path leaves these
	// options undefined so config/env defaults (root id, shadow DOM) are
	// preserved exactly.
	const isConfiguredInstance =
		options.rootElementId !== undefined ||
		options.instanceId !== undefined ||
		options.targetWindow !== undefined;
	// Each configured instance owns a subtree of the shared virtual filesystem
	// so concurrent instances never read or write each other's files.
	const instanceRoot = isConfiguredInstance
		? `/instances/${(
				options.instanceId ??
				options.rootElementId ??
				"drafter-root--"
			).replace(/[^A-Za-z0-9_-]/g, "-")}`
		: undefined;
	if (isConfiguredInstance) {
		const rootId = options.rootElementId ?? "drafter-root--";
		const shadowArg =
			options.useShadowDom === undefined
				? "None"
				: options.useShadowDom
					? "True"
					: "False";
		try {
			// The target window (an iframe's contentWindow) can't be encoded
			// in source text; hand it over through the interpreter globals.
			const hasTargetWindow = options.targetWindow !== undefined;
			if (hasTargetWindow) {
				pyodide.globals.set(
					"__drafter_instance_window",
					options.targetWindow,
				);
			}
			const windowArg = hasTargetWindow
				? "__drafter_instance_window"
				: "None";
			try {
				await pyodide.runPythonAsync(
					[
						"from drafter.client_server.commands import configure_instance",
						`configure_instance(${JSON.stringify(rootId)}, ${shadowArg}, ` +
							`js_window=${windowArg}, ` +
							`instance_id=${JSON.stringify(
								options.instanceId ?? rootId,
							)}, ` +
							`instance_root=${JSON.stringify(instanceRoot)})`,
					].join("\n"),
				);
			} finally {
				if (hasTargetWindow) {
					pyodide.globals.delete("__drafter_instance_window");
				}
			}
		} catch (error) {
			throw reportSystemError({
				id: "runtime.instance_configure_failed",
				category: "runtime",
				message: "Error configuring Drafter instance",
				error,
				context: { phase: "setup", dom_id: options.rootElementId },
				targetDocument: options.targetWindow?.document,
			});
		}
	}

	// For concurrent instances, run the student code in its own module namespace
	// so they don't share __main__ globals (route functions, State classes, etc.).
	// The single-instance path runs in the main globals exactly as before.
	const studentFilename = options?.studentFilename || "main.py";
	// Configured instances keep their code file inside their own FS subtree.
	const virtualFilename = instanceRoot
		? `${instanceRoot}/${studentFilename.replace(/^\/+/, "")}`
		: studentFilename;
	const codeToRun = options.code ?? "";
	try {
		writeStudentCodeFile(pyodide, virtualFilename, codeToRun);
	} catch (error) {
		throw reportSystemError({
			id: "runtime.student_code_write_failed",
			category: "runtime",
			message: "Error writing student code file",
			error,
			recoverable: true,
			context: { phase: "setup" },
		});
	}

	const runOptions: { filename: string; globals?: any } = {
		filename: virtualFilename,
	};
	if (isConfiguredInstance) {
		runOptions.globals = pyodide.toPy({ __name__: "__main__" });
	}
	try {
		const result = await pyodide.runPythonAsync(codeToRun, runOptions);
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
			targetDocument: options.targetWindow?.document,
			rootElementId: options.rootElementId,
		});
	}
}

/**
 * Boot settings for the shared runtime. Only the FIRST registration's
 * settings are used to boot; later registrations reuse the live runtime.
 * URL-ish fields must be absolute (embeds resolve their relative asset URLs
 * against their own document before registering, since the host page lives
 * at a different URL).
 */
export interface DrafterHostBootSettings {
	pyodideUrl: string;
	systemPackages?: string[];
	/** Absolute wheel/zip URL, or a "drafter==x.y.z" requirement. */
	drafterPath?: string;
	/** Dev-only: mount a local drafter working directory instead. */
	mountDrafterLocally?: boolean;
	verbose?: boolean;
	/** The embed's DRAFTER_MODIFIED_CONFIGURATION, written before boot. */
	modifiedConfiguration?: unknown;
}

/** What an embedded page hands to the host to run inside its own document. */
export interface DrafterHostRegistration {
	/** The embed's window (its iframe's contentWindow). */
	window: Window;
	/** Student code to run. */
	code: string;
	/** Runtime boot settings (used only if the runtime isn't booted yet). */
	bootSettings: DrafterHostBootSettings;
	/**
	 * Stable id for this embed (e.g. the compiled demo id). Keys the Python
	 * server registry and the embed's virtual-filesystem folder. Generated
	 * when omitted.
	 */
	instanceId?: string;
	studentFilename?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
	rootElementId?: string;
	/** Defaults to false: the iframe already encapsulates HTML/CSS. */
	useShadowDom?: boolean;
}

/**
 * One shared Pyodide runtime for every Drafter embed on a page.
 *
 * The host lives in the top-level page; each embedded iframe loads only the
 * (cheap, cached) JS bundle and registers itself here instead of booting its
 * own Pyodide. The iframe keeps HTML/CSS encapsulated in its own document,
 * while Python execution, installed packages, and sys.modules are shared.
 * Isolation between embeds comes from per-instance DOM contexts, module
 * namespaces, and virtual-filesystem subtrees, plus the runtime work queue
 * that serializes all interpreter access.
 */
export class DrafterHost {
	private runtimePromise: Promise<void> | null = null;
	private instances = new Map<string, DrafterInstanceHandle>();
	private instanceCounter = 0;

	/** Boot the shared runtime exactly once, even under concurrent attach. */
	private ensureRuntime(settings: DrafterHostBootSettings): Promise<void> {
		if (!this.runtimePromise) {
			this.runtimePromise = (async () => {
				if (settings.modifiedConfiguration !== undefined) {
					// The embed's compiled configuration must reach the Python
					// runtime's config file. The host page has no embedded
					// config of its own — its bundle initialized
					// DRAFTER_MODIFIED_CONFIGURATION to empty overrides at
					// load — so adopt the embed's as the embedded config and
					// re-merge any persisted debug overrides on top.
					(window as any).DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION =
						settings.modifiedConfiguration;
					syncWindowConfigurationOverrides(
						getStoredConfigurationOverrides(),
					);
				}
				await setupPyodide(
					{
						pyodideUrl: settings.pyodideUrl,
						systemPackages: settings.systemPackages ?? [],
					},
					settings.verbose ?? false,
				);
				if (settings.mountDrafterLocally) {
					await mountDrafterDirectory();
				} else if (settings.drafterPath) {
					await mountDrafterRemote(settings.drafterPath);
				}
				await patchPythonFeatures();
			})();
		}
		return this.runtimePromise;
	}

	/**
	 * Run an embed's code in the shared runtime, rendering into the embed's
	 * own document. Resolves once the embed's first page has rendered.
	 */
	async attach(
		registration: DrafterHostRegistration,
	): Promise<DrafterInstanceHandle> {
		const instanceId =
			registration.instanceId ??
			`drafter-embed-${++this.instanceCounter}`;
		if (this.instances.has(instanceId)) {
			// Same embed attaching again (e.g. its iframe was reloaded and
			// pagehide cleanup hasn't finished): tear the old one down first.
			await this.detach(instanceId);
		}
		await this.ensureRuntime(registration.bootSettings);
		const handle = await createDrafterInstance({
			verbose: registration.bootSettings.verbose ?? false,
			inlineCode: registration.code,
			studentFilename: registration.studentFilename,
			rootElementId: registration.rootElementId ?? "drafter-root--",
			useShadowDom: registration.useShadowDom ?? false,
			targetWindow: registration.window,
			instanceId,
			loadPackagesAutomatically: registration.loadPackagesAutomatically,
			explicitPackageList: registration.explicitPackageList,
		});
		this.instances.set(instanceId, handle);
		// Tear down when the embed's document goes away (reload or removal).
		registration.window.addEventListener(
			"pagehide",
			() => {
				void this.detach(instanceId);
			},
			{ once: true },
		);
		return handle;
	}

	/** Whether an embed with this id is currently attached and runnable. */
	has(instanceId: string): boolean {
		return this.instances.has(instanceId);
	}

	/**
	 * Restart an attached embed, optionally with new code. This is how
	 * external editors (e.g. the documentation's editable demos) push updated
	 * code into an embed running in the shared runtime.
	 */
	async restart(instanceId: string, code?: string): Promise<void> {
		const handle = this.instances.get(instanceId);
		if (!handle) {
			throw new Error(
				`No Drafter embed is attached with id "${instanceId}".`,
			);
		}
		await handle.restart(code);
	}

	/** Stop an embed and forget its server in the shared interpreter. */
	async detach(instanceId: string): Promise<void> {
		const handle = this.instances.get(instanceId);
		if (!handle) {
			return;
		}
		this.instances.delete(instanceId);
		handle.stop();
		const pyodide = (window as any).pyodide;
		if (pyodide === undefined) {
			return;
		}
		try {
			await enqueueRuntimeWork(() =>
				pyodide.runPythonAsync(
					[
						"from drafter.client_server.commands import reset_server_for_root",
						`reset_server_for_root(${JSON.stringify(instanceId)})`,
					].join("\n"),
				),
			);
		} catch (error) {
			console.warn(
				"[Drafter Host] Failed to reset server for detached instance:",
				error,
			);
		}
	}
}

let sharedHost: DrafterHost | null = null;

/**
 * The page's shared host, created on first use. Embedded iframes reach it as
 * `window.parent.Drafter?.getHost?.()` and fall back to a standalone boot
 * when it is unavailable (direct viewing, cross-origin, or an old bundle).
 */
export function getHost(): DrafterHost {
	if (!sharedHost) {
		sharedHost = new DrafterHost();
	}
	return sharedHost;
}
