import type {
	ErrorTelemetryRecord,
	SystemErrorReport,
	ErrorDetailsJson,
	SystemErrorPresentation,
} from "../debug/telemetry/errors";
import { alertDialog } from "../dialogs";

export type { ErrorTelemetryRecord } from "../debug/telemetry/errors";

export interface DrafterInitOptions {
	studentFilename?: string;
	code?: string;
	url?: string;
	presentErrors?: boolean;
	assetsUrl?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
	/** The root element this instance renders into (for concurrent instances). */
	rootElementId?: string;
	/** Whether to isolate this instance in a shadow root. */
	useShadowDom?: boolean;
	/**
	 * The window this instance renders into (an iframe's contentWindow for
	 * embedded instances sharing the host page's Pyodide runtime). Defaults
	 * to the global window.
	 */
	targetWindow?: Window;
	/**
	 * Unique key for this instance in the shared Python server registry.
	 * Required when several instances use the same rootElementId in separate
	 * documents (iframes); defaults to rootElementId.
	 */
	instanceId?: string;
}

const DEFAULT_SUGGESTION = "Please show this to your instructor for more help.";

const SYSTEM_ERROR_SOURCE = "js.bridge.engine";

type SystemTelemetrySink = (event: ErrorTelemetryRecord) => void;

/**
 * Error objects that have already been reported, with whether the report
 * was shown to the student (root render or dialog). Drafter's reporters
 * throw the error onward after reporting it, so the same object can reach
 * a second reporter or the window's error event; this is how they tell.
 */
const reportedErrors = new WeakMap<object, { presented: boolean }>();

/** Remember that an error has been reported once already. */
export function markErrorReported(error: unknown, presented = false): void {
	if (error !== null && typeof error === "object") {
		const earlier = reportedErrors.get(error);
		reportedErrors.set(error, {
			presented: presented || (earlier?.presented ?? false),
		});
	}
}

/** Whether this exact error object has been reported before. */
export function isErrorReported(error: unknown): boolean {
	return (
		error !== null && typeof error === "object" && reportedErrors.has(error)
	);
}

/** Windows that already have Drafter's uncaught-error listeners. */
const listenedWindows = new WeakSet<Window>();

/** The browser's text for an error in a script it will not describe. */
const OPAQUE_SCRIPT_ERROR = "Script error.";

/**
 * Report errors that escape to the browser: uncaught exceptions and
 * rejected promises nobody handled. Errors Drafter has already reported
 * (and then thrown onward, as its reporters do) are recognized by identity
 * and skipped, so nothing is reported twice. Errors from other sites'
 * scripts, which the browser hides behind "Script error.", are ignored.
 * Installing is idempotent per window.
 */
export function installUncaughtErrorListeners(target: Window = window): void {
	if (listenedWindows.has(target)) {
		return;
	}
	listenedWindows.add(target);
	target.addEventListener("error", (event: ErrorEvent) => {
		if (isErrorReported(event.error)) {
			return;
		}
		if (!event.error && (!event.message || event.message === OPAQUE_SCRIPT_ERROR)) {
			return;
		}
		reportSystemError({
			id: "runtime.uncaught_error",
			category: "runtime",
			message: "An error happened in the browser that nothing handled",
			error: event.error ?? event.message,
			severity: "error",
			recoverable: true,
			presentation: "log",
			suggestion:
				"Look for the error in the debug panel's Current tab; if your page still works, it may come from a browser extension or another script on the page.",
		});
	});
	target.addEventListener(
		"unhandledrejection",
		(event: PromiseRejectionEvent) => {
			if (isErrorReported(event.reason)) {
				return;
			}
			reportSystemError({
				id: "runtime.unhandled_rejection",
				category: "runtime",
				message: "A background task failed and nothing handled the failure",
				error: event.reason,
				severity: "error",
				recoverable: true,
				presentation: "log",
				suggestion:
					"Look for the error in the debug panel's Current tab.",
			});
		},
	);
}

