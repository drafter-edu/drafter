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
	console.error(
		`[Drafter System Error] ${report.id}:`,
		report.message,
		report.error,
	);
	const envelope = buildEnvelope(report, normalizedError);
	emitSystemTelemetry(envelope);

	const mode = resolvePresentation(report);
	const suggestion = report.suggestion ?? DEFAULT_SUGGESTION;

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
