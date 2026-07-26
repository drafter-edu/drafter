/**
 * Reports errors raised while a site is running to the local development
 * server, which appends them to a shared on-disk debug log next to the
 * student's code (see src/drafter/app/error_log.py).
 *
 * Reporting only happens outside production mode (`in_debug_mode` on) and
 * is best-effort: the first failed delivery (no dev server, e.g. a compiled
 * site, or the endpoint rejected the report) disables the reporter for the
 * rest of the session with a single console message.
 */
import { collectSystemStatus } from "./saveload";
import type { ErrorDetailsJson } from "./telemetry/errors";

/** Mirror of INTERNAL_ROUTES["ERROR_LOG"] in src/drafter/config/urls.py. */
export const ERROR_LOG_PATH = "/__drafter_error_log";

/** How long reports are batched before one delivery is attempted. */
const FLUSH_DELAY_MS = 2000;

/** Cap on reports held between flushes, so error storms stay bounded. */
const MAX_QUEUED_REPORTS = 25;

/** Caps on the free-text envelope fields, keeping a full batch safely under
 * the server's request-size limit (MAX_ERROR_REPORT_BYTES). */
const MAX_MESSAGE_LENGTH = 2000;
const MAX_TEXT_LENGTH = 8000;

function truncate(text: string | null, limit: number): string | null {
	if (typeof text !== "string" || text.length <= limit) {
		return text ?? null;
	}
	return `${text.slice(0, limit)}… [truncated]`;
}

/**
 * Copy the fields the log cares about into a plain object. Envelopes that
 * crossed the Pyodide bridge are Map-like proxies whose JSON.stringify
 * output is not reliable, so the fields are read out explicitly (which
 * works on both plain objects and property-accessible proxies).
 */
function normalizeEnvelope(envelope: ErrorDetailsJson): ErrorDetailsJson {
	const context = envelope.context ?? ({} as ErrorDetailsJson["context"]);
	return {
		id: envelope.id,
		category: envelope.category,
		severity: envelope.severity,
		message: truncate(envelope.message, MAX_MESSAGE_LENGTH) ?? "",
		details: truncate(envelope.details, MAX_TEXT_LENGTH) ?? "",
		traceback: truncate(envelope.traceback, MAX_TEXT_LENGTH),
		context: {
			causation_id: context.causation_id ?? null,
			route: context.route ?? null,
			request_id: context.request_id ?? null,
			response_id: context.response_id ?? null,
			dom_id: context.dom_id ?? null,
			phase: context.phase ?? null,
		},
		status_code: envelope.status_code,
		recoverable: envelope.recoverable,
	};
}

export class DevServerErrorReporter {
	private queue: ErrorDetailsJson[] = [];
	private timer: ReturnType<typeof setTimeout> | null = null;
	private disabled = false;
	private inDebugMode = true;

	constructor(private readonly path: string = ERROR_LOG_PATH) {}

	/** Track the site's production toggle; reports only flow in debug mode. */
	public setDebugMode(inDebugMode: boolean): void {
		this.inDebugMode = inDebugMode;
	}

	/** Queue one error envelope for delivery to the development server. */
	public report(envelope: ErrorDetailsJson): void {
		if (this.disabled || !this.inDebugMode) {
			return;
		}
		if (this.queue.length >= MAX_QUEUED_REPORTS) {
			return;
		}
		this.queue.push(normalizeEnvelope(envelope));
		if (this.timer === null) {
			this.timer = setTimeout(() => {
				void this.flush();
			}, FLUSH_DELAY_MS);
		}
	}

	/** Deliver all queued reports now (normally driven by the batch timer). */
	public async flush(): Promise<void> {
		if (this.timer !== null) {
			clearTimeout(this.timer);
			this.timer = null;
		}
		if (this.disabled || this.queue.length === 0) {
			return;
		}
		const reports = this.queue.splice(0);
		const payload = {
			kind: "drafter-error-report",
			version: 1,
			url: window.location.href,
			system: collectSystemStatus(),
			reports,
		};
		try {
			const response = await fetch(this.path, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
				keepalive: true,
			});
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}
		} catch (error) {
			// No dev server is listening (compiled/deployed site) or it
			// rejected the report; stop trying, and say so exactly once.
			this.disabled = true;
			this.queue.length = 0;
			console.info(
				"[Drafter] Errors will not be logged to the development server:",
				error,
			);
		}
	}
}