let systemTelemetrySink: SystemTelemetrySink | null = null;
let syntheticEventCounter = 0;

/**
 * Register the consumer for system-error telemetry (normally the debug
 * panel). The last registered sink wins, so re-created panels take over.
 */
export function setSystemErrorSink(sink: SystemTelemetrySink | null): void {
	systemTelemetrySink = sink;
}

export function clearDrafterSiteRoot(
	rootElementId: string = "drafter-root--",
	targetDocument: Document = document,
) {
	const rootElement = targetDocument.getElementById(
		rootElementId,
	) as HTMLElement;
	if (rootElement) {
		rootElement.innerHTML = "";
	} else {
		throw new Error(`Element with ID ${rootElementId} not found`);
	}
}

export function normalizeSystemError(error: unknown): Error {
	if (error instanceof Error) {
		return error;
	}

	return new Error(String(error));
}

function buildEnvelope(
	report: SystemErrorReport,
	error: Error,
): ErrorDetailsJson {
	const context = report.context ?? {};
	return {
		id: report.id,
		category: report.category,
		severity: report.severity ?? "error",
		message: report.message,
		details: `${error.name}: ${error.message}`,
		friendly_message: report.friendlyMessage ?? buildStudentLead(report),
		friendly_steps: resolveStudentSteps(report, error),
		traceback: error.stack ?? null,
		context: {
			causation_id: context.causation_id ?? null,
			route: context.route ?? null,
			request_id: context.request_id ?? null,
			response_id: context.response_id ?? null,
			dom_id: context.dom_id ?? null,
			phase: context.phase ?? null,
		},
		status_code: "error",
		recoverable: report.recoverable ?? false,
	};
}

function emitSystemTelemetry(envelope: ErrorDetailsJson): void {
	const level =
		envelope.severity === "critical" ? "error" : envelope.severity;
	const event: ErrorTelemetryRecord = {
		kind: envelope.id,
		metadata: {
			source: SYSTEM_ERROR_SOURCE,
			level,
			id: --syntheticEventCounter,
			version: "0.0.1",
			timestamp: new Date().toISOString(),
		},
		correlation: {
			route: envelope.context.route ?? undefined,
			request_id: envelope.context.request_id ?? undefined,
			response_id: envelope.context.response_id ?? undefined,
			dom_id: envelope.context.dom_id ?? undefined,
		},
		error: envelope,
	};
	if (systemTelemetrySink) {
		try {
			systemTelemetrySink(event);
		} catch (sinkError) {
			console.error(
				"[Drafter System Error] Failed to deliver system error to debug panel",
				sinkError,
			);
		}
	}
}

/**
 * Presentation policy matrix:
 *
 * | Severity  | Recoverable | Presentation        |
 * |-----------|-------------|---------------------|
 * | critical  | any         | root render         |
 * | error     | false       | root render         |
 * | error     | true        | dialog              |
 * | warning   | any         | debug panel logging |
 * | info      | any         | debug panel logging |
 *
 * Explicit `presentation` overrides win; a root render falls back to a
 * dialog when the root element is unavailable. All reports are always
 * mirrored to the debug panel sink and the console regardless of mode.
 */
function resolvePresentation(
	report: SystemErrorReport,
): Exclude<SystemErrorPresentation, "auto"> {
	if (report.presentation && report.presentation !== "auto") {
		return report.presentation;
	}
	const severity = report.severity ?? "error";
	const recoverable = report.recoverable ?? false;
	if (severity === "critical") {
		return "root";
	}
	if (severity === "error") {
		return recoverable ? "dialog" : "root";
	}
	return "log";
}

