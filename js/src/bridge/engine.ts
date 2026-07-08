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

export function clearDrafterSiteRoot(rootElementId: string = "drafter-root--") {
	const rootElement = document.getElementById(rootElementId) as HTMLElement;
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
		traceback: error.stack ?? null,
		context: {
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
	return `${message}\n\nWhat to try:\n- ${suggestion}\n\nTechnical details:\n${technicalDetails}`;
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

function renderSystemErrorInRoot(
	report: SystemErrorReport,
	message: string,
	error: Error,
	suggestion: string,
): boolean {
	const rootElement = document.getElementById("drafter-root--");
	if (!rootElement) {
		return false;
	}

	rootElement.replaceChildren();

	const container = document.createElement("div");
	container.className = "drafter-system-error";

	const title = document.createElement("h1");
	title.textContent = "Something Went Wrong";

	const lead = document.createElement("p");
	lead.textContent = buildStudentLead(report);

	const advice = document.createElement("p");
	advice.textContent = "What to try next:";

	const steps = document.createElement("ul");
	for (const step of buildStudentSteps(report, error, suggestion)) {
		const item = document.createElement("li");
		item.textContent = step;
		steps.appendChild(item);
	}

	const summary = document.createElement("p");
	summary.textContent = `Message: ${message}`;

	const detailsHeading = document.createElement("h2");
	detailsHeading.textContent = "Technical Details";

	const details = document.createElement("pre");
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
