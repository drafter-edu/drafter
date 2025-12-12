import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
} from "../telemetry/requests";

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

        const initialContent = <div id="drafter-debug-page-history-list"></div>;
        content?.appendChild(initialContent);
        this.listElement = document.getElementById(
            "drafter-debug-page-history-list"
        )!;
    }

    public addRequest(request: RequestEvent): void {
        const requestElement = (
            <div class="history-event" data-request-id={request.request_id}>
                <div class="request-event">
                    <strong>Request:</strong>{" "}
                    <code class="drafter-history-request-url truncate">
                        {request.url}
                    </code>{" "}
                    <span class="drafter-history-request-meta">
                        {request.action} (ID: {request.request_id})
                    </span>
                </div>
            </div>
        );

        const historyElement = this.listElement.appendChild(requestElement);
        historyElement
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
