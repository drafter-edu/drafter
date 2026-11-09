import { Panel } from "./panel";
import type {
	ArgumentProvenance,
	RequestEvent,
	RequestParseEvent,
	ResponseEvent,
} from "../telemetry/requests";
import type { ErrorDetailsJson } from "../telemetry/errors";
import type { SpecificRepresentation } from "../telemetry/state";
import { renderRepresentation } from "./state";
import { createTruncatableUrl } from "../components/urls";
import type { ReactElement } from "jsx-dom/types";

/** How many visits are shown at first, and how many each "older" click adds. */
export const VISITS_PER_BATCH = 10;

/** Argument sources that are supplied by Drafter rather than by the visit. */
const IMPLICIT_SOURCES = new Set(["state", "framework_meta", "framework_injected"]);

/** Longest value preview kept in a visit's headline. */
const HEADLINE_VALUE_LENGTH = 40;

/** Human-readable labels for argument provenance sources. */
const SOURCE_LABELS: Record<string, string> = {
	form_field: "form field",
	event_detail: "event value",
	component_argument: "component argument",
	framework_meta: "framework value",
	framework_injected: "framework (injected)",
	state: "current state",
	default: "default value",
};

/** Everything the panel keeps about one visit beyond its DOM. */
interface Visit {
	element: HTMLElement;
	requestId: number;
	url: string;
	statusPill: HTMLElement;
	headline: HTMLElement;
	meta: HTMLElement;
	/** First error and warning messages reported for this visit. */
	errorMessages: string[];
	warningMessages: string[];
	responded: boolean;
}

