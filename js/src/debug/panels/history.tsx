import { Panel } from "./panel";
import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
} from "../telemetry/requests";
import { createTruncatableUrl } from "../components/urls";

export class HistoryPanel extends Panel {
    constructor(containerId: string, instanceId: number) {
        super(containerId, instanceId, "drafter-debug-history", "Page History");
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
                    class={`drafter-debug-page-history-list drafter-debug-page-history-list-${this.instanceId}`}
                ></div>
            </div>
        );
    }

    public clearHistory(): void {
        this.getListElement().innerHTML = "";
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

        const requestElement = (
            <div class="history-event" data-request-id={request.request_id}>
                <div class="request-event">
                    <strong>Request:</strong>{" "}
                    <span class="drafter-history-request-time">
                        {prettyTime}
                    </span>
                    {urlElement}
                    <span class="drafter-history-request-meta">
                        <span class="drafter-history-via">via</span>{" "}
                        {request.action} (ID: {request.request_id})
                    </span>
                    {recreateLink}
                </div>
            </div>
        );

        this.getListElement().prepend(requestElement);
        requestElement
            .querySelector(".drafter-history-request-url")
            ?.addEventListener("click", (d) => {
                (d.target as HTMLElement).classList.toggle("truncate");
            });
    }

    public addRequestParse(parseEvent: RequestParseEvent): void {
        const requestEventElement = this.getContentElement().querySelector(
            `.history-event[data-request-id="${parseEvent.request_id}"] .drafter-history-request-url`,
        );

        if (requestEventElement) {
            const parseElement = (
                <span class="request-parse-event">
                    <code>{parseEvent.representation}</code>
                </span>
            );

            requestEventElement.appendChild(parseElement);
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${parseEvent.request_id} not found for parse event.`,
            );
        }
    }

    public addResponse(response: ResponseEvent): void {
        const requestEventElement = this.getContentElement().querySelector(
            `.history-event[data-request-id="${response.request_id}"]`,
        );

        if (requestEventElement) {
            requestEventElement.classList.add("has-response");
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}.`,
            );
        }
        // Choose a red marker, green marker, or yellow marker based on errors/warnings
        const marker = response.has_errors
            ? "🔴"
            : response.has_warnings
              ? "🟡"
              : "🟢";
        const responseElement = (
            <div class="response-event">
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
                </details>
            </div>
        );

        requestEventElement?.appendChild(responseElement);
    }
}
