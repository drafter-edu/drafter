/**
 * Here is the list of all the things that have to be set up:
 *
 * 1) Load Pyodide
 *   1) Load micropip
 *   2) Load system dependencies (e.g., Bakery, Pillow)
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
import { markDevServerDocument } from "./debug/dev_server";
import type { DrafterInitOptions } from "./bridge/engine";
import { closeDialog, confirmDialog } from "./dialogs";
import { clearDrafterSiteRoot, reportSystemError, installUncaughtErrorListeners } from "./bridge/engine";
import {
	installWithIndexes,
	normalizeProjectName,
	requirementName,
	type IndexInstallResult,
	type PackageRuntime,
} from "./package_index";
import {
	getStoredConfigurationOverrides,
	initializeRuntimeConfigurationOverrides,
	syncWindowConfigurationOverrides,
} from "./config_overrides";
import { getPrinterConsole } from "./console/printer";
import {
	connectLiveReload,
	type LiveReloadConnection,
	type LiveReloadSchedule,
} from "./live_reload";
// The Python that decides which imports and requirements are missing. It
// is carried inside this bundle (as text, run with exec) rather than
// imported from the drafter package in the browser, because the two can be
// different versions: the development server and the documentation demos
// install the published drafter wheel from PyPI, while this bundle comes
// from the local checkout.
import IMPORT_HELPERS_SOURCE from "../../src/drafter/helpers/imports.py";
// Carried as text for the same reason: gives a program drawn in an iframe a
// `js` that is that iframe's window.
import SCOPED_JS_SOURCE from "../../src/drafter/helpers/scoped_js.py";
export { attachPrinterConsole, getPrinterConsole } from "./console/printer";
export { clearDrafterSiteRoot, reportSystemError } from "./bridge/engine";
export * from "./common.index";

window.DebugPanel = DebugPanel;
initializeRuntimeConfigurationOverrides();

const DRAFTER_CONFIG_FILENAME = "/_drafter_config.json";

/**
 * Ids of the dialogs that report a run of the student's code that failed
 * (see `reportStudentSyntaxError` and `runStudentCodeInner`).
 */
const RUN_FAILURE_DIALOG_IDS = [
	"runtime.student_code_failed",
	"runtime.student_code_syntax_error",
];

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
	/**
	 * Overrides for how a lost live-reload connection is retried and when
	 * the retries stop (see `DEFAULT_LIVE_RELOAD_SCHEDULE`).
	 */
	liveReloadSchedule?: Partial<LiveReloadSchedule>;
	pythonUrl?: string;
	inlineCode?: string;
	studentFilename?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
	/** Wheel indexes (`wheels.json` URLs) searched when PyPI has no wheel. */
	packageIndexes?: string[];
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
// Number of student runs whose runPythonAsync has not settled yet.
let activeStudentRuns = 0;

/**
 * A stop-signal that was consumed by the interpreter but never raised into a
 * running coroutine stays "tripped" inside Python's signal machinery and is
 * raised as KeyboardInterrupt by whatever Python runs next, which would kill
 * the cancel snippet or an unrelated run at compile time. Run a no-op to
 * absorb it first. Never throws.
 */
async function drainPendingInterrupt(pyodide: any): Promise<void> {
	try {
		await pyodide.runPythonAsync("pass");
	} catch (error) {
		console.debug(
			"[Drafter AppServer Scaffolding] Absorbed a pending interrupt:",
			error,
		);
	}
}

/**
 * The interrupt signal is only checked while Python bytecode is executing.
 * If it instead lands inside the event loop's own callback machinery (a
 * timer wakeup, a future's done-callback), that callback dies, the run's
 * coroutine is left suspended on a future nobody will ever complete, and no
 * Python ever runs again — so the signal sits unconsumed forever, the run's
 * promise never settles, and the runtime work queue is bricked behind it.
 *
 * Since Pyodide 314 there is a second shape of the same failure: the signal
 * IS consumed (the buffer resets to 0) but the resulting KeyboardInterrupt is
 * never delivered into a coroutine that is only ever resumed by event-loop
 * timer callbacks — it stays pending until the next runPythonAsync call.
 * The run keeps spinning and its promise never settles.
 *
 * Escalation closes both races: if, after a grace period, the signal is
 * still unconsumed OR a student run is still active, drain any pending
 * KeyboardInterrupt and cancel the orphaned tasks directly so the run
 * settles with CancelledError. Callers treating "interrupted" should accept
 * both KeyboardInterrupt and CancelledError.
 */