function formatFileSize(bytes: number): string {
	if (bytes < 1024) {
		return `${bytes} B`;
	}
	if (bytes < 1024 * 1024) {
		return `${(bytes / 1024).toFixed(1)} KB`;
	}
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** A dataclass representation's field value, when it is a primitive. */
function fieldValue(rep: SpecificRepresentation, name: string): string | null {
	if (rep.kind !== "dataclass") {
		return null;
	}
	const field = rep.fields.find((entry) => entry.name === name);
	if (!field || field.value.kind !== "primitive") {
		return null;
	}
	return String(field.value.value);
}

/** The amounts of a Color representation as a CSS hex code, or null. */
function colorFromRepresentation(rep: SpecificRepresentation): string | null {
	if (rep.kind !== "dataclass" || rep.type !== "Color") {
		return null;
	}
	const channels = ["red", "green", "blue"].map((name) =>
		Number(fieldValue(rep, name)),
	);
	if (channels.some((amount) => Number.isNaN(amount))) {
		return null;
	}
	const alpha = Number(fieldValue(rep, "alpha") ?? 255);
	const hex = (amount: number) => amount.toString(16).padStart(2, "0");
	return (
		"#" + channels.map(hex).join("") + (alpha === 255 ? "" : hex(alpha))
	);
}

/** Whether a representation describes one of Drafter's uploaded-file values. */
function isFileRepresentation(rep: SpecificRepresentation): boolean {
	return (
		rep.kind === "dataclass" &&
		(rep.type === "DrafterTextFile" || rep.type === "DrafterBinaryFile") &&
		fieldValue(rep, "filename") !== null
	);
}

/**
 * The short text for one argument in a visit's headline: pictures, files
 * and colors get a summary instead of their raw text, which for an upload
 * would be the start of a dictionary of bytes.
 */
export function summarizeArgument(entry: ArgumentProvenance): string {
	const rep = entry.representation ?? null;
	if (rep) {
		if (rep.kind === "image") {
			const size =
				rep.width != null && rep.height != null
					? ` ${rep.width}×${rep.height}`
					: "";
			return `<Picture${rep.filename ? ` ${rep.filename}` : ""}${size}>`;
		}
		if (rep.kind === "bytes") {
			return `<${rep.length} bytes>`;
		}
		if (isFileRepresentation(rep)) {
			const size = Number(fieldValue(rep, "size"));
			return `<file ${fieldValue(rep, "filename")}${
				Number.isNaN(size) ? "" : `, ${formatFileSize(size)}`
			}>`;
		}
		const color = colorFromRepresentation(rep);
		if (color) {
			return `Color(${color})`;
		}
	}
	const text = entry.converted ?? entry.value;
	if (text.length > HEADLINE_VALUE_LENGTH) {
		return `${text.slice(0, HEADLINE_VALUE_LENGTH - 1)}…`;
	}
	return text;
}

/** The call a visit made, as a student would write it: route(name=value, ...). */
export function buildCallHeadline(
	url: string,
	entries: ArgumentProvenance[],
): string {
	const parts = entries
		.filter((entry) => !IMPLICIT_SOURCES.has(entry.source))
		.map((entry) => `${entry.name}=${summarizeArgument(entry)}`);
	return `${url}(${parts.join(", ")})`;
}

export class HistoryPanel extends Panel {
	private visits: Visit[] = [];
	/** How many of the newest visits are shown; grows with "older" clicks. */
	private visibleCount = VISITS_PER_BATCH;
	// State snapshots arrive (UpdatedState) before their ResponseEvent, so
	// they wait here keyed by request id until addResponse consumes them.
	private pendingStateSnapshots = new Map<number, SpecificRepresentation>();
	/** Unclaimed snapshots beyond this bound are dropped, oldest first. */
	private readonly maxPendingSnapshots = 100;

	/**
	 * @param onClear Called after the history is cleared, so panels derived
	 *   from it (the Tests tab's regression tests) can start fresh too.
	 */
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
		private readonly onClear: () => void = () => {},
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-history",
			"Page History",
			root,
		);
	}

	protected getListElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-page-history-list"),
			"DebugPanel: History section not found.",
		);
	}

	private getCountElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-page-history-count"),
			"DebugPanel: History count element not found.",
		);
	}

	private getOlderElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-page-history-older"),
			"DebugPanel: History 'older' element not found.",
		);
	}

	public override initialize() {
		// Setup event handlers after structure is created
		const clearButton = this.getContentElement().querySelector(
			".drafter-debug-clear-history-btn",
		);
		if (clearButton) {
			clearButton.addEventListener("click", () => {
				if (confirm("Are you sure you want to clear the history?")) {
					this.clearHistory();
				}
			});
		}
	}

	protected get initialContent() {
		return (
			<div>
				<div class="drafter-debug-history-actions">
					<span
						class={`drafter-debug-page-history-count drafter-debug-page-history-count-${this.instanceId}`}
					></span>
					<button class="drafter-debug-clear-history-btn drafter-debug-button--">
						Clear History
					</button>
				</div>
				<div
					class={`drafter-debug-page-history-list drafter-debug-page-history-list-${this.instanceId}`}
				></div>
				<div
					class={`drafter-debug-page-history-older drafter-debug-page-history-older-${this.instanceId}`}
				></div>
			</div>
		);
	}

	public clearHistory(): void {
		this.visits = [];
		this.pendingStateSnapshots.clear();
		this.visibleCount = VISITS_PER_BATCH;
		this.renderList();
		this.onClear();
	}

	/** Re-draw the visible visits, the count line, and the "older" button. */
	private renderList(): void {
		const list = this.getListElement();
		list.innerHTML = "";
		const count = this.getCountElement();
		const older = this.getOlderElement();
		older.innerHTML = "";

		if (this.visits.length === 0) {
			list.appendChild(
				<div class="drafter-debug-history-empty">
					No history available.
				</div>,
			);
			count.textContent = "";
			return;
		}

		const total = this.visits.length;
		const shown = Math.min(this.visibleCount, total);
		for (const visit of this.visits.slice(0, shown)) {
			list.appendChild(visit.element);
		}
		count.textContent =
			shown === total
				? `${total} ${total === 1 ? "visit" : "visits"}, newest first`
				: `Showing the newest ${shown} of ${total} visits`;

		const remaining = total - shown;
		if (remaining > 0) {
			const batch = Math.min(VISITS_PER_BATCH, remaining);
			const button = (
				<button class="drafter-debug-history-older-btn drafter-debug-button--">
					Show {batch} older {batch === 1 ? "visit" : "visits"}
				</button>
			) as HTMLButtonElement;
			button.addEventListener("click", () => {
				this.visibleCount += VISITS_PER_BATCH;
				this.renderList();
			});
			older.appendChild(button);
		}
	}

	private findVisit(requestId: number | string): Visit | undefined {
		return this.visits.find((visit) => visit.requestId === Number(requestId));
	}

	public addRequest(request: RequestEvent): void {
		const now = new Date();
		const prettyTime = now.toLocaleTimeString();

		const urlElement = createTruncatableUrl(request.url);
		const recreateLink = (
			<button
				class="request-recreate-link drafter-debug-button--"
				title="Click to recreate this request"
			>
				Revisit
			</button>
		);
		// Python re-dispatches the actual Request object it logged for this
		// id; the url and JSON kwargs ride along so the request can be
		// rebuilt even after the log was reset (e.g. a code restart).
		recreateLink.addEventListener("click", () => {
			window.dispatchEvent(
				new CustomEvent("drafter-replay-request", {
					detail: {
						request_id: request.request_id,
						url: request.url,
						kwargs_json: request.kwargs_json ?? "",
					},
				}),
			);
		});

		const statusPill = (
			<span class="drafter-history-status is-pending">Running…</span>
		) as HTMLElement;
		const headline = (
			<code class="drafter-history-call">{request.url}()</code>
		) as HTMLElement;
		const meta = (
			<span class="drafter-history-request-meta"></span>
		) as HTMLElement;

		const requestElement = (
			<div class="history-event" data-request-id={request.request_id}>
				<div class="request-event">
					{statusPill}
					<span class="drafter-history-request-time">
						{prettyTime}
					</span>
					{headline}
					{meta}
					{recreateLink}
				</div>
				<div class="drafter-debug-history-event-detail drafter-debug-history-request-detail">
					<details class="drafter-debug-provenance-details">
						<summary>Where these values came from</summary>
						<div class="drafter-history-request-line">
							{urlElement}
							<span class="drafter-history-request-via">
								<span class="drafter-history-via">via</span>{" "}
								{request.action} (ID: {request.request_id})
							</span>
						</div>
					</details>
				</div>
			</div>
		) as HTMLElement;

		this.visits.unshift({
			element: requestElement,
			requestId: request.request_id,
			url: request.url,
			statusPill,
			headline,
			meta,
			errorMessages: [],
			warningMessages: [],
			responded: false,
		});
		this.renderList();

		requestElement
			.querySelector(".drafter-history-request-url")
			?.addEventListener("click", (d) => {
				(d.target as HTMLElement).classList.toggle("truncate");
			});
	}

	public addRequestParse(parseEvent: RequestParseEvent): boolean {
		const visit = this.findVisit(parseEvent.request_id);
		if (!visit) {
			// An event may reference a request this panel never saw (e.g. after
			// a panel restart). Ignore it rather than throwing back into the
			// bridge's error-reporting path.
			console.warn(
				`DebugPanel: Corresponding request ${parseEvent.request_id} not found for parse event; ignoring.`,
			);
			return false;
		}

		const entries = parseEvent.arguments ?? [];
		visit.headline.textContent = buildCallHeadline(visit.url, entries);

		const details = visit.element.querySelector(
			".drafter-debug-provenance-details",
		);
		if (details) {
			details.appendChild(
				<span class="request-parse-event">
					<code>{parseEvent.representation}</code>
				</span>,
			);
			const argumentList = this.buildArgumentList(entries);
			if (argumentList) {
				details.appendChild(argumentList);
			}
		}
		return true;
	}

	/** One line per bound argument: where it came from and what it became. */
	private buildArgumentList(entries: ArgumentProvenance[]): HTMLElement | null {
		if (entries.length === 0) {
			return null;
		}
		return (
			<div class="drafter-debug-provenance">
				{entries.map((entry) => this.buildArgumentEntry(entry))}
			</div>
		) as HTMLElement;
	}

	private buildArgumentEntry(entry: ArgumentProvenance): HTMLElement {
		const rep = entry.representation ?? null;
		const color = rep ? colorFromRepresentation(rep) : null;
		const bulky =
			rep !== null &&
			(rep.kind === "image" ||
				rep.kind === "bytes" ||
				isFileRepresentation(rep));
		return (
			<div class="drafter-history-arg">
				<span class="drafter-history-arg-name">
					{entry.name}
					{entry.expected_type ? (
						<span class="drafter-history-arg-type">
							: {entry.expected_type}
						</span>
					) : null}
				</span>
				<span class="drafter-history-arg-source">
					{SOURCE_LABELS[entry.source] ?? entry.source}
					{entry.source_detail ? ` (${entry.source_detail})` : ""}
				</span>
				<span class="drafter-history-arg-value">
					{color ? (
						<span
							class="drafter-history-arg-swatch"
							style={{ backgroundColor: color }}
							title={color}
						></span>
					) : null}
					{bulky ? (
						<code>{summarizeArgument(entry)}</code>
					) : (
						<code>{entry.value}</code>
					)}
					{entry.changed && !bulky ? (
						<span class="drafter-history-arg-converted">
							{" → "}
							<code>{entry.converted ?? ""}</code>
						</span>
					) : null}
				</span>
				{bulky && rep ? (
					<div class="drafter-history-arg-preview">
						{renderRepresentation(rep)}
					</div>
				) : null}
			</div>
		) as HTMLElement;
	}

	/**
	 * Remember an error or warning reported for a visit, so the visit's
	 * status can name it. Problems with no request id belong to no visit.
	 */
	public noteProblem(envelope: ErrorDetailsJson): void {
		const requestId = envelope.context?.request_id;
		if (requestId == null) {
			return;
		}
		const visit = this.findVisit(requestId);
		if (!visit) {
			return;
		}
		const message = (envelope.friendly_message || envelope.message || "")
			.split("\n")[0]
			.trim();
		if (envelope.severity === "warning") {
			visit.warningMessages.push(message);
		} else if (envelope.severity === "error" || envelope.severity === "critical") {
			visit.errorMessages.push(message);
		}
		if (visit.responded) {
			this.refreshStatus(visit);
		}
	}

	/** The visit's pill and note, from its response and reported problems. */
	private refreshStatus(visit: Visit, response?: ResponseEvent): void {
		const pill = visit.statusPill;
		pill.classList.remove("is-pending", "is-ok", "is-warning", "is-error");
		const notes: string[] = [];
		if (response && typeof response.duration_ms === "number") {
			notes.push(`${Math.round(response.duration_ms)} ms`);
		}
		const hasErrors =
			(response?.has_errors ?? false) || visit.errorMessages.length > 0;
		const warningCount = visit.warningMessages.length;
		if (hasErrors) {
			pill.classList.add("is-error");
			pill.textContent = "Error";
			if (visit.errorMessages[0]) {
				notes.push(visit.errorMessages[0]);
			}
		} else if (response?.status_code === "not_found") {
			pill.classList.add("is-error");
			pill.textContent = "Page not found";
		} else if (warningCount > 0 || response?.has_warnings) {
			pill.classList.add("is-warning");
			pill.textContent =
				warningCount > 1 ? `${warningCount} warnings` : "1 warning";
			if (visit.warningMessages[0]) {
				notes.push(visit.warningMessages[0]);
			}
		} else {
			pill.classList.add("is-ok");
			pill.textContent = "Success";
		}
		visit.meta.textContent = notes.join(" · ");
	}

	/** The summary line of a response's details block. */
	private static responseLabel(response: ResponseEvent): string {
		if (response.has_errors || response.status_code === "error") {
			return "Error page shown";
		}
		if (response.status_code === "not_found") {
			return "Not-found page shown";
		}
		return "Page shown";
	}

	public addResponse(response: ResponseEvent): boolean {
		const visit = this.findVisit(response.request_id);
		if (!visit) {
			// See addRequestParse: unknown request ids are ignored, not thrown.
			console.warn(
				`DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}; ignoring.`,
			);
			return false;
		}

		visit.responded = true;
		this.refreshStatus(visit, response);

		// The state snapshot for this visit (logged just before the response)
		// renders below the generated unit test inside the response details.
		const snapshot = this.pendingStateSnapshots.get(response.request_id);
		this.pendingStateSnapshots.delete(response.request_id);

		visit.element.classList.add("has-response");
		const responseElement = (
			<div class="drafter-debug-history-event-detail drafter-debug-history-response-detail">
				<details>
					<summary>
						{HistoryPanel.responseLabel(response)}
						<span class="drafter-history-response-ids">
							{" "}
							(request {response.request_id}, response{" "}
							{response.response_id}, status {response.status_code})
						</span>
					</summary>
					<pre>
						{response.formatted_page_content ||
							"No content available."}
					</pre>
					{snapshot ? this.buildStateEntry(snapshot) : null}
				</details>
			</div>
		);

		visit.element.appendChild(responseElement);
		return true;
	}

	/**
	 * Record the state snapshot the server reported for the given request so
	 * it can be shown with that visit's response details. Snapshots without a
	 * request id (e.g. restored save slots) have no visit to attach to and
	 * are ignored; the Current State panel still shows them.
	 */
	public addStateSnapshot(
		representation: SpecificRepresentation,
		requestId: number | null | undefined,
	): void {
		if (requestId == null) {
			return;
		}

		// Late arrival (the response is already rendered): attach directly,
		// replacing any earlier snapshot for the same visit.
		const responseDetails = this.findVisit(requestId)?.element.querySelector(
			".drafter-debug-history-response-detail details",
		);
		if (responseDetails) {
			responseDetails
				.querySelector(".drafter-debug-state-history-entry")
				?.remove();
			responseDetails.appendChild(this.buildStateEntry(representation));
			return;
		}

		this.pendingStateSnapshots.set(requestId, representation);
		// A snapshot may reference a request this panel never saw (e.g. after
		// a panel restart), so its response never claims it; bound the map.
		while (this.pendingStateSnapshots.size > this.maxPendingSnapshots) {
			const oldest = this.pendingStateSnapshots.keys().next().value;
			if (oldest === undefined) {
				break;
			}
			this.pendingStateSnapshots.delete(oldest);
		}
	}

	/** The expandable "state after this visit" block for response details. */
	private buildStateEntry(
		representation: SpecificRepresentation,
	): ReactElement {
		return (
			<details class="drafter-debug-state-history-entry">
				<summary>State after this visit</summary>
				{renderRepresentation(representation)}
			</details>
		);
	}
}
