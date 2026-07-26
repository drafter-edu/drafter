import type { TelemetryRecord } from "./base";

/**
 * Canonical error payload type.
 */

/**
 * Canonical error contract, mirroring the Python ErrorDetails in
 * src/drafter/data/errors.py. All TypeScript system errors are normalized
 * into this shape before presentation and telemetry.
 */
export type SystemErrorCategory =
	| "system"
	| "request"
	| "payload"
	| "bridge"
	| "config"
	| "runtime";

export type SystemErrorSeverity = "info" | "warning" | "error" | "critical";

/**
 * Symbolic, HTTP-name-style status strings (mirrors Python STATUSES in
 * src/drafter/data/errors.py). The precise failure lives in the envelope id.
 */
export type SystemErrorStatus = "ok" | "bad_request" | "not_found" | "error";

export type SystemErrorPresentation = "auto" | "root" | "dialog" | "log";

export interface SystemErrorCorrelation {
	causation_id?: number;
	route?: string;
	request_id?: number;
	response_id?: number;
	dom_id?: string;
	phase?: string;
}

/** JSON shape identical to Python ErrorDetails.to_json(). */
export interface ErrorDetailsJson {
	id: string;
	category: SystemErrorCategory;
	severity: SystemErrorSeverity;
	message: string;
	details: string;
	/**
	 * Structured, JSON-safe details (nested objects/arrays). Well-known
	 * keys: route_call, route_call_exact, request. Optional; Python-side
	 * envelopes always include it (possibly empty).
	 */
	data?: Record<string, unknown>;
	/** Student-friendly page-title-style label (see friendly_message). */
	friendly_title?: string;
	/**
	 * Student-friendly explanation of the failure. Optional so envelopes
	 * from older producers still parse; empty/absent means "not provided"
	 * and renderers fall back to generic wording.
	 */
	friendly_message?: string;
	/** Student-friendly "what to try next" suggestions (see friendly_message). */
	friendly_steps?: string[];
	traceback: string | null;
	context: {
		causation_id: number | null;
		route: string | null;
		request_id: number | null;
		response_id: number | null;
		dom_id: string | null;
		phase: string | null;
	};
	status_code: SystemErrorStatus;
	recoverable: boolean;
}

export interface SystemErrorReport {
	/** Stable symbolic id, e.g. "runtime.pyodide_setup_failed". */
	id: string;
	/** Canonical category; boot/runtime failures are usually "runtime". */
	category: SystemErrorCategory;
	/** Human-safe message. */
	message: string;
	/** Canonical severity (default "error"). */
	severity?: SystemErrorSeverity;
	/** Whether the app can continue after this failure (default false). */
	recoverable?: boolean;
	/** Actionable advice shown to the user. */
	suggestion?: string;
	/** Student-friendly explanation; preferred over the derived lead text. */
	friendlyMessage?: string;
	/** Student-friendly fix steps; preferred over the derived step lists. */
	friendlySteps?: string[];
	/** Dialog title (dialog presentation only). */
	title?: string;
	/** Originating thrown value, if any. */
	error?: unknown;
	/** Correlation context tying the error to the request lifecycle. */
	context?: SystemErrorCorrelation;
	/** Explicit presentation override; "auto" applies the policy matrix. */
	presentation?: SystemErrorPresentation;
	/**
	 * Document to render root-presented errors into (an iframe's document for
	 * embedded instances). Defaults to the global document. Presentation-only;
	 * never serialized into the telemetry envelope.
	 */
	targetDocument?: Document;
	/** Root element id for root-presented errors (default "drafter-root--"). */
	rootElementId?: string;
}

/**
 * Telemetry record shape matching the Python ErrorRecord.to_json() output,
 * so the debug panel can consume system errors like any other record. The
 * record's `kind` is the error's stable id (e.g. "runtime.pyodide_setup_failed").
 */
export interface ErrorTelemetryRecord extends TelemetryRecord {
	error: ErrorDetailsJson;
}