function scheduleInterruptEscalation(buffer: Int32Array, pyodide: any) {
	if (interruptEscalationTimer !== null) {
		return;
	}
	interruptEscalationTimer = setTimeout(() => {
		interruptEscalationTimer = null;
		const unconsumed = Atomics.load(buffer, 0) === 2;
		if (!unconsumed && activeStudentRuns === 0) {
			// Consumed and the run settled: the normal interrupt path
			// delivered KeyboardInterrupt.
			return;
		}
		// Clear the signal first so the cancel snippet below (and the next
		// legitimate run) is not itself killed at compile time.
		Atomics.store(buffer, 0, 0);
		void (async () => {
			try {
				await drainPendingInterrupt(pyodide);
				await pyodide.runPythonAsync(
					[
						"import asyncio",
						"for _drafter_task in asyncio.all_tasks() - {asyncio.current_task()}:",
						"    _drafter_task.cancel()",
					].join("\n"),
				);
			} catch (error) {
				console.warn(
					"[Drafter AppServer Scaffolding] Interrupt escalation failed:",
					error,
				);
			}
		})();
	}, 1000);
}

interface StudentSyntaxProblem {
	errorName: string;
	message: string;
	lineno: number | null;
	text: string;
	formatted: string;
}

const SYNTAX_CHECK_SNIPPET = `
import ast as _ast
import json as _json
import traceback as _traceback

def _drafter_check_syntax(source, filename):
    try:
        compile(source, filename, "exec", flags=_ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    except SyntaxError as exc:
        return _json.dumps({
            "ok": False,
            "error_name": type(exc).__name__,
            "message": exc.msg or "invalid syntax",
            "lineno": exc.lineno,
            "text": (exc.text or "").strip(),
            "formatted": "".join(_traceback.format_exception_only(exc)).rstrip(),
        })
    return _json.dumps({"ok": True})

_drafter_check_syntax(__drafter_syntax_source, __drafter_syntax_filename)
`;

/**
 * Compile-check student code without executing it, so a restart can refuse
 * to tear down a working site for code that cannot even start. Returns the
 * problem details when the code fails to compile, or null when it compiles.
 * The guard fails open: if the check itself cannot run, null is returned
 * and the normal execution path reports whatever is actually wrong.
 */
async function checkStudentCodeSyntax(
	code: string,
	filename: string,
): Promise<StudentSyntaxProblem | null> {
	const pyodide = (window as any).pyodide;
	if (pyodide === undefined) {
		return null;
	}
	// PyCF_ALLOW_TOP_LEVEL_AWAIT mirrors runPythonAsync's own compile flags,
	// so the check never rejects code the real run would accept.
	const checkGlobals = pyodide.toPy({
		__drafter_syntax_source: code,
		__drafter_syntax_filename: filename,
	});
	try {
		const resultJson = await pyodide.runPythonAsync(SYNTAX_CHECK_SNIPPET, {
			globals: checkGlobals,
		});
		const result = JSON.parse(resultJson);
		if (result.ok) {
			return null;
		}
		return {
			errorName: result.error_name,
			message: result.message,
			lineno: result.lineno ?? null,
			text: result.text ?? "",
			formatted:
				result.formatted ?? `${result.error_name}: ${result.message}`,
		};
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Syntax pre-check could not run:",
			error,
		);
		return null;
	} finally {
		checkGlobals.destroy?.();
	}
}

/**
 * Report a syntax problem caught by the pre-flight check. When a previous
 * run is still on screen (`keptPreviousRun`), the report is recoverable and
 * presents as a dialog over the still-working site; on a first run there is
 * nothing to preserve, so it renders a friendly error page into the root.
 */
