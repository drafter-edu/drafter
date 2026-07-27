import { Panel } from "./panel";
import type {
	RequestEvent,
	RequestParseEvent,
	ResponseEvent,
} from "../telemetry/requests";
import type { SpecificRepresentation } from "../telemetry/state";
import { renderRepresentation } from "./state";
import { createTruncatableUrl } from "../components/urls";
import type { ReactElement } from "jsx-dom/types";

export class HistoryPanel extends Panel {
	private historyItems: ReactElement[] = [];
	private currentPage = 1;
	private readonly pageSize = 5;
	// State snapshots arrive (UpdatedState) before their ResponseEvent, so
	// they wait here keyed by request id until addResponse consumes them.
	private pendingStateSnapshots = new Map<number, SpecificRepresentation>();
	/** Unclaimed snapshots beyond this bound are dropped, oldest first. */
	private readonly maxPendingSnapshots = 100;

	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
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
					<button class="drafter-debug-clear-history-btn drafter-debug-button--">
						Clear History
					</button>
				</div>

				<div
					class={`drafter-debug-page-history-pagination drafter-debug-page-history-pagination-${this.instanceId}`}
				></div>
				<div
					class={`drafter-debug-page-history-list drafter-debug-page-history-list-${this.instanceId}`}
				></div>
				<div
					class={`drafter-debug-page-history-pagination drafter-debug-page-history-pagination-bottom-${this.instanceId}`}
				></div>
			</div>
		);
	}

	private getPaginationElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-page-history-pagination"),
			"DebugPanel: Pagination element not found.",
		);
	}

	private getBottomPaginationElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-page-history-pagination-bottom"),
			"DebugPanel: Bottom pagination element not found.",
		);
	}

	public clearHistory(): void {
		this.historyItems = [];
		this.pendingStateSnapshots.clear();
		this.currentPage = 1;
		this.renderPage();
	}

	private renderPage(): void {
		const list = this.getListElement();
		list.innerHTML = ""; // Clear existing items

		if (!this.historyItems || this.historyItems.length === 0) {
			const emptyMessage = (
				<div class="drafter-debug-history-empty">
					No history available.
				</div>
			);
			list.appendChild(emptyMessage);
			return;
		}

		const totalPages = Math.max(
			1,
			Math.ceil(this.historyItems.length / this.pageSize),
		);
		this.currentPage = Math.min(this.currentPage, totalPages);

		const startIndex = (this.currentPage - 1) * this.pageSize;
		const endIndex = Math.min(
			startIndex + this.pageSize,
			this.historyItems.length,
		);
		const pageItems = this.historyItems.slice(startIndex, endIndex);

		pageItems.forEach((item) => list.appendChild(item));
		this.renderPagination(totalPages);
	}

	private renderPagination(totalPages: number): void {
		const containers = [
			this.getPaginationElement(),
			this.getBottomPaginationElement(),
		];
		containers.forEach((c) => (c.innerHTML = "")); // Clear existing pagination

		if (this.historyItems.length <= this.pageSize) {
			return; // No pagination needed
		}

		// Each bar needs its own elements (and listeners), so build one per
		// container rather than cloning.
		containers.forEach((c) =>
			c.appendChild(this.buildPaginationBar(totalPages)),
		);
	}

	/** One full-width pagination bar: controls plus a progress track showing
	 * how far through the results the current page reaches. */
	private buildPaginationBar(totalPages: number): ReactElement {
		const totalItems = this.historyItems.length;
		const startIndex = (this.currentPage - 1) * this.pageSize;
		const endIndex = Math.min(startIndex + this.pageSize, totalItems);
		const percent = Math.round((endIndex / totalItems) * 100);

		const previousButton = (
			<button
				class="drafter-debug-pagination-btn drafter-debug-button--"
				style="margin-left: 0;"
				disabled={this.currentPage === 1}
			>
				&#9664; Previous
			</button>
		);

		const pageLabel = (
			<span class="drafter-debug-page-history-page-label">
				Page {this.currentPage} of {totalPages}
				<span class="drafter-debug-page-history-range">
					{" "}
					(visits {startIndex + 1}&ndash;{endIndex} of {totalItems})
				</span>
			</span>
		);

		const nextButton = (
			<button
				class="drafter-debug-pagination-btn drafter-debug-button--"
				style="margin-left: 0;"
				disabled={this.currentPage === totalPages}
			>
				Next &#9654;
			</button>
		);

		previousButton.addEventListener("click", () => {
			if (this.currentPage > 1) {
				this.currentPage--;
				this.renderPage();
			}
		});

		nextButton.addEventListener("click", () => {
			if (this.currentPage < totalPages) {
				this.currentPage++;
				this.renderPage();
			}
		});

		return (
			<div class="drafter-debug-pagination-bar">
				<div class="drafter-debug-pagination-controls">
					{previousButton}
					{pageLabel}
					{nextButton}
				</div>
				<div
					class="drafter-debug-pagination-progress"
					role="progressbar"
					aria-valuemin={0}
					aria-valuemax={100}
					aria-valuenow={percent}
					title={`${percent}% of the way through the results`}
				>
					<div
						class="drafter-debug-pagination-progress-fill"
						style={{ width: `${percent}%` }}
					></div>
				</div>
			</div>
		);
	}

	public addRequest(request: RequestEvent): void {
		const now = new Date();
		const prettyTime = now.toLocaleTimeString();

		const urlElement = createTruncatableUrl(request.url);
		// TODO: Ability to debug the sent parameters
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

		const requestElement = (
			<div class="history-event" data-request-id={request.request_id}>
				<div class="request-event">
					<strong>Visit:</strong>{" "}
					<span class="drafter-history-request-time">
						{prettyTime}
					</span>
					<code>{request.url}</code>
					<span class="drafter-history-request-meta">
						<span class="drafter-history-via">via</span>{" "}
						{request.action} (ID: {request.request_id})
					</span>
					{recreateLink}
				</div>
				<div class="drafter-debug-history-event-detail">
					<details>
						<summary>
							<strong>Request</strong>
						</summary>
						<div>{urlElement}</div>
					</details>
				</div>
			</div>
		);

		// this.getListElement().prepend(requestElement);
		this.historyItems.unshift(requestElement);
		this.currentPage = 1; // Reset to first page on new request
		this.renderPage();

		requestElement
			.querySelector(".drafter-history-request-url")
			?.addEventListener("click", (d) => {
				(d.target as HTMLElement).classList.toggle("truncate");
			});
	}

	public addRequestParse(parseEvent: RequestParseEvent): boolean {
		const requestEventElement = this.historyItems
			.find((el) => el.dataset.requestId === "" + parseEvent.request_id)
			?.querySelector(".drafter-history-request-url");

		if (!requestEventElement) {
			// An event may reference a request this panel never saw (e.g. after
			// a panel restart). Ignore it rather than throwing back into the
			// bridge's error-reporting path.
			console.warn(
				`DebugPanel: Corresponding request ${parseEvent.request_id} not found for parse event; ignoring.`,
			);
			return false;
		}

		const parseElement = (
			<span class="request-parse-event">
				<code>{parseEvent.representation}</code>
			</span>
		);

		requestEventElement.appendChild(parseElement);
		const provenance = this.buildProvenanceTable(parseEvent.arguments);
		if (provenance) {
			requestEventElement.appendChild(provenance);
		}
		return true;
	}

	/** Human-readable labels for argument provenance sources. */
	private static readonly SOURCE_LABELS: Record<string, string> = {
		form_field: "form field",
		event_detail: "event value",
		component_argument: "component argument",
		framework_meta: "framework value",
		framework_injected: "framework (injected)",
		state: "current state",
		default: "default value",
	};

	/** A table showing where each bound route argument came from. */
	private buildProvenanceTable(
		argumentEntries: RequestParseEvent["arguments"] | undefined,
	): HTMLElement | null {
		if (!argumentEntries || argumentEntries.length === 0) {
			return null;
		}
		return (
			<details class="drafter-debug-provenance-details">
				<summary>Parameters ({argumentEntries.length})</summary>
				<table class="drafter-debug-provenance">
					<thead>
						<tr>
							<th>Parameter</th>
							<th>Source</th>
							<th>Value</th>
							<th>Converted</th>
						</tr>
					</thead>
					<tbody>
						{argumentEntries.map((entry) => (
							<tr>
								<td>
									{entry.name}
									{entry.expected_type
										? `: ${entry.expected_type}`
										: ""}
								</td>
								<td>
									{HistoryPanel.SOURCE_LABELS[entry.source] ??
										entry.source}
									{entry.source_detail
										? ` (${entry.source_detail})`
										: ""}
								</td>
								<td>{entry.value}</td>
								<td>
									{entry.changed
										? (entry.converted ?? "")
										: "—"}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</details>
		) as HTMLElement;
	}

	public addResponse(response: ResponseEvent): boolean {
		const requestEventElement = this.historyItems.find(
			(el) => el.dataset.requestId === "" + response.request_id,
		);

		if (!requestEventElement) {
			// See addRequestParse: unknown request ids are ignored, not thrown.
			console.warn(
				`DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}; ignoring.`,
			);
			return false;
		}

		// The state snapshot for this visit (logged just before the response)
		// renders below the generated unit test inside the response details.
		const snapshot = this.pendingStateSnapshots.get(response.request_id);
		this.pendingStateSnapshots.delete(response.request_id);

		requestEventElement.classList.add("has-response");
		// Choose a red marker, green marker, or yellow marker based on errors/warnings
		const marker = response.has_errors
			? "🔴"
			: response.has_warnings
				? "🟡"
				: "🟢";
		const responseElement = (
			<div class="drafter-debug-history-event-detail drafter-debug-history-response-detail">
				<details>
					<summary>
						<strong>Response:</strong> {marker}{" "}
						{response.status_code} for Request ID:{" "}
						{response.request_id} (Response ID:{" "}
						{response.response_id})
					</summary>
					<pre>
						{response.formatted_page_content ||
							"No content available."}
					</pre>
					{snapshot ? this.buildStateEntry(snapshot) : null}
				</details>
			</div>
		);

		requestEventElement.appendChild(responseElement);
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
		const responseDetails = this.historyItems
			.find((el) => el.dataset.requestId === "" + requestId)
			?.querySelector(".drafter-debug-history-response-detail details");
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