function formatSystemErrorMessage(
	report: SystemErrorReport,
	message: string,
	error: Error,
	suggestion: string,
): string {
	const technicalDetails = [
		`Error ID: ${report.id}`,
		`Category: ${report.category}`,
		`Severity: ${report.severity ?? "error"}`,
		`${error.name}: ${error.message}`,
	].join("\n");
	const lead = report.friendlyMessage ? `${report.friendlyMessage}\n\n` : "";
	const steps = resolveStudentSteps(report, error, suggestion)
		.map((step) => `- ${step}`)
		.join("\n");
	return `${message}\n\n${lead}What to try:\n${steps}\n\nTechnical details:\n${technicalDetails}`;
}

function buildStudentLead(report: SystemErrorReport): string {
	if (report.id.includes("pyodide_setup")) {
		return "Drafter could not finish setting up Python in the browser.";
	}
	if (report.id.includes("package_")) {
		return "Drafter had trouble loading one of the Python packages your code needs.";
	}
	if (report.id.includes("student_code_failed")) {
		return "Your code started running but stopped because of an error.";
	}
	if (report.category === "runtime") {
		return "A runtime problem interrupted your program before it could finish.";
	}
	return "Something went wrong while Drafter was running your project.";
}

/**
 * Student-facing fix steps for a report: steps supplied by the reporter
 * (e.g. passed through from a Python envelope) win; otherwise they are
 * derived from the error text.
 */
function resolveStudentSteps(
	report: SystemErrorReport,
	error: Error,
	suggestion: string = report.suggestion ?? DEFAULT_SUGGESTION,
): string[] {
	if (report.friendlySteps && report.friendlySteps.length > 0) {
		return report.friendlySteps;
	}
	return buildStudentSteps(report, error, suggestion);
}

function buildStudentSteps(
	report: SystemErrorReport,
	error: Error,
	suggestion: string,
): string[] {
	const combined = `${report.message}\n${error.name}: ${error.message}\n${error.stack ?? ""}`;

	if (combined.includes("SyntaxError")) {
		return [
			"Open the file and line shown in the traceback or stack details.",
			"Check punctuation first: missing colons, commas, quotes, or parentheses.",
			"Run your code again after fixing one syntax issue at a time.",
		];
	}

	if (combined.includes("ModuleNotFoundError")) {
		// By this point Drafter has already tried to install the library
		// (see installMissingImports), so what is left is a misspelling, a
		// library whose install name differs from its import name, or one
		// that cannot run in a browser at all.
		const match = /No module named '([^'.]+)/.exec(combined);
		const name = match ? match[1] : null;
		const library = name ? `\`${name}\`` : "the library";
		return [
			`Check the spelling of ${library} on the \`import\` line. If it is one of your own files, check that the file is next to your program.`,
			name
				? `Drafter looked for a library named \`${name}\` to install and could not use one. If the library installs under a different name (the way \`sklearn\` is installed as \`scikit-learn\`), start your site with \`--project-packages\` followed by that name.`
				: "If the library installs under a different name than you import it by (the way `sklearn` is installed as `scikit-learn`), start your site with `--project-packages` followed by that name.",
			"Some libraries cannot run in a browser at all. The \"Third-party libraries\" page of the Drafter documentation explains which ones work.",
		];
	}

	if (combined.includes("NameError")) {
		return [
			"Check for misspelled variable or function names.",
			"Make sure names are defined before they are used.",
			"Check capitalization because names are case-sensitive.",
		];
	}

	return [
		suggestion,
		"Read the technical details and focus on the first failing line.",
		"If needed, share the Error ID with your instructor for faster help.",
	];
}

/**
 * Fill a step list item, turning backtick-marked fragments (like `this`)
 * into inline <code> elements. Text is always added via text nodes, so
 * step strings can never inject markup.
 */
function appendStepContent(
	item: HTMLElement,
	step: string,
	targetDocument: Document,
): void {
	if (!step.includes("`")) {
		item.textContent = step;
		return;
	}
	step.split("`").forEach((segment, index) => {
		if (!segment) {
			return;
		}
		if (index % 2 === 1) {
			const code = targetDocument.createElement("code");
			code.textContent = segment;
			item.appendChild(code);
		} else {
			item.appendChild(targetDocument.createTextNode(segment));
		}
	});
}

