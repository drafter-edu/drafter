import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
    OutcomeEvent,
} from "../telemetry/requests";

type HistoryEvent = RequestEvent | ResponseEvent;

export class HistoryPanel {
    private contentElement: HTMLElement;
    private listElement: HTMLElement;

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
            <div
                class="history-event request-event"
                data-request-id={request.request_id}
            >
                <div class="history-event-header">
                    <strong>Request #{request.request_id}:</strong> {request.url}
                    <span class="request-action">[{request.action}]</span>
                </div>
                {(request.args || request.kwargs) && (
                    <div class="request-params">
                        {request.args && <div><strong>Args:</strong> {request.args}</div>}
                        {request.kwargs && <div><strong>Kwargs:</strong> {request.kwargs}</div>}
                    </div>
                )}
            </div>
        );

        this.listElement.appendChild(requestElement);
    }

    public addRequestParse(parseEvent: RequestParseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event.request-event[data-request-id="${parseEvent.request_id}"]`
        );

        if (requestEventElement) {
            const parseElement = (
                <div class="history-event request-parse-event">
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
            `.history-event.request-event[data-request-id="${response.request_id}"]`
        );

        if (requestEventElement) {
            requestEventElement.classList.add("has-response");
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}.`
            );
        }
        
        const statusClass = response.has_errors ? "status-error" : 
                           response.has_warnings ? "status-warning" : 
                           "status-success";
        
        const responseElement = (
            <div class={`history-event response-event ${statusClass}`}>
                <div class="response-header">
                    <strong>Response #{response.response_id}:</strong>
                    <span class={`status-code ${statusClass}`}>
                        {response.status_code}
                    </span>
                    <span class="response-type">{response.payload_type}</span>
                    <span class="response-duration">{response.duration_ms}ms</span>
                </div>
                <div class="response-metadata">
                    <span>Body: {response.body_length} bytes</span>
                    {response.has_errors && <span class="has-errors">❌ Has Errors</span>}
                    {response.has_warnings && <span class="has-warnings">⚠️ Has Warnings</span>}
                </div>
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

    public addOutcome(outcome: OutcomeEvent): void {
        const responseEventElement = this.contentElement.querySelector(
            `[data-request-id] .response-event`
        );

        if (responseEventElement) {
            const outcomeElement = (
                <div class={`history-event outcome-event ${outcome.success ? "outcome-success" : "outcome-failure"}`}>
                    <strong>Outcome #{outcome.outcome_id}:</strong>
                    <span class="outcome-status">
                        {outcome.success ? "✅ Success" : "❌ Failed"}
                    </span>
                    <span class="outcome-message">{outcome.message}</span>
                </div>
            );

            responseEventElement.appendChild(outcomeElement);
        }
    }
}
