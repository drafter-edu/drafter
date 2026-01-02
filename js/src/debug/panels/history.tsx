import { clear } from "console";
import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
} from "../telemetry/requests";
import { createTruncatableUrl } from "../components/urls";

type HistoryEvent = RequestEvent | ResponseEvent;

export class HistoryPanel {
    private contentElement: HTMLElement;
    private listElement: HTMLElement;

    private MAX_URL_LENGTH = 42;

    constructor() {
        const content = document.getElementById(
            "drafter-debug-page-history-content"
        );

        if (!content) {
            throw new Error("DebugPanel: History section not found.");
        }

        this.contentElement = content;

        const initialContent = this.createInitialContent();
        content?.appendChild(initialContent);
        this.listElement = document.getElementById(
            "drafter-debug-page-history-list"
        )!;
    }

    private createInitialContent() {
        const clearButton = (
            <button class="drafter-debug-clear-history-btn drafter-debug-button--">
                Clear History
            </button>
        );
        clearButton.addEventListener("click", () => {
            if (confirm("Are you sure you want to clear the history?")) {
                this.clearHistory();
            }
        });
        return (
            <div>
                <div class="drafter-debug-history-actions">{clearButton}</div>
                <div
                    id="drafter-debug-page-history-list"
                    class="drafter-debug-page-history-list"
                ></div>
            </div>
        );
    }

    public clearHistory(): void {
        if (this.listElement) {
            this.listElement.innerHTML = "";
        }
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

        this.listElement.prepend(requestElement);
        requestElement
            .querySelector(".drafter-history-request-url")
            ?.addEventListener("click", (d) => {
                (d.target as HTMLElement).classList.toggle("truncate");
            });
    }

    public addRequestParse(parseEvent: RequestParseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event[data-request-id="${parseEvent.request_id}"]`
        );

        if (requestEventElement) {
            const parseElement = (
                <div class="request-parse-event">
                    <strong>Called: </strong>
                    <code>{parseEvent.representation}</code>
                </div>
            );

            requestEventElement.appendChild(parseElement);
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${parseEvent.request_id} not found for parse event.`
            );
        }
    }

    public addResponse(response: ResponseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event[data-request-id="${response.request_id}"]`
        );

        if (requestEventElement) {
            requestEventElement.classList.add("has-response");
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}.`
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
                <strong>Response:</strong> {marker} {response.status_code} for
                Request ID: {response.request_id} (Response ID:{" "}
                {response.response_id})
                <details>
                    <summary>View Page Content</summary>
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