function renderSystemErrorInRoot(
	report: SystemErrorReport,
	message: string,
	error: Error,
	suggestion: string,
): boolean {
	// Embedded instances report which document/root the error belongs to;
	// default to the primary root in the global document.
	const targetDocument = report.targetDocument ?? document;
	const rootElement = targetDocument.getElementById(
		report.rootElementId ?? "drafter-root--",
	);
	if (!rootElement) {
		return false;
	}

	rootElement.replaceChildren();

	const container = targetDocument.createElement("div");
	container.className = "drafter-system-error";

	const title = targetDocument.createElement("h1");
	title.textContent = "Something Went Wrong";

	const lead = targetDocument.createElement("p");
	lead.textContent = report.friendlyMessage ?? buildStudentLead(report);

	const advice = targetDocument.createElement("p");
	advice.textContent = "What to try next:";

	const steps = targetDocument.createElement("ul");
	for (const step of resolveStudentSteps(report, error, suggestion)) {
		const item = targetDocument.createElement("li");
		appendStepContent(item, step, targetDocument);
		steps.appendChild(item);
	}

	const summary = targetDocument.createElement("p");
	summary.textContent = `Message: ${message}`;

	const detailsHeading = targetDocument.createElement("h2");
	detailsHeading.textContent = "Technical Details";

	const details = targetDocument.createElement("pre");
	details.textContent = [
		`Error ID: ${report.id}`,
		`Category: ${report.category}`,
		`Severity: ${report.severity ?? "error"}`,
		`Recoverable: ${String(report.recoverable ?? false)}`,
		`Message: ${message}`,
		"",
		`${error.name}: ${error.message}`,
	].join("\n");

	container.append(
		title,
		lead,
		advice,
		steps,
		summary,
		detailsHeading,
		details,
	);
	rootElement.appendChild(container);
	return true;
}

/**
 * Single entry point for reporting TypeScript-side system errors.
 *
 * Normalizes the report into a canonical envelope, mirrors it to the
 * console and the debug panel sink, and presents it according to the
 * presentation policy matrix (see resolvePresentation).
 */
export function reportSystemError(report: SystemErrorReport): Error {
	const normalizedError = normalizeSystemError(
		report.error ?? report.message,
	);
	const mode = resolvePresentation(report);
	const suggestion = report.suggestion ?? DEFAULT_SUGGESTION;

	// An error object that was reported already (by a lower layer that then
	// threw it onward) is not logged again. It is still shown to the
	// student if the earlier report never was and this one would be.
	const earlier =
		reportedErrors.get(report.error as object) ??
		reportedErrors.get(normalizedError);
	const alreadyPresented = earlier?.presented ?? false;
	const wantsPresentation = mode === "root" || mode === "dialog";
	markErrorReported(report.error, wantsPresentation);
	markErrorReported(normalizedError, wantsPresentation);
	if (earlier && (alreadyPresented || !wantsPresentation)) {
		return normalizedError;
	}
	if (!earlier) {
		console.error(
			`[Drafter System Error] ${report.id}:`,
			report.message,
			report.error,
		);
		const envelope = buildEnvelope(report, normalizedError);
		emitSystemTelemetry(envelope);
	}

	if (
		mode === "root" &&
		renderSystemErrorInRoot(
			report,
			report.message,
			normalizedError,
			suggestion,
		)
	) {
		return normalizedError;
	}

	if (mode === "root" || mode === "dialog") {
		void alertDialog(
			formatSystemErrorMessage(
				report,
				report.message,
				normalizedError,
				suggestion,
			),
			{
				title: report.title ?? "System Error",
				modal: true,
				draggable: true,
				width: "560px",
				symbolicId: report.id,
			},
		).catch((dialogError) => {
			console.error(
				"[Drafter System Error] Failed to present system error dialog",
				dialogError,
			);
		});
	}

	return normalizedError;
}