function reportStudentSyntaxError(
	problem: StudentSyntaxProblem,
	options: DrafterInitOptions,
	filename: string,
	keptPreviousRun: boolean,
): Error {
	const syntaxError = new Error(problem.formatted);
	syntaxError.name = problem.errorName;
	const location =
		problem.lineno !== null
			? `line ${problem.lineno} of ${filename}`
			: filename;
	return reportSystemError({
		id: "runtime.student_code_syntax_error",
		category: "runtime",
		message: `Your code has a syntax error (${problem.errorName}: ${problem.message})`,
		title: "Syntax Error",
		error: syntaxError,
		recoverable: keptPreviousRun,
		friendlyMessage: keptPreviousRun
			? "Your latest code has a syntax error, so Drafter is still showing the last working version of your site."
			: "Drafter could not start your site because the code has a syntax error.",
		friendlySteps: [
			problem.text
				? `Look at ${location}: \`${problem.text}\``
				: `Look at ${location}.`,
			"Check punctuation first: missing colons, commas, quotes, or parentheses.",
			keptPreviousRun
				? "Fix the code and save or run it again; your site will restart automatically."
				: "Fix the code and run it again.",
		],
		context: { phase: "setup", dom_id: options.rootElementId },
		targetDocument: options.targetWindow?.document,
		rootElementId: options.rootElementId,
	});
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
	// Only the development server hands out a live-reload socket, so its
	// presence is what lets the debug panel offer to stop that server.
	if (options.devWsUrl) {
		markDevServerDocument(targetDocument ?? document);
	}
	// Errors that escape to the browser (in this window and in an embedded
	// instance's own window) reach the debug panel too.
	installUncaughtErrorListeners(window);
	if (options.targetWindow && options.targetWindow !== window) {
		installUncaughtErrorListeners(options.targetWindow);
	}

	let latestStudentCode: string | null = null;
	let runInProgress = false;
	let restartRequested = false;
	let hasCompletedRun = false;
	// Whether this instance's last run ended in an error dialog that is
	// still open. A later run that succeeds closes it: the dialog describes
	// code that is no longer what is running.
	let failureDialogMayBeOpen = false;
	let liveReload: LiveReloadConnection | null = null;

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
					packageIndexes: options.packageIndexes,
				};

				try {
					// One queue slot for the whole reset -> package-install ->
					// configure -> run critical section, so concurrent
					// instances can never interleave their setup phases.
					await enqueueRuntimeWork(async () => {
						// Guard: refuse to tear down a working site for code
						// that cannot compile. Checking BEFORE the reset means
						// a syntax error while live-editing (or a partially
						// saved file) leaves the previous version running.
						const displayFilename =
							options.studentFilename || "main.py";
						const syntaxProblem = await checkStudentCodeSyntax(
							code,
							displayFilename,
						);
						if (syntaxProblem) {
							throw reportStudentSyntaxError(
								syntaxProblem,
								executionOptions,
								displayFilename,
								hasCompletedRun,
							);
						}
						await resetPyodideRuntime(
							instanceKey,
							rootElementId,
							targetDocument,
						);
						await setupEnvironment(executionOptions);
						return runStudentCodeInner(executionOptions);
					});
					hasCompletedRun = true;
					if (failureDialogMayBeOpen) {
						failureDialogMayBeOpen = false;
						RUN_FAILURE_DIALOG_IDS.forEach((id) => closeDialog(id));
					}
				} catch (error) {
					// Interrupt-driven restarts are expected while live-editing.
					if (!restartRequested) {
						failureDialogMayBeOpen = true;
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
		// The connection looks after itself: when the program stops it
		// retries, and it reloads this tab once the program is running
		// again (see live_reload.ts).
		liveReload = connectLiveReload({
			url: options.devWsUrl,
			schedule: options.liveReloadSchedule,
			onMessage: (msg) => {
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
			},
		});
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
			// A deliberate close: nothing is retried and no notice is shown.
			if (liveReload) {
				liveReload.close();
				liveReload = null;
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

/**
 * How browsers, Pyodide, and micropip word a download that did not arrive:
 * Chrome ("Failed to fetch", also for dynamic imports), Firefox ("error
 * loading dynamically imported module", "NetworkError"), Safari ("Importing
 * a module script failed", "Load failed"), Pyodide ("Failed to load '...':
 * request failed."), and micropip ("Can't fetch ...").
 */
const DOWNLOAD_FAILURE_PATTERN =
	/failed to fetch|error loading dynamically imported module|importing a module script failed|networkerror|load failed|request failed|can't fetch/i;

/** The host a URL points at, or null when it names no other server. */
function externalHostOf(url: string | undefined): string | null {
	if (!url || !/^https?:\/\//i.test(url)) {
		return null;
	}
	try {
		return new URL(url).host || null;
	} catch {
		return null;
	}
}

/**
 * Student-facing explanation for a Pyodide setup failure caused by a
 * download that did not arrive (offline, a blocked CDN, or a stale cached
 * copy of Drafter asking for a file that no longer exists). Returns an
 * empty object for any other failure, leaving the generic setup text.
 */
function explainPyodideDownloadFailure(
	error: unknown,
	pyodideUrl: string,
): { friendlyMessage?: string; friendlySteps?: string[] } {
	const text = error instanceof Error ? error.message : String(error);
	if (!DOWNLOAD_FAILURE_PATTERN.test(text)) {
		return {};
	}
	// Prefer the server named in the error itself (the file that failed)
	// over the configured Pyodide location.
	const failedUrl = /https?:\/\/[^\s'"`)]+/i.exec(text)?.[0];
	const host = externalHostOf(failedUrl) ?? externalHostOf(pyodideUrl);
	const blocked = host ? `\`${host}\`` : "the download";
	return {
		friendlyMessage:
			"Drafter could not download the files it needs to run Python in your browser. This is a connection or browser problem, not a mistake in your code.",
		friendlySteps: [
			"Check that this computer is connected to the internet.",
			"Reload this page with a hard refresh (Ctrl+Shift+R on Windows or Linux, Cmd+Shift+R on a Mac), so the browser downloads fresh copies instead of reusing saved ones.",
			`If it still fails, your network may be blocking ${blocked} (some school and work networks do). Try a different network, or show the technical details to your instructor.`,
		],
	};
}

/**
 * Python that replaces the built-in `input` with one that asks its question
 * in the browser's prompt box. Left alone, Pyodide reads `input()` from a
 * prompt box with nothing in it and writes the question to the output
 * instead, so the visitor is asked for an answer without seeing what is
 * being asked. Cancelling the box gives an empty string.
 *
 * The snippet imports nothing from drafter, so it works with whichever
 * drafter version the browser has installed. `js.prompt` is looked up on
 * each call rather than once.
 */
const BROWSER_INPUT_SNIPPET = `
def _drafter_install_input():
    import builtins
    import js

    def input(prompt="", /):
        """Ask for a line of text in the browser's prompt box.

        The prompt box shows \`prompt\`. Cancelling it gives an empty string.
        """
        answer = js.prompt(str(prompt))
        return answer if isinstance(answer, str) else ""

    builtins.input = input

_drafter_install_input()
del _drafter_install_input
`;

/**
 * Make Python's `input(question)` show the question (see
 * `BROWSER_INPUT_SNIPPET`). A failure leaves Pyodide's own `input` in place
 * and is only logged: nothing else depends on it.
 */
function installBrowserInput(pyodide: any): void {
	try {
		pyodide.runPython(BROWSER_INPUT_SNIPPET);
	} catch (error) {
		console.warn(
			"[Drafter AppServer Scaffolding] Could not set up input():",
			error,
		);
	}
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
			// input("question") asks its question in the prompt box.
			installBrowserInput(window.pyodide);
			verboseLog("Pyodide setup complete.");
		} catch (error) {
			throw reportSystemError({
				id: "runtime.pyodide_setup_failed",
				category: "runtime",
				message: "Error setting up Pyodide",
				error,
				...explainPyodideDownloadFailure(error, options.pyodideUrl),
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

// Imports that could not be installed automatically. They are not retried
// on every re-run (live editing re-runs setup on each save); reloading the
// page tries again.
const failedAutomaticInstalls = new Set<string>();

/**
 * Python that defines the import helpers (drafter/helpers/imports.py, carried
 * in this bundle) in the snippet's own namespace, then runs `body`, whose
 * value is the snippet's result.
 */
function importHelperSnippet(body: string): string {
	return `
import json as _json
_helpers = {}
exec(__drafter_import_helpers, _helpers)
${body}
`;
}

const SCOPED_JS_SNIPPET = `
_scoped_js = {}
exec(__drafter_scoped_js_source, _scoped_js)
__drafter_program_globals["__builtins__"] = _scoped_js["make_scoped_builtins"](
    __drafter_program_window
)
`;

/**
 * Make `import js` inside one program mean the window that program is drawn
 * in, instead of the window that hosts the shared interpreter.
 *
 * A program embedded through an iframe (a documentation demo) shares the
 * hosting page's interpreter, where `js` is the hosting page. Without this,
 * `js.document.getElementById(...)` in a demo searches the page around it
 * and never finds the demo's own elements. Only the program's own code is
 * affected; Drafter's `import js` is unchanged.
 *
 * Fails open: if the scoping cannot be set up, the program still runs, with
 * `js` as the hosting page, and the problem is logged.
 *
 * @param pyodide The shared interpreter.
 * @param programGlobals The Python dict the program's code will run in.
 * @param targetWindow The window the program is drawn in.
 */
export function scopeJsToWindow(
	pyodide: any,
	programGlobals: any,
	targetWindow: Window,
): void {
	let scratch: any;
	try {
		scratch = pyodide.toPy({ __drafter_scoped_js_source: SCOPED_JS_SOURCE });
		scratch.set("__drafter_program_globals", programGlobals);
		scratch.set("__drafter_program_window", targetWindow);
		pyodide.runPython(SCOPED_JS_SNIPPET, { globals: scratch });
	} catch (error) {
		console.warn(
			"[Drafter] Could not give this embedded program its own `js`; " +
				"`import js` will mean the hosting page.",
			error,
		);
	} finally {
		scratch?.destroy?.();
	}
}

const MISSING_IMPORTS_SNIPPET = importHelperSnippet(
	`_json.dumps(_helpers["find_missing_imports"](__drafter_import_source))`,
);

const IMPORTED_MODULES_SNIPPET = importHelperSnippet(
	`_json.dumps(_helpers["find_imported_modules"](__drafter_import_source))`,
);

/**
 * Run one of the import-helper snippets over student code and return the
 * module names it lists. Fails open: if the snippet cannot run, the problem
 * is logged with `failureNote` and no names are returned.
 */
async function listImports(
	pyodide: any,
	snippet: string,
	code: string,
	failureNote: string,
): Promise<string[]> {
	if (typeof pyodide?.runPythonAsync !== "function" || !pyodide.toPy) {
		return [];
	}
	const checkGlobals = pyodide.toPy({
		__drafter_import_helpers: IMPORT_HELPERS_SOURCE,
		__drafter_import_source: code,
	});
	try {
		const result = await pyodide.runPythonAsync(snippet, {
			globals: checkGlobals,
		});
		const names = JSON.parse(result);
		return Array.isArray(names) ? names.map(String) : [];
	} catch (error) {
		console.warn(failureNote, error);
		return [];
	} finally {
		checkGlobals.destroy?.();
	}
}

/**
 * The imports in student code that nothing can provide yet: not the standard
 * library, not an installed package, and not one of the student's own files
 * (which the remote-module finder supplies). The decision is made in Python
 * (drafter.helpers.imports, bundled here) by the real import machinery.
 * Fails open: if the check cannot run, no imports are reported and the
 * program runs as it would have before.
 */
function findMissingImports(pyodide: any, code: string): Promise<string[]> {
	return listImports(
		pyodide,
		MISSING_IMPORTS_SNIPPET,
		code,
		"[Drafter] Could not check for libraries to install automatically:",
	);
}

const MISSING_REQUIREMENTS_SNIPPET = importHelperSnippet(
	`_json.dumps(_helpers["find_missing_requirements"](list(__drafter_distributions)))`,
);

const INSTALLED_DISTRIBUTIONS_SNIPPET = `
import json as _json
import importlib.metadata as _md
_json.dumps(sorted({_d.metadata["Name"] for _d in _md.distributions() if _d.metadata["Name"]}))
`;

/**
 * The live runtime as the wheel-index code sees it: micropip for installs
 * and Python's own package metadata for what is installed and what the
 * installed packages still need.
 */
function packageRuntime(pyodide: any, micropip: any): PackageRuntime {
	return {
		async install(specs, deps) {
			if (typeof micropip.install?.callKwargs === "function") {
				await micropip.install.callKwargs(specs, { deps });
			} else {
				await micropip.install(specs);
			}
		},
		async missingRequirements(distributions) {
			if (typeof pyodide?.runPythonAsync !== "function" || !pyodide.toPy) {
				return [];
			}
			const globals = pyodide.toPy({
				__drafter_import_helpers: IMPORT_HELPERS_SOURCE,
				__drafter_distributions: distributions,
			});
			try {
				const result = await pyodide.runPythonAsync(
					MISSING_REQUIREMENTS_SNIPPET,
					{ globals },
				);
				const names = JSON.parse(result);
				return Array.isArray(names) ? names.map(String) : [];
			} catch (error) {
				console.warn(
					"[Drafter] Could not check what the installed packages still need:",
					error,
				);
				return [];
			} finally {
				globals.destroy?.();
			}
		},
		async installedDistributions() {
			if (typeof pyodide?.runPythonAsync !== "function") {
				return new Set<string>();
			}
			try {
				const names = JSON.parse(
					await pyodide.runPythonAsync(INSTALLED_DISTRIBUTIONS_SNIPPET),
				);
				return new Set(
					(Array.isArray(names) ? names : []).map((name: unknown) =>
						String(name).trim().toLowerCase().replace(/[-_.]+/g, "-"),
					),
				);
			} catch {
				return new Set<string>();
			}
		},
	};
}

/**
 * Install one requirement: from PyPI, or from a wheel index that has it when
 * PyPI cannot supply it (see package_index.ts). Logs what the index provided.
 */
async function installPackage(
	spec: string,
	indexes: string[],
): Promise<IndexInstallResult> {
	const pyodide = (window as any).pyodide;
	const micropip = (window as any).micropip;
	const result = await installWithIndexes(
		packageRuntime(pyodide, micropip),
		spec,
		indexes,
	);
	if (result.index) {
		console.log(
			`Installed ${spec} from the wheel index ${result.index}:`,
			result.wheels.map((url) => url.split("/").pop()),
			result.requirements.length > 0
				? `plus ${result.requirements.join(", ")}`
				: "",
		);
	}
	return result;
}

/**
 * Imports that an automatic install filled from PyPI by name alone: the
 * project did not list the library and Pyodide does not ship it, so the
 * name on the `import` line was looked up on PyPI and whatever is published
 * under that name was installed. That is what the student wants for
 * `import seaborn`. It is not what they want when `helpers` was meant to be
 * their own `helpers.py` and the file is missing from the site: PyPI has an
 * unrelated package called `helpers`, and the program then fails inside a
 * library the student has never heard of. The names are remembered for the
 * life of the page (the library stays installed that long) so each run can
 * say what happened; see `reportImportsFilledFromPyPI` and
 * `explainImportFilledFromPyPI`.
 */
const automaticPyPIInstalls = new Set<string>();

/** What micropip records in `pyodide.loadedPackages` for Pyodide's own packages. */
const PYODIDE_PACKAGE_CHANNEL = "default channel";

/**
 * Whether the library came with Pyodide rather than from PyPI: micropip
 * serves a request from Pyodide's own distribution when it can.
 */
function cameWithPyodide(pyodide: any, name: string): boolean {
	const loaded: unknown = pyodide?.loadedPackages;
	if (loaded === null || typeof loaded !== "object") {
		return false;
	}
	const wanted = normalizeProjectName(name);
	return Object.entries(loaded as Record<string, unknown>).some(
		([project, channel]) =>
			normalizeProjectName(project) === wanted &&
			channel === PYODIDE_PACKAGE_CHANNEL,
	);
}

/**
 * Try to install each library the student imports that Pyodide's own
 * package loading did not provide (seaborn is the usual example): from
 * PyPI, then from the wheel indexes. A library that cannot be installed is
 * skipped quietly: its import then fails in the student's program with the
 * ordinary ModuleNotFoundError, whose error page explains what to do.
 *
 * An import that PyPI filled is remembered, unless the project declared the
 * library itself (`declaredPackages`, the project's package list) or
 * Pyodide ships it, so the student can be told where it came from.
 */
export async function installMissingImports(
	code: string,
	indexes: string[] = [],
	declaredPackages: string[] = [],
): Promise<string[]> {
	const pyodide = (window as any).pyodide;
	const micropip = (window as any).micropip;
	if (!micropip) {
		return [];
	}
	const declared = new Set(
		declaredPackages.map((spec) => requirementName(spec) ?? spec),
	);
	const installed: string[] = [];
	for (const name of await findMissingImports(pyodide, code)) {
		if (requestedPackageSpecs.has(name) || failedAutomaticInstalls.has(name)) {
			continue;
		}
		try {
			const result = await installPackage(name, indexes);
			requestedPackageSpecs.add(name);
			installed.push(name);
			if (
				result.index === null &&
				!declared.has(normalizeProjectName(name)) &&
				!cameWithPyodide(pyodide, name)
			) {
				automaticPyPIInstalls.add(name);
				console.warn(
					`[Drafter] Your program imports "${name}" and no ${name}.py was found with it, so the library named "${name}" was installed from PyPI.`,
				);
			}
		} catch (error) {
			failedAutomaticInstalls.add(name);
			console.warn(
				`[Drafter] Could not install "${name}" automatically:`,
				error,
			);
		}
	}
	if (installed.length > 0) {
		console.log("Installed missing libraries:", installed);
	}
	return installed;
}

/**
 * After a run that started, tell the debug panel about each import of the
 * program that PyPI filled (see `automaticPyPIInstalls`). This waits for
 * the run because the debug panel that shows the warning is built by the
 * run itself. It is said again on every run for as long as the program
 * still imports the library. Never throws.
 */
async function reportImportsFilledFromPyPI(
	pyodide: any,
	code: string,
	options: DrafterInitOptions,
): Promise<void> {
	if (automaticPyPIInstalls.size === 0) {
		return;
	}
	const imported = new Set(
		await listImports(
			pyodide,
			IMPORTED_MODULES_SNIPPET,
			code,
			"[Drafter] Could not check which installed libraries the program imports:",
		),
	);
	for (const name of automaticPyPIInstalls) {
		if (!imported.has(name)) {
			continue;
		}
		const technical = new Error(
			`Nothing with the site provides "${name}" (no ${name}.py and no ${name}/__init__.py), so micropip installed the PyPI project of that name.`,
		);
		technical.name = "AutomaticInstall";
		reportSystemError({
			id: "runtime.import_installed_from_pypi",
			category: "runtime",
			severity: "warning",
			recoverable: true,
			message: `The import "${name}" was filled by installing a library from PyPI`,
			error: technical,
			// Shown as plain text in the debug panel, so no code marks.
			friendlyMessage: `Your program imports ${name}, and there is no ${name}.py next to your program, so Drafter installed the library named ${name} from PyPI. If ${name} is meant to be one of your own files, that library is something else: check the file's name and that the file is deployed with your site, then reload the page. If you do want the library, start your site with --project-packages ${name} and this warning will stop.`,
			friendlySteps: [
				`If \`${name}\` is meant to be one of your own files, check the file's name and that the file is deployed with your site, then reload the page.`,
				`If you do want the library from PyPI, start your site with \`--project-packages ${name}\` and this warning will stop.`,
			],
			context: { phase: "setup", dom_id: options.rootElementId },
		});
	}
}

/**
 * The module (and the name missing from it) in a Python error that says a
 * module does not have what the program asked it for:
 * "cannot import name 'x' from 'helpers' (...)", "module 'helpers' has no
 * attribute 'x'", or "No module named 'helpers.x'". Null for other errors.
 */
function findModuleShortfall(
	errorText: string,
): { module: string; missing: string } | null {
	const importFrom = /cannot import name '([^']+)' from '([^'.]+)/.exec(
		errorText,
	);
	if (importFrom) {
		return { module: importFrom[2], missing: importFrom[1] };
	}
	const attribute = /module '([^'.]+)[^']*' has no attribute '([^']+)'/.exec(
		errorText,
	);
	if (attribute) {
		return { module: attribute[1], missing: attribute[2] };
	}
	const submodule = /No module named '([^'.]+)\.([^']+)'/.exec(errorText);
	if (submodule) {
		return { module: submodule[1], missing: submodule[2] };
	}
	return null;
}

/**
 * Student-facing steps for a run that failed because a module lacks what
 * the program asked it for, when that module is a library Drafter installed
 * from PyPI on its own (see `automaticPyPIInstalls`). The usual cause is a
 * file of the student's that is missing from the site; the generic advice
 * for these errors never mentions that a stranger's library was installed
 * in its place. Returns an empty object for every other failure.
 */
function explainImportFilledFromPyPI(error: unknown): {
	friendlySteps?: string[];
} {
	const text = error instanceof Error ? error.message : String(error);
	const shortfall = findModuleShortfall(text);
	if (!shortfall || !automaticPyPIInstalls.has(shortfall.module)) {
		return {};
	}
	const { module, missing } = shortfall;
	return {
		friendlySteps: [
			`There is no \`${module}.py\` next to your program, so Drafter installed the library named \`${module}\` from PyPI. If \`${module}\` is meant to be one of your own files, that library is something else.`,
			`Check the file's name (capital letters matter) and that the file is deployed with your site. Then reload the page: the library stays installed until you do.`,
			`If you do want the library from PyPI, it has nothing named \`${missing}\`. Check that name against the library's documentation.`,
		],
	};
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
			// Matplotlib is not preloaded, and MatPlotLibPlot needs it even
			// when the scanned module never imports matplotlib itself (e.g.,
			// the plotting happens in an imported helper module). loadPackage
			// skips packages that are already loaded.
			if (/\bMatPlotLibPlot\b/.test(options.code ?? "")) {
				await pyodide.loadPackage("matplotlib");
			}
			// Libraries outside Pyodide's own distribution (seaborn, for
			// example) are not covered by loadPackagesFromImports.
			await installMissingImports(
				options.code ?? "",
				options.packageIndexes ?? [],
				options.explicitPackageList ?? [],
			);
		} catch (error) {
			throw reportSystemError({
				id: "runtime.package_load_failed",
				category: "runtime",
				message: "Error loading packages automatically",
				error,
				context: { phase: "setup" },
			});
		}
	}
	// Explicit packages install in addition to (not instead of) automatic
	// loading, covering dependencies that import scanning cannot see.
	if (options.explicitPackageList) {
		const loaded = [];
		for (const pkg of options.explicitPackageList) {
			if (requestedPackageSpecs.has(pkg)) {
				continue;
			}
			try {
				await installPackage(pkg, options.packageIndexes ?? []);
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
		if (options.targetWindow && options.targetWindow !== window) {
			scopeJsToWindow(pyodide, runOptions.globals, options.targetWindow);
		}
	}
	// A stop-signal consumed by the interpreter but never delivered (see
	// scheduleInterruptEscalation) would otherwise be raised into this run.
	await drainPendingInterrupt(pyodide);
	activeStudentRuns += 1;
	try {
		const result = await pyodide.runPythonAsync(codeToRun, runOptions);
		await reportImportsFilledFromPyPI(pyodide, codeToRun, options);
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
			...explainImportFilledFromPyPI(error),
			recoverable: true,
			context: { phase: "setup" },
			targetDocument: options.targetWindow?.document,
			rootElementId: options.rootElementId,
		});
	} finally {
		activeStudentRuns -= 1;
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
	/** Wheel indexes (`wheels.json` URLs) searched when PyPI has no wheel. */
	packageIndexes?: string[];
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
			packageIndexes: registration.packageIndexes,
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
