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

export function clearDrafterSiteRoot() {
	const rootElement = document.getElementById(
		"drafter-root--",
	) as HTMLElement;
	if (rootElement) {
		rootElement.innerHTML = "";
	} else {
		throw new Error(`Element with ID drafter-root-- not found`);
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
	message: string,
	error: Error,
	suggestion: string,
): string {
	return `${message}\n\n${suggestion}\n\n${error.name}: ${error.message}`;
}

function renderSystemErrorInRoot(
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
	title.textContent = "Drafter System Error";

	const lead = document.createElement("p");
	lead.textContent = message;

	const advice = document.createElement("p");
	advice.textContent = suggestion;

	const details = document.createElement("pre");
	details.textContent = `${error.name}: ${error.message}`;

	container.append(title, lead, advice, details);
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
		renderSystemErrorInRoot(report.message, normalizedError, suggestion)
	) {
		return normalizedError;
	}

	if (mode === "root" || mode === "dialog") {
		void alertDialog(
			formatSystemErrorMessage(
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
